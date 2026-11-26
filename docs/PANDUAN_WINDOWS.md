# Panduan Windows — V2.1 Preview

## 1. Instalasi pertama (PowerShell)
Install Python 3.11+ dan Git for Windows. Buka PowerShell:
```powershell
git --version
py -3 --version
git clone -b v2-preview https://github.com/JaGir9/tradewill.git
cd tradewill
.\INSTALL.bat
.\START.bat
```
Buka http://127.0.0.1:8000. Biarkan terminal aktif.

## 2. Update instalasi lama
STOP entry, tutup posisi paper, lalu Ctrl+C di terminal backend. Cadangkan runtime (termasuk profil sensitif; jangan unggah).
```powershell
git status
git fetch origin
git switch v2-preview
git pull --ff-only origin v2-preview
.\INSTALL.bat
.\START.bat
```
Jika ada konflik, jangan reset paksa. Refresh browser Ctrl+F5.

## 3. Uji software sampai RUNNING
Pilih OFFLINE synthetic test, klik SWITCH ACCOUNT, atur AUTO strategy, AUTO RISK, maksimum 1 posisi, SAVE CONFIGURATION, START. Status RUNNING tidak berarti langsung ada entry. WAIT adalah hasil normal. Harga dan P/L sintetis, bukan pasar live.
Di PowerShell kedua:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/state
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/account -ContentType application/json -Body '{"account":"demo"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/control/start
Invoke-RestMethod http://127.0.0.1:8000/api/history
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/control/pause
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/control/stop
```
Jalankan pemilihan akun hanya ketika STOPPED tanpa posisi. Jika masih ada posisi paper, gunakan EMERGENCY PAPER CLOSE sebelum mematikan backend.

## 4. Login broker
Klik LOGIN TRADEWILL, login manual di Chromium dengan email/password/OTP. Jangan kirim kredensial ke GitHub. Profil disimpan lokal. Cek:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/broker/login-status
```
browser_running bukan bukti autentikasi. Deteksi login dan pergantian akun broker belum tersedia.

## 5. Simulation external feed
STOP, pastikan tidak ada posisi, pilih SIMULATION dan set saldo awal sebelum transaksi pertama.
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/account -ContentType application/json -Body '{"account":"simulation"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/virtual-balance -ContentType application/json -Body '{"amount":100}'
Invoke-RestMethod http://127.0.0.1:8000/api/state
```
START hanya setelah feed_ready true. Adapter TradeWill live belum tersedia. Endpoint /api/feed membutuhkan bid, ask, timestamp Unix detik, symbol, dan 210–500 candle M1 tertutup. Tidak ada perintah yang dapat membuat feed TradeWill aktif tanpa adapter. Demo broker dan real tetap terkunci.

## 6. Troubleshooting
- START abu-abu: cek status, akun, feed_ready.
- Login browser tidak terbuka: jalankan INSTALL.bat, cek terminal.
- Port 8000 terpakai: hentikan instance lama; jangan menjalankan dua engine pada database yang sama.
- API docs: http://127.0.0.1:8000/docs
- Tests: .venv\Scripts\python.exe -m pip install pytest httpx ; .venv\Scripts\python.exe -m pytest -q
- V2.1 dan launcher baru belum diuji runtime oleh pengembang dalam update dokumentasi ini.

## 7. Shutdown
STOP menghentikan entry, bukan server. Tutup posisi virtual dengan harga valid, cek open positions = 0, lalu Ctrl+C di terminal. Posisi aktif belum persisten. Jangan gunakan uang asli.
