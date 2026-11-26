# V3.1 — Existing browser session detection

Stop engine and close virtual positions before updating. Back up runtime, Ctrl+C backend.
```powershell
git fetch origin
git switch v2-preview
git pull --ff-only origin v2-preview
.\INSTALL.bat
.\START.bat
```
Open chrome://extensions, reload TradeWill Read-only Bridge (3.1.0). Open localhost, COPY PAIRING KEY, paste in extension options and Save. Refresh the already logged-in TradeWill trading tab. No logout required. Use one TradeWill tab only.

Check:
```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/bridge/status | ConvertTo-Json -Depth 5
```
DISCONNECTED: no heartbeat in 15 seconds. TAB_CONNECTED_ACCOUNT_UNKNOWN: tab connected but selectors not found. LOGIN_REQUIRED_OR_FORM_VISIBLE: visible password input (not definitive logout). TRADING_UI_DETECTED: trading UI candidate. ACCOUNT_UI_DETECTED: trading UI and account marker visible; not authenticated identity. All authentication remains UNVERIFIED. Market feed and broker orders remain disabled. No CAPTCHA bypass. Selectors are experimental, top-level DOM only; no runtime testing yet.
