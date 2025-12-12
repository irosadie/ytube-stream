#!/usr/bin/env python3
"""
Test crossfade audio - output ke WAV untuk preview sebelum streaming
"""

import subprocess
import json

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

audio_file = config['audio']['file']

# Get audio duration
result = subprocess.run([
    'ffprobe',
    '-v', 'error',
    '-show_entries', 'format=duration',
    '-of', 'default=noprint_wrappers=1:nokey=1',
    audio_file
], capture_output=True, text=True)

duration = float(result.stdout.strip())
crossfade_duration = 8  # 8 seconds

print(f"Audio duration: {duration:.2f} seconds")
print(f"Crossfade: {crossfade_duration} seconds")
print(f"Creating 4x loop with crossfade overlap...\n")

# Calculate parameters
fade_start = duration - crossfade_duration
delay_ms = int(fade_start * 1000)

# FFmpeg command: 4 loops dengan crossfade
cmd = [
    'ffmpeg', '-y',
    # Load audio 2x
    '-stream_loop', '3',  # 4x loop = 3+1
    '-i', audio_file,
    '-stream_loop', '3',
    '-i', audio_file,
    
    # Filter: audio 1 fade out di akhir, audio 2 delayed + fade in, mix (quarter sine tanpa volume boost)
    '-filter_complex',
    f'[0:a]afade=t=out:st={fade_start}:d={crossfade_duration}:curve=qsin[a1];'
    f'[1:a]adelay={delay_ms}|{delay_ms},afade=t=in:st=0:d={crossfade_duration}:curve=qsin[a2];'
    f'[a1][a2]amix=inputs=2:duration=first:dropout_transition=0[aout]',
    
    '-map', '[aout]',
    '-c:a', 'pcm_s16le',
    '-ar', '48000',
    'test_crossfade_4x.wav'
]

print("Running FFmpeg...")
print(f"Command: {' '.join(cmd)}\n")

result = subprocess.run(cmd, capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Success! File created: test_crossfade_4x.wav")
    print(f"\nPlay dengan: ffplay test_crossfade_4x.wav")
    print(f"atau: open test_crossfade_4x.wav")
else:
    print("❌ Error!")
    print(result.stderr)
