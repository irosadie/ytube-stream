#!/usr/bin/env python3
"""
Debug tool untuk monitor streaming quality dan network performance
"""

import subprocess
import time
import json
import re
from datetime import datetime

def check_network_to_youtube():
    """Check network latency and packet loss to YouTube"""
    print("\n🌐 Testing Network to YouTube...")
    print("=" * 60)
    
    try:
        # Ping YouTube RTMP servers
        result = subprocess.run(
            ['ping', '-c', '10', 'a.rtmp.youtube.com'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        output = result.stdout
        
        # Extract statistics
        loss_match = re.search(r'(\d+\.\d+)% packet loss', output)
        time_match = re.search(r'min/avg/max/stddev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)
        
        if loss_match:
            packet_loss = float(loss_match.group(1))
            print(f"📦 Packet Loss: {packet_loss}%")
            
            if packet_loss > 5:
                print("⚠️  WARNING: High packet loss! Network unstable.")
            elif packet_loss > 0:
                print("⚠️  Minor packet loss detected")
            else:
                print("✅ No packet loss - Network stable")
        
        if time_match:
            avg_ping = float(time_match.group(2))
            print(f"⏱️  Average Ping: {avg_ping:.1f}ms")
            
            if avg_ping > 150:
                print("⚠️  WARNING: High latency! May cause streaming issues.")
            elif avg_ping > 80:
                print("⚠️  Moderate latency")
            else:
                print("✅ Good latency")
                
    except Exception as e:
        print(f"❌ Network test failed: {e}")

def check_upload_bandwidth():
    """Estimate upload bandwidth requirement"""
    print("\n📊 Bandwidth Analysis...")
    print("=" * 60)
    
    # Load config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        video_bitrate = config['video']['bitrate']
        audio_bitrate = config['audio']['bitrate']
        
        # Parse bitrates
        video_mbps = float(video_bitrate.rstrip('Mk'))
        audio_kbps = float(audio_bitrate.rstrip('k'))
        
        total_mbps = video_mbps + (audio_kbps / 1000)
        recommended_mbps = total_mbps * 1.5  # 1.5x untuk overhead
        
        print(f"📹 Video Bitrate: {video_mbps} Mbps")
        print(f"🎵 Audio Bitrate: {audio_kbps} kbps")
        print(f"📦 Total: {total_mbps:.2f} Mbps")
        print(f"🚀 Recommended Upload Speed: {recommended_mbps:.2f} Mbps (minimum)")
        print(f"⚡ Recommended Upload Speed: {recommended_mbps * 1.5:.2f} Mbps (stable)")
        
        if total_mbps > 15:
            print("\n⚠️  WARNING: High bitrate for 2K streaming!")
            print("   YouTube recommended 2K (1440p) bitrate: 9-18 Mbps")
            print("   Consider using 10-12 Mbps for better stability")
            
    except Exception as e:
        print(f"❌ Config analysis failed: {e}")

def check_ffmpeg_process():
    """Check if FFmpeg is running and get stats"""
    print("\n🎬 FFmpeg Process Status...")
    print("=" * 60)
    
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        )
        
        ffmpeg_lines = [line for line in result.stdout.split('\n') if 'ffmpeg' in line.lower() and 'grep' not in line]
        
        if ffmpeg_lines:
            print("✅ FFmpeg is running:")
            for line in ffmpeg_lines:
                parts = line.split()
                if len(parts) > 10:
                    cpu = parts[2]
                    mem = parts[3]
                    print(f"   CPU: {cpu}% | RAM: {mem}%")
        else:
            print("❌ FFmpeg is not running")
            
    except Exception as e:
        print(f"❌ Process check failed: {e}")

def check_video_source():
    """Analyze video source quality"""
    print("\n🎥 Video Source Analysis...")
    print("=" * 60)
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        video_file = config['video']['file']
        
        # Get video info
        result = subprocess.run(
            ['ffprobe', '-v', 'error', 
             '-select_streams', 'v:0',
             '-show_entries', 'stream=codec_name,width,height,r_frame_rate,bit_rate',
             '-of', 'json',
             video_file],
            capture_output=True,
            text=True
        )
        
        data = json.loads(result.stdout)
        if 'streams' in data and len(data['streams']) > 0:
            stream = data['streams'][0]
            codec = stream.get('codec_name', 'unknown')
            width = stream.get('width', 0)
            height = stream.get('height', 0)
            bitrate = int(stream.get('bit_rate', 0)) / 1_000_000
            
            print(f"📁 Source File: {video_file}")
            print(f"🎞️  Codec: {codec}")
            print(f"📐 Resolution: {width}x{height}")
            print(f"💾 Source Bitrate: {bitrate:.1f} Mbps")
            
            # Compare with config
            config_codec = config['video']['codec']
            config_bitrate = float(config['video']['bitrate'].rstrip('Mk'))
            
            print(f"\n🔄 Encoding Settings:")
            print(f"   Target Codec: {config_codec}")
            print(f"   Target Bitrate: {config_bitrate} Mbps")
            
            if config_codec == 'copy':
                print("   ✅ Using codec copy (no re-encoding)")
                print(f"   📤 Streaming at: {bitrate:.1f} Mbps (source bitrate)")
            else:
                print(f"   🔄 Re-encoding from {codec} to {config_codec}")
                if bitrate > config_bitrate:
                    print(f"   ⚠️  Source bitrate ({bitrate:.1f}M) > Target ({config_bitrate}M)")
                    print(f"   📉 Quality will be reduced by re-encoding")
                else:
                    print(f"   ✅ Target bitrate is appropriate")
                    
    except Exception as e:
        print(f"❌ Video analysis failed: {e}")

def get_recommendations():
    """Provide recommendations based on analysis"""
    print("\n💡 Recommendations...")
    print("=" * 60)
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        codec = config['video']['codec']
        bitrate = float(config['video']['bitrate'].rstrip('Mk'))
        preset = config['video'].get('preset', 'medium')
        
        recommendations = []
        
        # Check codec
        if codec != 'copy':
            recommendations.append(
                "🔄 QUALITY: Switch to 'codec: copy' to preserve original quality\n"
                "   Re-encoding always reduces quality, especially with CRF/bitrate limits"
            )
        
        # Check bitrate
        if bitrate > 15:
            recommendations.append(
                f"📉 STABILITY: Current bitrate ({bitrate}M) is very high for 2K\n"
                "   Reduce to 10-12M for better stability, or use 'copy' codec"
            )
        elif bitrate < 8:
            recommendations.append(
                f"📈 QUALITY: Current bitrate ({bitrate}M) is low for 2K\n"
                "   Increase to 10-12M for better quality"
            )
        
        # Check preset
        if codec != 'copy' and preset in ['ultrafast', 'superfast', 'veryfast']:
            recommendations.append(
                f"⚡ QUALITY: Preset '{preset}' prioritizes speed over quality\n"
                "   Use 'medium' or 'slow' for better quality, or 'copy' for best quality"
            )
        
        # Buffer size
        buffer_size = config['streaming'].get('buffer_size', '20M')
        buffer_mb = int(buffer_size.rstrip('M'))
        if buffer_mb < 30:
            recommendations.append(
                f"📦 STABILITY: Buffer size ({buffer_size}) could be larger\n"
                "   Increase to 40M or 50M for better network stability"
            )
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec}")
        else:
            print("\n✅ Configuration looks good!")
            
        # Optimal config suggestion
        print("\n" + "=" * 60)
        print("🎯 OPTIMAL CONFIG for 2K ASMR (no quality loss):")
        print("=" * 60)
        print("""
{
  "video": {
    "codec": "copy",           ← No re-encoding = perfect quality
    "bitrate": "22M"           ← Not used with 'copy', just for reference
  },
  "audio": {
    "bitrate": "256k",         ← High quality for ASMR
    "codec": "aac"
  },
  "streaming": {
    "buffer_size": "50M"       ← Large buffer for stability
  }
}

Why this is best:
- 'copy' codec = zero quality loss
- No CPU overhead from re-encoding
- Original 22M bitrate preserved
- Large buffer handles network fluctuations
        """)
        
    except Exception as e:
        print(f"❌ Recommendation generation failed: {e}")

def main():
    """Main debug function"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║     YouTube ASMR Streaming Quality Debugger            ║
    ║     Diagnose network and encoding issues               ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    print(f"🕐 Debug started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all checks
    check_video_source()
    check_network_to_youtube()
    check_upload_bandwidth()
    check_ffmpeg_process()
    get_recommendations()
    
    print("\n" + "=" * 60)
    print("✅ Debug complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
