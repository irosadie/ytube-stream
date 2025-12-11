# Lightweight YouTube ASMR Streaming

Aplikasi Python untuk streaming ASMR ke YouTube dengan CPU/RAM usage minimal. Mendukung video loop dan audio loop terpisah dengan kualitas 2K terjaga.

## Features

- ✅ **Sangat Ringan**: Optimized untuk minimal CPU/RAM usage
- ✅ **Video & Audio Loop Terpisah**: Video dan audio berjalan independent
- ✅ **2K Quality**: Support streaming 2560x1440 dengan bitrate optimal
- ✅ **Buffer Besar**: 20MB buffer untuk koneksi stabil tanpa putus
- ✅ **Auto-Restart**: Otomatis reconnect jika koneksi terputus
- ✅ **Monitoring**: Track CPU/RAM usage secara real-time
- ✅ **No Latency Priority**: Optimized untuk quality, bukan low latency

## Requirements

- Python 3.7+
- FFmpeg (harus terinstall di sistem)
- Koneksi internet stabil

## Installation

### 1. Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download dari [ffmpeg.org](https://ffmpeg.org/download.html) dan tambahkan ke PATH.

### 2. Install Python Dependencies

```bash
cd /Users/baimwong/Me/Program/python/stream
pip install -r requirements.txt
```

### 3. Setup Configuration

```bash
cp config.example.json config.json
```

Edit `config.json` dan isi:
- `stream_key`: Dapatkan dari YouTube Studio → Live → Stream Key
- `video.file`: Path ke file video loop kamu (2 menit)
- `audio.file`: Path ke file audio loop kamu

## Preparing Your Assets

### Video Loop (Recommended Settings)

Untuk hasil terbaik, pre-encode video loop kamu dengan settings berikut:

```bash
ffmpeg -i input_video.mp4 \
  -c:v libx264 \
  -preset slow \
  -crf 18 \
  -s 2560x1440 \
  -r 30 \
  -pix_fmt yuv420p \
  -an \
  assets/video_loop.mp4
```

**Penjelasan:**
- `-preset slow`: Encoding lambat tapi quality lebih bagus (ukuran file lebih kecil)
- `-crf 18`: Constant Rate Factor, 18 = very high quality
- `-s 2560x1440`: Resolution 2K
- `-r 30`: 30 FPS
- `-an`: Hapus audio dari video (karena audio terpisah)

**Tips untuk transisi bagus:**
- Pastikan frame pertama dan terakhir video mirip untuk looping seamless
- Atau tambahkan fade di awal/akhir video secara manual di editor

### Audio Loop (Recommended Settings)

```bash
ffmpeg -i input_audio.mp3 \
  -c:a aac \
  -b:a 256k \
  -ar 48000 \
  assets/audio_loop.mp3
```

**Penjelasan:**
- `-c:a aac`: AAC codec untuk quality tinggi
- `-b:a 256k`: 256 kbps bitrate (excellent untuk ASMR)
- `-ar 48000`: 48kHz sample rate (professional quality)

**Tips ASMR:**
- Gunakan bitrate minimal 256k untuk preserve detail suara ASMR
- Bisa gunakan 320k untuk quality maksimal
- Audio loop bisa beda durasi dari video (akan loop independent)

## Usage

### Start Streaming

```bash
python stream.py
```

Program akan menanyakan mode:
1. **Single stream**: Manual restart jika disconnect
2. **Auto-restart**: Otomatis reconnect (recommended untuk streaming 24/7)

### Stop Streaming

Tekan `Ctrl+C` untuk stop streaming dengan graceful.

## Configuration Options

Edit `config.json` untuk customize:

```json
{
  "youtube": {
    "rtmp_url": "rtmp://a.rtmp.youtube.com/live2",
    "stream_key": "YOUR_STREAM_KEY"
  },
  "video": {
    "file": "assets/video_loop.mp4",
    "resolution": "2560x1440",
    "bitrate": "10M",          // 10 Mbps untuk 2K
    "preset": "slow",          // slow = best quality/CPU balance
    "codec": "libx264"
  },
  "audio": {
    "file": "assets/audio_loop.mp3",
    "bitrate": "256k",         // 256 kbps untuk ASMR
    "codec": "aac"
  },
  "streaming": {
    "buffer_size": "20M",      // Buffer besar = lebih stabil
    "reconnect_delay_seconds": 5,
    "max_reconnect_attempts": 10
  },
  "monitoring": {
    "enabled": true,
    "log_interval_seconds": 30,
    "log_file": "stream_monitor.log"
  }
}
```

### Bitrate Recommendations

**Video (2K - 2560x1440):**
- Minimal: 8 Mbps
- Recommended: **10 Mbps** (default)
- Maximum: 12 Mbps

**Audio (ASMR):**
- Good: 192k
- **Recommended: 256k** (default)
- Excellent: 320k

## Getting YouTube Stream Key

1. Buka [YouTube Studio](https://studio.youtube.com)
2. Klik **"Go Live"** atau **"Create" → "Go Live"**
3. Pilih **"Stream"** (bukan webcam)
4. Copy **Stream Key** dari halaman stream settings
5. Paste ke `config.json` di field `youtube.stream_key`

**PENTING:** Jangan share stream key ke siapa pun!

## Monitoring

Log file `stream_monitor.log` akan berisi:
- CPU usage (system & FFmpeg process)
- RAM usage (system & FFmpeg process)
- Timestamp setiap log

Contoh log:
```
2025-12-11 10:30:00 - CPU: 15.2% | RAM: 45.1% (7.23 GB) | FFmpeg CPU: 8.5% | FFmpeg RAM: 245.3 MB
2025-12-11 10:30:30 - CPU: 14.8% | RAM: 45.2% (7.24 GB) | FFmpeg CPU: 8.2% | FFmpeg RAM: 243.1 MB
```

## Troubleshooting

### "FFmpeg not found"
Install FFmpeg menggunakan package manager (lihat Installation).

### "Stream disconnects frequently"
- Cek koneksi internet
- Increase buffer_size di config (coba 30M atau 40M)
- Turunkan bitrate video (coba 8M atau 9M)

### "High CPU usage"
- Pastikan video sudah di-pre-encode dengan settings recommended
- Gunakan `preset: "ultrafast"` di config untuk real-time encoding lebih cepat (quality sedikit turun)
- Atau gunakan video codec copy jika video sudah perfect: `"codec": "copy"`

### "Audio/Video out of sync"
- Normal untuk looping independent - audio dan video tidak sync by design
- Jika ingin sync, pastikan durasi video dan audio sama persis

### "YouTube rejects stream"
- Pastikan stream key benar
- Pastikan YouTube live streaming sudah enabled di channel kamu
- Channel baru perlu menunggu 24 jam setelah enable live streaming

## File Structure

```
stream/
├── stream.py                 # Main application
├── config.json              # Your configuration (create from example)
├── config.example.json      # Configuration template
├── requirements.txt         # Python dependencies
├── stream_monitor.log       # Monitoring logs (auto-generated)
├── assets/                  # Your video and audio files
│   ├── video_loop.mp4      # 2-minute video loop
│   └── audio_loop.mp3      # Audio loop (any duration)
└── README.md               # This file
```

## Tips untuk ASMR Streaming

1. **Audio Quality adalah Priority**: Gunakan minimal 256k bitrate untuk audio
2. **Pre-encode assets**: Jangan realtime encode, pre-encode dulu untuk CPU minimal
3. **Buffer Besar**: 20-40MB buffer untuk prevent buffering/stuttering
4. **Preset Slow**: Gunakan `preset: slow` untuk pre-encoding (smaller file, better quality)
5. **Independent Loops**: Audio dan video bisa beda durasi, akan loop sendiri-sendiri
6. **Test dulu**: Test streaming 10-15 menit dulu sebelum stream panjang

## Advanced: 24/7 Streaming

Untuk streaming 24/7, gunakan auto-restart mode dan consider:

1. **System sleep**: Disable sleep mode di sistem operasi
2. **Screen saver**: Disable screen saver
3. **Network stability**: Gunakan ethernet jika memungkinkan
4. **Monitor logs**: Check `stream_monitor.log` regular untuk track stability

## License

Free to use for personal and commercial ASMR streaming.

## Support

Jika ada masalah atau pertanyaan, check troubleshooting section atau review FFmpeg logs.
