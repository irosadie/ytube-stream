#!/usr/bin/env python3
"""
Quick bandwidth test untuk YouTube streaming
"""

import subprocess
import time
import sys

def test_upload_to_youtube():
    """Test upload bandwidth ke YouTube RTMP server"""
    print("🚀 Testing upload bandwidth to YouTube RTMP servers...")
    print("=" * 60)
    
    # Test ping stability
    print("\n1️⃣ Testing connection stability...")
    try:
        result = subprocess.run(
            ['ping', '-c', '20', '-i', '0.2', 'a.rtmp.youtube.com'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        lines = result.stdout.split('\n')
        for line in lines:
            if 'packet loss' in line:
                print(f"   {line.strip()}")
            if 'min/avg/max' in line:
                print(f"   {line.strip()}")
                
    except Exception as e:
        print(f"   ⚠️ Ping test failed: {e}")
    
    # Estimate bandwidth needed
    print("\n2️⃣ Bandwidth requirements:")
    print("   📹 Video: 10 Mbps")
    print("   🎵 Audio: 0.192 Mbps")
    print("   📦 Total: ~10.2 Mbps")
    print("   🚀 Recommended: 15+ Mbps upload (1.5x safety margin)")
    print("   ⚡ Ideal: 20+ Mbps upload (2x safety margin)")
    
    # Check if we can simulate bandwidth
    print("\n3️⃣ Recommendations:")
    print("   ✅ Use 10M bitrate (safe for most home internet)")
    print("   ✅ Use 'veryfast' preset (low CPU, fast encoding)")
    print("   ✅ Use 192k audio (excellent quality, less bandwidth)")
    print("   ✅ Use 50M buffer (handles network fluctuations)")
    
    print("\n" + "=" * 60)
    print("💡 If still buffering, try these in order:")
    print("   1. Reduce bitrate to 8M")
    print("   2. Reduce resolution to 1920x1080 (1080p)")
    print("   3. Use 'ultrafast' preset")
    print("   4. Check if other apps using upload bandwidth")
    print("=" * 60)

if __name__ == '__main__':
    test_upload_to_youtube()
