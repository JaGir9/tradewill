"""Fail-closed demo strategy evaluation. NEVER submits broker orders."""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
from threading import RLock
import math
import time
from .strategy import decide
from .core import SPECS

class DemoAuto:
    def __init__(self):
        self.lock = RLock()
        self.enabled = False
        self.last_bar = ""
        self.last_decision = None
        self.audit = []
        self.account_verified = False

    def enable(self, enabled: bool):
        with self.lock:
            self.enabled = bool(enabled)
            if not enabled:
                self.last_bar = ""
            self._log("AUTOMATED DEMO STRATEGY TEST " + ("ENABLED" if enabled else "DISABLED"))

    def _log(self, message):
        self.audit.append({"ts":datetime.now(timezone.utc).isoformat(), "event":message})
        self.audit = self.audit[-100:]

    def evaluate(self, feed, bridge, config):
        """Generate at most one advisory decision per closed bar, with explicit rejection reasons."""
        with self.lock:
            status = bridge.status()
            data = status.get("observation", {})
            reasons = []
            if not self.enabled:
                reasons.append("disabled")
            if not status.get("fresh"):
                reasons.append("stale bridge")
            if data.get("domain") != "tradewill.id" and not str(data.get("domain", "")).endswith(".tradewill.id"):
                reasons.append("invalid domain")
            # DOM account text is a hint, NOT a verified broker identity.
            if not data.get("account_marker") or data.get("login_form") or not data.get("trading_ui"):
                reasons.append("account UI unavailable")
            if not (data.get("account_hint") or "").lower().startswith("demo"):
                reasons.append("demo account not observed")
            if not self.account_verified:
                reasons.append("broker demo identity not authenticated")
            s = feed.status()
            if not s.get("fresh") or s.get("closed_candles", 0) < 210:
                reasons.append("insufficient fresh closed candles")
            if s.get("symbol") != config["symbol"]:
                reasons.append("symbol mismatch")
            bid, ask = data.get("bid"), data.get("ask")
            if not isinstance(bid, (int, float)) or not isinstance(ask, (int, float)) or not all(map(math.isfinite, (bid, ask))) or bid <= 0 or ask < bid:
                reasons.append("invalid quote")
            if reasons:
                return {"status":"BLOCKED", "reasons":reasons, "execution":"DISABLED", "last_decision":self.last_decision}
            bar = feed.bars[-1].timestamp
            if self.last_bar == bar:
                return {"status":"ALREADY_EVALUATED", "execution":"DISABLED", "last_decision":self.last_decision}
            self.last_bar = bar
            signal = decide(list(feed.bars), ask-bid, min_score=config["min_score"],
                use_pullback=config["pullback"] and config["mode"]!="MOMENTUM_BREAKOUT",
                use_breakout=config["breakout"] and config["mode"]!="SNIPER_PULLBACK")
            if config["direction"] not in ("BOTH", signal.side) and signal.side != "WAIT":
                reasons.append("direction blocked")
            decision = {"bar":bar, "symbol":s["symbol"], "signal":asdict(signal),
                        "reasons":reasons, "execution":"DISABLED", "timestamp":time.time()}
            self.last_decision = decision
            self._log("SIGNAL " + signal.side + " " + signal.strategy + " score=" + str(signal.score) + " (NO BROKER ORDER)")
            return {"status":"EVALUATED", "execution":"DISABLED", "last_decision":decision}

    def status(self):
        with self.lock:
            return {"enabled":self.enabled, "broker_execution":"DISABLED",
                    "account_verified":self.account_verified,
                    "last_decision":self.last_decision, "audit":list(reversed(self.audit[-30:]))}
