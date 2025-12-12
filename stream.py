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
import threading
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
    
    def get_audio_duration(self):
        """Get audio file duration in seconds using ffprobe."""
        try:
            result = subprocess.run([
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                self.config['audio']['file']
            ], capture_output=True, text=True, timeout=10)
            
            duration = float(result.stdout.strip())
            print(f"Audio duration: {duration:.2f} seconds")
            return duration
        except Exception as e:
            print(f"Warning: Could not detect audio duration: {e}")
            print("Crossfade will be disabled.")
            return None
    
    def build_ffmpeg_command(self):
        """Build FFmpeg command for streaming with separate video/audio loops."""
        youtube_url = f"{self.config['youtube']['rtmp_url']}/{self.config['youtube']['stream_key']}"
        
        # Get audio duration for crossfade
        audio_duration = self.get_audio_duration()
        crossfade_duration = 8  # 8 seconds crossfade overlap
        
        # FFmpeg command for looping video and audio separately
        # Using large buffers for pre-encoding stability
        # For true overlap crossfade, we need 2 audio inputs
        cmd = [
            'ffmpeg',
            # Video input with loop
            '-stream_loop', '-1',  # Infinite loop for video
            '-re',  # Read input at native frame rate
            '-i', self.config['video']['file'],
            # Audio input 1 with loop
            '-stream_loop', '-1',
            '-i', self.config['audio']['file'],
            # Audio input 2 (same file) with loop for crossfade overlap
            '-stream_loop', '-1',
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
        
        # Audio encoding with TRUE OVERLAP crossfade (overlap di 8 detik transisi saja)
        if audio_duration and audio_duration > crossfade_duration * 2:
            # Audio cukup panjang untuk crossfade
            # Audio 1: fade out di 8 detik terakhir
            # Audio 2: delay sampai 8 detik sebelum audio 1 habis, fade in di 8 detik pertama
            fade_out_start = audio_duration - crossfade_duration
            delay_ms = int(fade_out_start * 1000)
            
            # Filter complex:
            # [1:a] = audio 1 dengan fade out di akhir
            # [2:a] = audio 2 dengan delay + fade in di awal
            # Lalu di-mix dengan acrossfade untuk overlap smooth
            audio_filter = (
                f"[1:a]afade=t=out:st={fade_out_start}:d={crossfade_duration}[a1];"
                f"[2:a]adelay={delay_ms}|{delay_ms},afade=t=in:st=0:d={crossfade_duration}[a2];"
                f"[a1][a2]amix=inputs=2:duration=longest:weights=1 1[aout]"
            )
            
            cmd.extend([
                '-filter_complex', audio_filter,
                '-map', '[aout]',  # Use mixed crossfaded output
                '-c:a', self.config['audio']['codec'],
                '-b:a', self.config['audio']['bitrate'],
                '-ar', '48000',  # 48kHz sample rate for high quality
            ])
            print(f"✅ Overlap Crossfade: 8 detik terakhir audio 1 (fade out) + 8 detik awal audio 2 (fade in) BERTUMPUK")
        else:
            # Audio terlalu pendek, pakai audio input pertama saja tanpa crossfade
            cmd.extend([
                '-map', '1:a:0',  # Audio dari input kedua
                '-c:a', self.config['audio']['codec'],
                '-b:a', self.config['audio']['bitrate'],
                '-ar', '48000',  # 48kHz sample rate for high quality
            ])
            if audio_duration:
                print(f"⚠️  Audio too short ({audio_duration}s) for {crossfade_duration}s crossfade, skipping")
        
        cmd.extend([
            # Streaming settings with buffering
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            
            # Buffer settings for smooth streaming
            '-max_muxing_queue_size', '9999',  # Large muxing queue
            '-fflags', '+genpts',  # Generate presentation timestamps
            
            # Connection settings for stability with aggressive reconnect
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '2',  # Reduced delay for faster reconnect
            '-reconnect_at_eof', '1',  # Reconnect at end of file
            '-multiple_requests', '1',  # Allow multiple HTTP requests
            '-timeout', '10000000',  # 10 seconds timeout in microseconds
            '-rw_timeout', '10000000',  # Read/write timeout
            
            youtube_url
        ])
        
        return cmd
    
    def _read_ffmpeg_output(self):
        """Read FFmpeg stderr output in real-time to prevent buffer blocking."""
        if not self.process or not self.process.stderr:
            return
        
        for line in iter(self.process.stderr.readline, ''):
            if not line:
                break
            line = line.strip()
            
            # Show important messages
            if any(keyword in line.lower() for keyword in ['error', 'warning', 'failed', 'invalid']):
                print(f"[FFmpeg] {line}")
            # Show progress/stats every few seconds
            elif 'frame=' in line or 'speed=' in line:
                # Only show occasional progress updates
                if hasattr(self, '_last_progress_time'):
                    if time.time() - self._last_progress_time < 5:
                        continue
                self._last_progress_time = time.time()
                print(f"[Progress] {line}")
    
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
                universal_newlines=True,
                bufsize=1  # Line buffered
            )
            
            print(f"FFmpeg process started (PID: {self.process.pid})")
            print("Menyiapkan streaming...")
            print("Menunggu koneksi ke YouTube RTMP...\n")
            
            # Start thread to read FFmpeg output
            output_thread = threading.Thread(target=self._read_ffmpeg_output, daemon=True)
            output_thread.start()
            
            # Wait a bit for initial connection
            time.sleep(3)
            
            # Check if still running after initial connection
            if self.process.poll() is not None:
                print("\n❌ FFmpeg process terminated during startup!")
                stderr = self.process.stderr.read()
                if stderr:
                    print(f"Error output:\n{stderr}")
                return
            
            print("✅ Streaming dimulai! Data sedang dikirim ke YouTube...\n")
            
            # Monitor the stream
            while True:
                # Check if process is still running
                if self.process.poll() is not None:
                    print("\n❌ FFmpeg process terminated unexpectedly!")
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
