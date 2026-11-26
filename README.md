# V3 Browser Bridge (read-only preview)

Windows: stop bot, close virtual positions, stop server, back up runtime.
```powershell
git clone -b v2-preview https://github.com/JaGir9/tradewill.git
cd tradewill
.\INSTALL.bat
.\START.bat
```
Existing checkout: git fetch origin; git switch v2-preview; git pull --ff-only origin v2-preview; then INSTALL and START.

1. Open http://127.0.0.1:8000 in normal Chrome or Edge.
2. Open chrome://extensions (Edge: edge://extensions), enable developer mode, Load unpacked, select extension folder.
3. Click COPY PAIRING KEY in dashboard. Open extension Details > Extension options, paste key and Save. Repeat after backend restart.
4. Open https://tradewill.id in a normal tab and log in manually. Refresh TradeWill after installing extension. No automated CAPTCHA handling.
5. Dashboard shows fresh bridge heartbeat and candidate account/balance text if selectors match. These are not authenticated account values.
6. Offline synthetic mode remains runnable. Simulation still requires authorized external bid/ask and closed M1 bars. No live feed collector, broker account switching, demo or real execution is implemented. Do not treat bridge heartbeat as login proof.
7. STOP entry, close virtual positions, Ctrl+C to shut down. Remove extension or clear key when finished.

V3 is untested in browser/runtime. Only use one TradeWill tab to avoid conflicting observations. No credentials or cookies collected. Pairing key is local and must not be shared.

---
# Panduan mulai dari nol

Baca [tutorial Windows lengkap](docs/PANDUAN_WINDOWS.md). Gunakan branch `v2-preview`, jalankan `INSTALL.bat` lalu `START.bat`.

# V2.1 manual login launcher

Install dependencies and Chromium: `.venv\\Scripts\\python.exe -m pip install -r requirements.txt` then `.venv\\Scripts\\python.exe -m playwright install chromium`. Start backend and click LOGIN TRADEWILL. Enter credentials and OTP only on broker website. Persistent browser profile under runtime/browser_profile is sensitive. This launcher does not verify login, enumerate accounts, switch accounts or collect quotes. Simulation still requires an authorized external feed; broker demo and real execution remain locked. Offline mode is synthetic. No automatic login gate is claimed. V2.1 has not been runtime tested.

# TradeWill Quant Engine V2 — external-feed paper preview

**Status:** experimental, untested V2. No verified TradeWill connector, no real or broker-demo orders, no automatic broker balance. External quotes are supplied by a separate authorized adapter; the engine cannot authenticate their provenance. Do not expose localhost or use real money. Offline synthetic mode is retained for software testing only.

## Windows installation

```powershell
git clone https://github.com/JaGir9/tradewill.git
cd tradewill
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 or run START.bat. Existing checkout: stop server, back up runtime database, then git pull --ff-only. Do not commit runtime, credentials, HAR or browser profiles.

## Usage

Select SIMULATION, switch account, set virtual balance before first trade, save strategy and lot settings. Start requires a fresh external quote and 210–500 closed M1 candles. OFFLINE synthetic test is available without a feed. DEMO TradeWill and REAL USD/CENT are configuration-only. Stop pauses entry; emergency closes paper positions only with fresh data. Positions are memory-only; do not restart with open positions. SQLite stores closed trades. No margin/swap model or verified contract specs yet.

## External feed contract

POST /api/feed with JSON {symbol, bid, ask, timestamp, bars}. Timestamp is Unix seconds, bars are ordered closed M1 candles with timestamp (minute start), open, high, low, close. Supply 210–500 bars on every update, last bar within 180 seconds; quote within 10 seconds. Feed stale pauses entry. Use an authorized provider; no TradeWill feed adapter is included. This interface is not proof of live data. Simulation uses ask for buys and bid for sells, opposite side for exit, assumed commissions. Spread and contract risk estimates remain approximate.

## Commands

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/state
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/account -ContentType application/json -Body '{"account":"simulation"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/virtual-balance -ContentType application/json -Body '{"amount":100}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/control/start
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/control/stop
```

Default AUTO: Sniper Pullback + Momentum Breakout, score 85, auto lot, max 1 position, risk 0.5%, daily loss 2%. No AI. Scores are not win probabilities. See app/strategy.py.

## Release gates for broker execution

Authorized API/browser integration, account identity/currency verification, actual balance/equity/free margin, instrument specifications, broker-side SL/TP, idempotent order reconciliation, demo execution tests, persistent recovery, explicit real enablement. None of these gates are completed by this preview.

## Tests

Install pytest/httpx and run pytest -q. Existing V1 tests may need migration to the new default account; V2 has not been executed in this environment.

## V1 reference

# TradeWill Universal Quant Engine V1 - PAPER ONLY

Prototype lokal **tanpa AI**, dengan dashboard `http://127.0.0.1:8000`, strategi **Adaptive Sniper Pullback** dan **Momentum Breakout**, akun DEMO paper, konfigurasi lot/risk/entry 1-3, history SQLite, dan kontrol START / PAUSE / STOP / EMERGENCY PAPER CLOSE.

> **PENTING:** Repo ini **belum** terhubung ke server atau akun TradeWill. Harga secara sengaja **SINTETIS**, bukan harga asli. Akun REAL USD dan REAL CENT adalah pilihan konfigurasi yang **terkunci**. Tidak ada login TradeWill, perubahan akun broker, BUY/SELL/CLOSE real, API trading broker, atau klaim profit. Jangan gunakan untuk perdagangan uang asli.

## Instalasi Windows

Python 3.11+ disarankan. Ekstrak/clone repository lalu jalankan `START.bat`, atau secara manual:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Buka **http://127.0.0.1:8000**. Pilih **DEMO**, atur strategi/lot, **SAVE CONFIGURATION**, lalu **START**. Posisi PAPER aktif saat ini hanya disimpan dalam memori; restart server akan menghilangkan posisi aktif dari simulasi (riwayat closed trade tetap di SQLite). Jangan menganggap ini recovery broker. Posisi tercipta hanya jika kondisi sinyal memenuhi aturan dan risiko mengizinkan. Nilai saldo awal DEMO $10.000 hanyalah contoh.

## Strategi default

- `AUTO`: dua strategi aktif: Sniper Pullback dan Momentum Breakout.
- Data 210+ candle, EMA 9/21/50/200, RSI 14, ATR 14, filter spread relatif terhadap ATR, candle body, trend/struktur sederhana.
- Minimum score 85 (skor aturan, **bukan peluang menang**). Hasil sinyal `BUY`, `SELL`, atau `WAIT`.
- Lot `AUTO` berdasarkan jarak stop, ukuran kontrak dan biaya estimasi, dibatasi total risiko posisi 0,5% equity. `MANUAL` tetap harus lolos batas risiko, min lot dan lot step.
- Default maksimum 1 posisi. Mode 2x/3x hanya menambah posisi sesudah profit dan pergerakan harga memadai; **tidak ada martingale, grid atau averaging kerugian**.
- SL 1,5 ATR / struktur, take profit 1,5R (pullback) / 2R (breakout), trailing simulasi, daily loss guard.
- Penghitungan spread, fee, kontrak pada `app/core.py` adalah **asumsi PAPER**, bukan spesifikasi broker yang telah divalidasi.

## Start/Pause/Stop dan akun

- `START`: entry aktif, hanya DEMO paper.
- `PAUSE ENTRY`: hentikan entry baru, pemantauan/exit posisi paper berjalan.
- `STOP`: hentikan entry baru, posisi paper **tidak otomatis ditutup**; pemantauan/exit tetap berjalan selama backend aktif.
- `EMERGENCY PAPER CLOSE`: hentikan entry dan tutup posisi paper. Tidak ada aksi broker.
- `SWITCH ACCOUNT`: tersedia ketika STOP dan tidak ada posisi. Saat memilih REAL USD/CENT hanya konfigurasi lokal yang berubah, **bukan akun aktif website**. Tombol START untuk akun real ditolak backend.
- Config dan statistik tersimpan terpisah per akun. Akun real tidak menampilkan saldo fiktif.

## Pengujian

```bash
pip install pytest httpx
pytest -q
```

## Arsitektur

- `app/strategy.py`: indikator dan keputusan entry deterministik.
- `app/core.py`: engine paper, kontrol, sizing, risiko, SQLite, konfigurasi akun.
- `app/main.py`: FastAPI lokal, endpoint status/pengaturan/kontrol.
- `app/static/`: dashboard browser, responsive.
- `tests/`: pengujian strategy, risk, isolation, dan API.

API: `GET /api/state`, `POST /api/config`, `POST /api/account`, `POST /api/control/{start|pause|stop|emergency}`, `GET /api/history`, `GET /api/broker/status`, `WS /ws`. Server **harus** di-bind ke loopback `127.0.0.1`, bukan `0.0.0.0`. Jangan mengeksposnya ke jaringan publik. Tidak ada autentikasi dashboard multi-pengguna.

## Syarat sebelum koneksi broker

1. Konfirmasi izin automasi dan dokumentasi API resmi broker/MT5, atau verifikasi browser automation dengan akun demo berizin.
2. Verifikasi login persisten, daftar akun, currency REAL/CENT/DEMO, selector pindah akun, dan account-ID setelah switch.
3. Verifikasi tick bid/ask, history M1/M5, contract unit, tick value, komisi, margin, dan spread per akun.
4. Uji end-to-end BUY/SELL/CLOSE/SL/TP serta order reconciliation, timeout tidak menggandakan order, reconnect, kill switch, dan perbedaan realized PnL.
5. Backtest data pasar nyata dengan biaya, lalu paper/demo forward test. Tidak ada target win rate yang dijamin.

**Jangan commit** cookies, HAR, password, token, file sesi browser, atau data akun sensitif ke GitHub publik. `.gitignore` mengabaikan beberapa pola, tetapi bukan jaminan sanitasi.
