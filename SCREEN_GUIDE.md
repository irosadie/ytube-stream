# 📺 Panduan Screen - Streaming 24/7 di Server

Panduan lengkap menggunakan `screen` untuk menjalankan streaming YouTube 24/7 di server, bisa logout/tutup terminal tanpa menghentikan stream.

---

## 🚀 Quick Start (5 Menit)

```bash
# 1. Install screen (jika belum ada)
sudo apt install screen

# 2. Buat session screen
screen -S streaming

# 3. Masuk ke folder project & aktifkan venv
cd /path/ke/ytube-stream
source myenv/bin/activate

# 4. Jalankan streaming
python stream.py
# Pilih option 2 (auto-restart)

# 5. Detach (keluar tanpa stop stream)
# Tekan: Ctrl+A, kemudian tekan D

# 6. Selesai! Stream jalan di background
# Anda bisa logout/tutup terminal
```

---

## 📖 Tutorial Lengkap Step-by-Step

### Step 1: Install Screen

Screen biasanya sudah terinstall di banyak server Linux. Jika belum:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install screen
```

**CentOS/RHEL:**
```bash
sudo yum install screen
```

**MacOS:**
```bash
brew install screen
```

### Step 2: Persiapan

SSH ke server Anda dan masuk ke folder project:

```bash
ssh username@your-server.com
cd /path/ke/ytube-stream
```

### Step 3: Buat Session Screen Baru

```bash
screen -S streaming
```

**Penjelasan:**
- `screen` = command untuk menjalankan screen
- `-S streaming` = beri nama session "streaming" (bisa diganti sesuai keinginan)

Anda akan masuk ke dalam session screen baru (terlihat seperti terminal biasa).

### Step 4: Aktifkan Virtual Environment

Di dalam screen, aktifkan virtual environment:

```bash
source myenv/bin/activate
```

Prompt akan berubah menunjukkan virtual environment aktif: `(myenv) user@server:~/ytube-stream$`

### Step 5: Jalankan Streaming

```bash
python stream.py
```

Pilih **option 2** untuk auto-restart:
```
Options:
1. Stream once (manual restart if disconnected)
2. Auto-restart on disconnection (recommended for 24/7)

Select option (1 or 2): 2
```

Stream akan mulai dan Anda akan melihat output:
```
✅ Streaming dimulai! Data sedang dikirim ke YouTube...
[Progress] frame= 1234 fps=30 speed=1.0x bitrate=3000kbits/s
```

### Step 6: Detach dari Screen

**PENTING:** Jangan tekan Ctrl+C! Itu akan stop streaming.

Untuk keluar tanpa stop streaming:

1. Tekan **`Ctrl + A`** (tahan Ctrl, tekan A, lepas)
2. Kemudian tekan **`D`** (huruf D saja)

Anda akan melihat pesan:
```
[detached from 12345.streaming]
```

**Stream tetap jalan di background!** 🎉

### Step 7: Logout/Tutup Terminal

Sekarang Anda bisa:
- Logout dari SSH: `exit`
- Tutup terminal
- Matikan komputer lokal Anda

**Stream akan tetap berjalan di server!**

---

## 🔧 Perintah Screen Penting

### Melihat Session yang Aktif

```bash
screen -ls
```

Output contoh:
```
There are screens on:
    12345.streaming	(Detached)
    67890.backup	(Detached)
2 Sockets in /var/run/screen/S-username.
```

### Kembali ke Session (Reattach)

```bash
screen -r streaming
```

Anda akan masuk kembali ke session streaming dan bisa lihat progress real-time.

### Detach Lagi

Dalam screen, tekan: **`Ctrl + A`** kemudian **`D`**

### Stop Streaming

**Cara 1: Dari dalam screen**
```bash
# Reattach dulu
screen -r streaming

# Tekan Ctrl+C untuk stop
# Tunggu hingga script berhenti
# Ketik 'exit' untuk keluar dari screen
exit
```

**Cara 2: Kill session dari luar**
```bash
screen -X -S streaming quit
```

⚠️ Cara 2 akan langsung terminate tanpa graceful shutdown.

### Rename Session

```bash
# Dari dalam screen:
# Tekan Ctrl+A kemudian :
# Ketik: sessionname nama_baru
# Tekan Enter
```

---

## 📊 Monitoring Stream

### Cek Apakah Stream Masih Jalan

```bash
# Cek screen session
screen -ls

# Cek FFmpeg process
ps aux | grep ffmpeg

# Cek resource usage
top -p $(pgrep -f ffmpeg)
```

### Lihat Output Real-time

```bash
# Reattach ke session
screen -r streaming

# Anda akan melihat:
# - Progress encoding
# - Bitrate dan speed
# - Error messages (jika ada)
# - CPU/RAM usage (jika monitoring enabled)
```

### Lihat Log (Jika Monitoring Enabled)

```bash
tail -f stream_monitor.log
```

---

## 🎯 Skenario Umum

### Skenario 1: Stream 24/7 Tanpa Pengawasan

```bash
# Setup sekali:
screen -S streaming
cd /path/ke/ytube-stream
source myenv/bin/activate
python stream.py
# Pilih option 2

# Detach: Ctrl+A, D
# Logout: exit

# Check sekali sehari:
ssh user@server
screen -r streaming
# Lihat sebentar
# Detach: Ctrl+A, D
```

### Skenario 2: Update Config Saat Stream Jalan

```bash
# SSH ke server
ssh user@server

# Edit config (stream tetap jalan)
cd /path/ke/ytube-stream
nano config.json
# Save changes

# Stop stream lama
screen -r streaming
# Ctrl+C untuk stop
exit

# Start stream baru dengan config baru
screen -S streaming
source myenv/bin/activate
python stream.py
# Ctrl+A, D untuk detach
```

### Skenario 3: Multiple Stream (Beda Akun YouTube)

```bash
# Stream 1
screen -S stream1
cd /path/ke/stream1
source myenv/bin/activate
python stream.py
# Ctrl+A, D

# Stream 2
screen -S stream2
cd /path/ke/stream2
source myenv/bin/activate
python stream.py
# Ctrl+A, D

# Lihat semua session
screen -ls

# Switch antar session
screen -r stream1
screen -r stream2
```

---

## 🆘 Troubleshooting

### Session Screen Hilang Setelah Reboot

Screen session tidak otomatis restart setelah server reboot. Solusi: setup auto-start (lihat bagian Auto-Start di bawah).

### Tidak Bisa Reattach (Session Attached)

```bash
# Jika muncul: There is a screen on... (Attached)
# Artinya session masih attached di terminal lain

# Force detach:
screen -d streaming

# Lalu reattach:
screen -r streaming
```

### Screen Freeze/Hang

```bash
# Tekan Ctrl+A kemudian Q untuk quit screen
# Atau dari luar:
screen -X -S streaming quit
```

### Lupa Nama Session

```bash
# List semua session dengan detail
screen -ls

# Reattach ke session pertama yang ditemukan
screen -r
```

---

## 🤖 Auto-Start Setelah Server Reboot

### Metode 1: Crontab (Mudah)

```bash
# Edit crontab
crontab -e
```

Tambahkan baris ini:
```cron
@reboot screen -dmS streaming bash -c "cd /path/ke/ytube-stream && source myenv/bin/activate && python stream.py <<< '2'"
```

**Penjelasan:**
- `@reboot` = jalankan saat server reboot
- `screen -dmS streaming` = buat detached screen session
- `bash -c "..."` = jalankan command
- `<<< '2'` = otomatis pilih option 2 (auto-restart)

### Metode 2: Systemd Service (Advanced)

Buat file `/etc/systemd/system/ytube-stream.service`:

```bash
sudo nano /etc/systemd/system/ytube-stream.service
```

Isi dengan:
```ini
[Unit]
Description=YouTube ASMR Stream
After=network.target

[Service]
Type=forking
User=username
WorkingDirectory=/path/ke/ytube-stream
ExecStart=/usr/bin/screen -dmS streaming /path/ke/ytube-stream/myenv/bin/python /path/ke/ytube-stream/stream.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

⚠️ **Catatan:** Systemd service akan auto-pilih option, perlu modifikasi script atau buat wrapper script.

Enable service:
```bash
sudo systemctl enable ytube-stream
sudo systemctl start ytube-stream
```

---

## 💡 Tips & Best Practices

### 1. Naming Convention untuk Session

Gunakan nama yang deskriptif:
```bash
screen -S youtube-asmr-main
screen -S youtube-music-backup
screen -S test-stream
```

### 2. Log Output ke File

```bash
# Jalankan dengan output log
screen -S streaming
source myenv/bin/activate
python stream.py 2>&1 | tee stream.log

# Detach: Ctrl+A, D

# Lihat log dari terminal lain
tail -f stream.log
```

### 3. Screen Config Custom

Buat file `~/.screenrc`:
```bash
# Disable startup message
startup_message off

# Set scrollback buffer
defscrollback 10000

# Status bar
hardstatus on
hardstatus alwayslastline
hardstatus string "%{.bW}%-w%{.rY}%n %t%{-}%+w %=%{..G} %H %{..Y} %Y-%m-%d %c"

# Auto detach on hangup
autodetach on
```

### 4. Keyboard Shortcuts Berguna

| Shortcut | Fungsi |
|----------|--------|
| `Ctrl+A, D` | Detach session |
| `Ctrl+A, K` | Kill session (dengan konfirmasi) |
| `Ctrl+A, C` | Buat window baru dalam session |
| `Ctrl+A, N` | Next window |
| `Ctrl+A, P` | Previous window |
| `Ctrl+A, "` | List semua window |
| `Ctrl+A, [` | Enter copy mode (scroll back) |
| `Ctrl+A, ?` | Help |

### 5. Monitoring dengan Watch

```bash
# Auto-refresh setiap 2 detik
watch -n 2 'screen -ls && ps aux | grep ffmpeg | grep -v grep'
```

---

## 📱 Remote Monitoring dari HP/Tablet

### Gunakan Termux (Android) atau iSH (iOS)

```bash
# Install Termux atau iSH
# Install openssh
pkg install openssh  # Termux
apk add openssh      # iSH

# SSH ke server
ssh user@your-server.com

# Reattach ke screen
screen -r streaming

# Lihat status
# Detach: Ctrl+A, D
```

### Gunakan SSH Apps
- **Android:** Termux, JuiceSSH, ConnectBot
- **iOS:** Termius, Prompt, Blink

---

## ✅ Checklist: Streaming Sudah Benar

- [ ] Screen session aktif (`screen -ls` menampilkan session)
- [ ] FFmpeg process berjalan (`ps aux | grep ffmpeg`)
- [ ] Bisa detach dan reattach tanpa masalah
- [ ] Stream muncul di YouTube Live Dashboard
- [ ] Auto-restart enabled (option 2)
- [ ] Sudah test disconnect dan reconnect
- [ ] Log monitoring berjalan (jika enabled)
- [ ] Bisa logout SSH tanpa stream mati

---

## 🎓 Kesimpulan

**Screen adalah tool yang sangat powerful untuk:**
- ✅ Menjalankan proses jangka panjang di server
- ✅ Menjaga proses tetap hidup meski SSH disconnect
- ✅ Monitoring real-time kapan saja
- ✅ Multiple session untuk multiple stream

**Workflow Standard:**
```
Login → Screen → VEnv → Stream → Detach → Logout
```

**Untuk monitoring:**
```
Login → Reattach → Check Status → Detach → Logout
```

---

**Happy Streaming! 🎥🚀**

Jika ada pertanyaan atau masalah, buat issue di GitHub repository.
