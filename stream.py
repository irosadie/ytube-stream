#!/usr/bin/env python3
"""
Lightweight YouTube ASMR Streaming Application
Streams video and audio loops separately to YouTube with minimal CPU/RAM usage.
"""

import json
import subprocess
import time
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Optional: psutil for monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not installed. Monitoring disabled.")


class StreamMonitor:
    """Monitor CPU and RAM usage during streaming."""
    
    def __init__(self, config):
        self.enabled = config.get('monitoring', {}).get('enabled', False) and PSUTIL_AVAILABLE
        self.log_interval = config.get('monitoring', {}).get('log_interval_seconds', 30)
        self.log_file = config.get('monitoring', {}).get('log_file', 'stream_monitor.log')
        self.last_log_time = 0
        
        if self.enabled:
            logging.basicConfig(
                filename=self.log_file,
                level=logging.INFO,
                format='%(asctime)s - %(message)s'
            )
            logging.info("Stream monitoring started")
    
    def log_stats(self, process_pid=None):
        """Log current CPU and RAM usage."""
        if not self.enabled:
            return
        
        current_time = time.time()
        if current_time - self.last_log_time < self.log_interval:
            return
        
        self.last_log_time = current_time
        
        # System stats
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_used_gb = mem.used / (1024**3)
        
        stats_msg = f"CPU: {cpu_percent}% | RAM: {mem_percent}% ({mem_used_gb:.2f} GB)"
        
        # FFmpeg process stats
        if process_pid:
            try:
                process = psutil.Process(process_pid)
                proc_cpu = process.cpu_percent(interval=0.1)
                proc_mem = process.memory_info().rss / (1024**2)  # MB
                stats_msg += f" | FFmpeg CPU: {proc_cpu}% | FFmpeg RAM: {proc_mem:.1f} MB"
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        logging.info(stats_msg)
        print(f"[MONITOR] {stats_msg}")


class ASMRStreamer:
    """Main streaming class for YouTube ASMR streams."""
    
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.config = self.load_config()
        self.monitor = StreamMonitor(self.config)
        self.process = None
        self.validate_config()
    
    def load_config(self):
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_path):
            print(f"Error: Config file '{self.config_path}' not found!")
            print("Please copy 'config.example.json' to 'config.json' and configure it.")
            sys.exit(1)
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def validate_config(self):
        """Validate that required files and settings exist."""
        video_file = self.config['video']['file']
        audio_file = self.config['audio']['file']
        
        if not os.path.exists(video_file):
            print(f"Error: Video file '{video_file}' not found!")
            print("Please place your video loop file in the assets/ folder and update config.json")
            sys.exit(1)
        
        if not os.path.exists(audio_file):
            print(f"Error: Audio file '{audio_file}' not found!")
            print("Please place your audio loop file in the assets/ folder and update config.json")
            sys.exit(1)
        
        if self.config['youtube']['stream_key'] == 'YOUR_STREAM_KEY_HERE':
            print("Error: Please configure your YouTube stream key in config.json")
            sys.exit(1)
    
    def build_ffmpeg_command(self):
        """Build FFmpeg command for streaming with separate video/audio loops."""
        youtube_url = f"{self.config['youtube']['rtmp_url']}/{self.config['youtube']['stream_key']}"
        
        # FFmpeg command for looping video and audio separately
        # Using large buffers for pre-encoding stability
        cmd = [
            'ffmpeg',
            # Input options for video
            '-probesize', '50M',  # Large probe size for better analysis
            '-analyzeduration', '30000000',  # Analyze 30 seconds (in microseconds)
            '-stream_loop', '-1',  # Infinite loop for video
            '-i', self.config['video']['file'],
            # Input options for audio
            '-stream_loop', '-1',  # Infinite loop for audio (independent)
            '-i', self.config['audio']['file'],
            
            # Video encoding settings
            '-map', '0:v:0',  # Video from first input
            '-c:v', self.config['video']['codec'],
        ]
        
        # Add encoding parameters only if not using copy codec
        if self.config['video']['codec'] != 'copy':
            keyframe_interval = self.config['video'].get('keyframe_interval', 2)
            gop_size = 30 * keyframe_interval  # fps * seconds
            maxrate = self.config['video'].get('maxrate', self.config['video']['bitrate'])
            tune = self.config['video'].get('tune', None)
            
            cmd.extend([
                '-preset', self.config['video']['preset'],
                '-b:v', self.config['video']['bitrate'],
                '-maxrate', maxrate,
                '-bufsize', self.config['streaming']['buffer_size'],
                '-s', self.config['video']['resolution'],
                '-r', '30',  # 30 fps
                '-g', str(gop_size),  # Keyframe interval
                '-keyint_min', str(gop_size),  # Minimum keyframe interval
                '-sc_threshold', '0',  # Disable scene change detection
                '-pix_fmt', 'yuv420p',
                '-profile:v', 'high',  # H.264 High profile
                '-level', '4.2',  # Level for 2K
            ])
            
            # Add tune if specified (film, animation, etc)
            if tune:
                cmd.extend(['-tune', tune])
            
            # Additional quality settings for veryfast/faster presets
            if self.config['video']['preset'] in ['veryfast', 'faster', 'fast']:
                cmd.extend([
                    '-refs', '2',  # Fewer reference frames for speed
                    '-bf', '2',  # B-frames for compression
                ])
            else:
                cmd.extend([
                    '-refs', '3',  # More reference frames for quality
                    '-bf', '3',  # More B-frames for better compression
                ])
        
        # Add buffer size for copy codec too
        if self.config['video']['codec'] == 'copy':
            cmd.extend([
                '-bufsize', self.config['streaming']['buffer_size'],
            ])
        
        cmd.extend([
            # Audio encoding settings
            '-map', '1:a:0',  # Audio from second input
            '-c:a', self.config['audio']['codec'],
            '-b:a', self.config['audio']['bitrate'],
            '-ar', '48000',  # 48kHz sample rate for high quality
            
            # Streaming settings with buffering
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            
            # Buffer settings for smooth streaming
            '-max_muxing_queue_size', '9999',  # Large muxing queue
            '-fflags', '+genpts',  # Generate presentation timestamps
            
            # Connection settings for stability
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            
            youtube_url
        ])
        
        return cmd
    
    def start_stream(self):
        """Start the streaming process."""
        print("=" * 60)
        print("Starting ASMR YouTube Stream...")
        print("=" * 60)
        print(f"Video: {self.config['video']['file']}")
        print(f"Audio: {self.config['audio']['file']}")
        print(f"Resolution: {self.config['video']['resolution']}")
        print(f"Video Bitrate: {self.config['video']['bitrate']}")
        print(f"Audio Bitrate: {self.config['audio']['bitrate']}")
        print(f"Buffer: {self.config['streaming']['buffer_size']}")
        print("=" * 60)
        print("\nPress Ctrl+C to stop streaming\n")
        
        cmd = self.build_ffmpeg_command()
        
        try:
            # Start FFmpeg process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            print(f"FFmpeg process started (PID: {self.process.pid})")
            print("\n⏳ Pre-buffering 30 seconds of content before streaming...")
            print("This ensures smooth playback without buffering issues.")
            print("Streaming will start automatically after buffer is ready.\n")
            
            time.sleep(32)  # Wait for pre-buffer to fill
            print("✅ Pre-buffer ready! Now streaming to YouTube...\n")
            
            # Monitor the stream
            while True:
                # Check if process is still running
                if self.process.poll() is not None:
                    print("\nFFmpeg process terminated unexpectedly!")
                    stderr = self.process.stderr.read()
                    print(f"Error output:\n{stderr}")
                    break
                
                # Log stats
                self.monitor.log_stats(self.process.pid)
                
                # Sleep to avoid busy waiting
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\nStopping stream...")
            self.stop_stream()
            print("Stream stopped successfully!")
        
        except Exception as e:
            print(f"\nError during streaming: {e}")
            self.stop_stream()
            raise
    
    def stop_stream(self):
        """Stop the streaming process gracefully."""
        if self.process and self.process.poll() is None:
            print("Terminating FFmpeg process...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Force killing FFmpeg process...")
                self.process.kill()
                self.process.wait()
    
    def run_with_auto_restart(self, max_attempts=None):
        """Run streaming with automatic restart on failure."""
        max_attempts = max_attempts or self.config['streaming'].get('max_reconnect_attempts', 10)
        delay = self.config['streaming'].get('reconnect_delay_seconds', 5)
        
        attempt = 0
        while max_attempts == -1 or attempt < max_attempts:
            try:
                attempt += 1
                print(f"\n[Attempt {attempt}] Starting stream...")
                self.start_stream()
                break  # Successful completion (user stopped)
            
            except KeyboardInterrupt:
                print("\nUser stopped the stream.")
                break
            
            except Exception as e:
                print(f"\n[Attempt {attempt}] Stream failed: {e}")
                if max_attempts == -1 or attempt < max_attempts:
                    print(f"Restarting in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"Max reconnection attempts ({max_attempts}) reached. Exiting.")
                    break


def main():
    """Main entry point."""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║   Lightweight YouTube ASMR Streaming Application       ║
    ║   Optimized for minimal CPU/RAM usage                  ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # Check if config file exists
    config_file = 'config.json'
    if not os.path.exists(config_file):
        print(f"Config file not found. Please create '{config_file}'")
        print(f"You can copy 'config.example.json' as a template.\n")
        sys.exit(1)
    
    # Initialize and start streamer
    streamer = ASMRStreamer(config_file)
    
    # Ask user about auto-restart
    print("\nOptions:")
    print("1. Stream once (manual restart if disconnected)")
    print("2. Auto-restart on disconnection (recommended for 24/7)")
    choice = input("\nSelect option (1 or 2): ").strip()
    
    if choice == '2':
        print("\nStarting with auto-restart enabled...")
        streamer.run_with_auto_restart(max_attempts=-1)  # Infinite retries
    else:
        print("\nStarting single stream session...")
        streamer.start_stream()


if __name__ == '__main__':
    main()
