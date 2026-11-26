"""Manual login browser launcher. Does not assert broker authentication."""
from pathlib import Path
import subprocess
import sys
from threading import Lock

_lock = Lock()
_process = None

def launch():
    global _process
    with _lock:
        if _process is None or _process.poll() is not None:
            _process = subprocess.Popen([sys.executable, "-m", "app.login_browser"])
        return {"browser_requested": True, "authenticated": False}

def status():
    with _lock:
        return {"browser_running": _process is not None and _process.poll() is None,
                "authenticated": False, "verification": "NOT_IMPLEMENTED"}

def run():
    from playwright.sync_api import sync_playwright
    profile = Path(__file__).resolve().parent.parent / "runtime" / "browser_profile"
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(str(profile), headless=False)
        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://tradewill.id", wait_until="domcontentloaded")
        print("Login manually. Close browser to finish. No orders are sent.", flush=True)
        while context.pages:
            try:
                context.pages[0].wait_for_timeout(1000)
            except Exception:
                break
        context.close()

if __name__ == "__main__":
    run()
