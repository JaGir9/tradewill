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
