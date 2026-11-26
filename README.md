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
