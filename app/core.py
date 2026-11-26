"""Paper execution, account isolation and deterministic risk checks."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
import json
import math
import random
import sqlite3
import time
from .strategy import Candle, decide, Signal


BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "runtime" / "trading.sqlite3"
SPECS = {
    # PAPER assumptions, not verified TradeWill live contract specifications.
    "XAUUSD": {"contract": 100.0, "min_lot": .01, "step": .01, "max_lot": 3., "commission_per_lot": 15.0, "spread": .15, "start": 3570.0},
    "EURUSD": {"contract": 100000.0, "min_lot": .01, "step": .01, "max_lot": 2., "commission_per_lot": 10.0, "spread": .00012, "start": 1.16},
    "BTCUSD": {"contract": 1.0, "min_lot": .01, "step": .01, "max_lot": 5., "commission_per_lot": 15.0, "spread": 12.0, "start": 90000.0},
}
DEFAULT_CONFIG = {"symbol": "XAUUSD", "mode": "AUTO", "lot_mode": "AUTO", "manual_lot": .01,
                  "risk_pct": .5, "max_positions": 1, "min_score": 85,
                  "pullback": True, "breakout": True, "daily_loss_pct": 2.0,
                  "direction": "BOTH", "trailing": True}
ACCOUNTS = {
    "demo": {"id": "demo", "label": "DEMO (paper)", "type": "DEMO", "currency": "USD", "paper": True, "initial_usd": 10000.},
    "real_usd": {"id": "real_usd", "label": "REAL USD - koneksi belum tersedia", "type": "REAL", "currency": "USD", "paper": False, "initial_usd": None},
    "real_cent": {"id": "real_cent", "label": "REAL CENT - koneksi belum tersedia", "type": "REAL", "currency": "CENT", "paper": False, "initial_usd": None},
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def finite(v: object, min_value: float | None = None, max_value: float | None = None) -> float:
    if isinstance(v, bool):
        raise ValueError("Nilai numerik tidak valid")
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError("Nilai numerik tidak valid") from None
    if not math.isfinite(x) or (min_value is not None and x < min_value) or (max_value is not None and x > max_value):
        raise ValueError("Nilai di luar batas")
    return x


def validate_config(data: dict) -> dict:
    unknown = set(data) - set(DEFAULT_CONFIG)
    if unknown:
        raise ValueError("Pengaturan tidak dikenal: " + ", ".join(sorted(unknown)))
    cfg = {**DEFAULT_CONFIG, **data}
    if cfg["symbol"] not in SPECS or cfg["mode"] not in {"AUTO", "SNIPER_PULLBACK", "MOMENTUM_BREAKOUT"}:
        raise ValueError("Instrumen/strategi tidak tersedia")
    if cfg["direction"] not in {"BOTH", "BUY", "SELL"} or cfg["lot_mode"] not in {"AUTO", "MANUAL"}:
        raise ValueError("Pilihan arah/lot tidak valid")
    cfg["risk_pct"] = finite(cfg["risk_pct"], .1, 1.)
    cfg["daily_loss_pct"] = finite(cfg["daily_loss_pct"], .5, 5.)
    cfg["manual_lot"] = finite(cfg["manual_lot"], .01, 5.)
    if type(cfg["max_positions"]) is not int or cfg["max_positions"] not in {1, 2, 3}:
        raise ValueError("Maksimum posisi 1, 2, atau 3")
    if type(cfg["min_score"]) is not int or not 70 <= cfg["min_score"] <= 100:
        raise ValueError("Score harus 70-100")
    for key in ("pullback", "breakout", "trailing"):
        if type(cfg[key]) is not bool:
            raise ValueError(key + " harus boolean")
    if not (cfg["pullback"] or cfg["breakout"]):
        raise ValueError("Aktifkan minimal satu strategi")
    return cfg


@dataclass
class Position:
    id: int
    account: str
    symbol: str
    side: str
    lot: float
    entry: float
    stop: float
    target: float
    commission: float
    strategy: str
    opened_at: str
    peak_net: float = 0.0


class Store:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS config(account TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT, account TEXT NOT NULL,
            symbol TEXT NOT NULL, side TEXT NOT NULL, lot REAL NOT NULL, strategy TEXT NOT NULL,
            entry REAL NOT NULL, exit REAL NOT NULL, net REAL NOT NULL, reason TEXT NOT NULL, opened_at TEXT, closed_at TEXT);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, account TEXT, event TEXT NOT NULL);
        """)
        self.db.execute("CREATE TABLE IF NOT EXISTS day_anchor(account TEXT, day TEXT, equity REAL NOT NULL, PRIMARY KEY(account,day))")
        self.db.commit()

    def anchor(self, account: str, day: str, default: float) -> float:
        row = self.db.execute("SELECT equity FROM day_anchor WHERE account=? AND day=?", (account, day)).fetchone()
        if row:
            return float(row["equity"])
        self.db.execute("INSERT INTO day_anchor(account,day,equity) VALUES(?,?,?)", (account, day, default))
        self.db.commit()
        return default

    def aggregates(self, account: str) -> dict:
        r = self.db.execute("SELECT COUNT(*) n, COALESCE(SUM(net),0) net, COALESCE(SUM(CASE WHEN net > 0 THEN 1 ELSE 0 END),0) wins FROM trades WHERE account=?", (account,)).fetchone()
        return {"trades":r["n"], "net":float(r["net"]), "wins":r["wins"]}

    def config(self, account: str) -> dict:
        row = self.db.execute("SELECT body FROM config WHERE account=?", (account,)).fetchone()
        return validate_config(json.loads(row["body"])) if row else dict(DEFAULT_CONFIG)

    def save_config(self, account: str, cfg: dict) -> dict:
        cfg = validate_config(cfg)
        self.db.execute("INSERT OR REPLACE INTO config(account,body) VALUES(?,?)", (account, json.dumps(cfg)))
        self.db.commit()
        return cfg

    def trade(self, p: Position, price: float, net: float, reason: str):
        self.db.execute("INSERT INTO trades(account,symbol,side,lot,strategy,entry,exit,net,reason,opened_at,closed_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (p.account, p.symbol, p.side, p.lot, p.strategy, p.entry, price, net, reason, p.opened_at, utcnow()))
        self.db.commit()

    def history(self, account: str) -> list[dict]:
        return [dict(r) for r in self.db.execute("SELECT * FROM trades WHERE account=? ORDER BY id DESC LIMIT 100", (account,))]

    def event(self, account: str, event: str):
        self.db.execute("INSERT INTO events(ts,account,event) VALUES(?,?,?)", (utcnow(), account, event[:400]))
        self.db.commit()

    def events(self, account: str) -> list[dict]:
        return [dict(r) for r in self.db.execute("SELECT ts,event FROM events WHERE account=? ORDER BY id DESC LIMIT 30", (account,))]


class Engine:
    """All state transitions protected by one lock. Real account paths are refused."""
    def __init__(self, store: Store, seed: int = 49):
        self.lock = RLock()
        self.store = store
        self.rng = random.Random(seed)
        self.account = "demo"
        self.status = "STOPPED"
        self.positions: list[Position] = []
        self.counter = 0
        self.latest_signal = Signal("WAIT", "NONE", 0, "Belum ada analisis")
        self.prices = {k: v["start"] for k, v in SPECS.items()}
        self.candles = {k: self._seed(k) for k in SPECS}
        self.day_key = datetime.now(timezone.utc).date().isoformat()
        self.day_start_equity = self.store.anchor("demo", self.day_key, self.equity())
        self.last_entry_bar = -1
        self.last_entry_price = None
        self.last_tick = time.monotonic()

    def _seed(self, symbol: str) -> list[Candle]:
        """Synthetic candles used ONLY by the offline paper prototype."""
        start = SPECS[symbol]["start"]
        step = start*.0004 if symbol != "EURUSD" else .0002
        price = start
        candles = []
        for idx in range(230):
            old = price
            price = max(step, old + self.rng.gauss(0, step) + (step*.03 if idx > 160 else 0))
            band = abs(self.rng.gauss(0, step*.32))
            candles.append(Candle(old, max(old, price)+band, min(old, price)-band, price, f"synthetic-{idx}"))
        self.prices[symbol] = price
        return candles

    def equity(self) -> float | None:
        if self.account != "demo":
            return None
        initial = float(ACCOUNTS["demo"]["initial_usd"])
        realized = self.store.aggregates("demo")["net"]
        floating = sum(self.net_pnl(p) for p in self.positions)
        return initial + realized + floating

    def net_pnl(self, p: Position, *, price: float | None = None) -> float:
        current = self.prices[p.symbol] if price is None else price
        spec = SPECS[p.symbol]
        # Spread represented by half-spread on entry and half-spread on exit.
        movement = ((current - p.entry) if p.side == "BUY" else (p.entry - current))
        return round(movement * spec["contract"] * p.lot - spec["spread"]*spec["contract"]*p.lot - p.commission, 6)

    def switch(self, account: str):
        with self.lock:
            if account not in ACCOUNTS:
                raise ValueError("Akun tidak dikenal")
            if self.status != "STOPPED" or self.positions:
                raise ValueError("Stop bot dan tutup posisi dahulu sebelum berganti akun")
            self.account = account
            self.latest_signal = Signal("WAIT", "NONE", 0, "Akun dipilih; broker belum terhubung" if account != "demo" else "Mode DEMO paper aktif")
            self.store.event(account, "Akun dipilih; tidak melakukan switching di broker")

    def configure(self, patch: dict) -> dict:
        with self.lock:
            if self.status != "STOPPED":
                raise ValueError("Stop bot sebelum mengubah konfigurasi")
            cfg = self.store.config(self.account)
            if self.positions and "symbol" in patch and patch["symbol"] != cfg["symbol"]:
                raise ValueError("Tidak boleh mengganti instrumen selama ada posisi terbuka")
            cfg.update(patch)
            return self.store.save_config(self.account, cfg)

    def start(self):
        with self.lock:
            if self.account != "demo":
                raise ValueError("Akun REAL terkunci: integrasi TradeWill belum diverifikasi")
            if self.status not in {"STOPPED", "PAUSED"}:
                raise ValueError("Bot sudah berjalan")
            self.status = "RUNNING"
            self.day_start_equity = self.store.anchor("demo", self.day_key, self.equity())
            self.store.event(self.account, "Bot RUNNING (PAPER, synthetic market)")

    def pause(self):
        with self.lock:
            if self.status != "RUNNING":
                raise ValueError("Bot tidak sedang berjalan")
            self.status = "PAUSED"
            self.store.event(self.account, "Entry PAUSED, proteksi posisi tetap aktif")

    def stop(self):
        with self.lock:
            self.status = "STOPPED"
            self.store.event(self.account, "Entry STOPPED; posisi tidak ditutup otomatis")

    def emergency(self):
        with self.lock:
            self.status = "STOPPED"
            # Only demo positions owned by this engine are affected.
            for p in list(self.positions):
                self._close(p, "EMERGENCY_PAPER")
            self.store.event(self.account, "Emergency stop: posisi PAPER ditutup")

    def _close(self, p: Position, reason: str):
        price = self.prices[p.symbol]
        net = self.net_pnl(p)
        self.store.trade(p, price, net, reason)
        self.positions.remove(p)
        self.store.event(self.account, f"PAPER close {p.symbol} #{p.id} {reason}; net={net:.2f}")

    def _open(self, signal: Signal, cfg: dict, symbol: str):
        if self.account != "demo" or self.status != "RUNNING":
            return
        spec = SPECS[symbol]
        equity = self.equity()
        if equity is None or equity <= 0:
            return
        if len(self.positions) >= cfg["max_positions"]:
            return
        if cfg["direction"] not in ("BOTH", signal.side):
            return
        price = self.prices[symbol]
        distance = abs(price - signal.stop)
        if distance <= 0:
            return
        # One total risk budget shared by ALL positions, including spread and fees.
        cap = equity*cfg["risk_pct"]/100
        used = sum(abs(p.entry-p.stop)*SPECS[p.symbol]["contract"]*p.lot + p.commission + SPECS[p.symbol]["spread"]*SPECS[p.symbol]["contract"]*p.lot for p in self.positions)
        available = cap-used
        cost_per_lot = distance*spec["contract"] + spec["commission_per_lot"] + spec["spread"]*spec["contract"]
        if cfg["lot_mode"] == "MANUAL":
            lot = cfg["manual_lot"]
            units = round(lot / spec["step"])
            if abs(units*spec["step"]-lot)>1e-8:
                self.store.event(self.account, "Lot manual tidak memenuhi step")
                return
        else:
            units = math.floor((available/cost_per_lot + 1e-10)/spec["step"])
            lot = round(units*spec["step"], 8)
        if lot < spec["min_lot"] or lot > spec["max_lot"] or lot*cost_per_lot > available+1e-8:
            self.store.event(self.account, "Entry skip: lot minimum/risk budget tidak mencukupi")
            return
        if self.positions:
            # No averaging down; need profit in existing positions, plus price improvement.
            if any(self.net_pnl(p) <= 0 for p in self.positions):
                return
            if self.last_entry_price is not None:
                if signal.side == "BUY" and price <= self.last_entry_price + signal.atr*.5:
                    return
                if signal.side == "SELL" and price >= self.last_entry_price - signal.atr*.5:
                    return
        self.counter += 1
        p = Position(self.counter, self.account, symbol, signal.side, lot, price,
                     signal.stop, signal.target, round(lot*spec["commission_per_lot"], 6),
                     signal.strategy, utcnow())
        self.positions.append(p)
        self.last_entry_price = price
        self.store.event(self.account, f"PAPER open #{p.id} {p.side} {p.symbol} {p.lot} lot")

    def tick(self):
        with self.lock:
            if self.account != "demo":
                return
            cfg = self.store.config(self.account)
            symbol = cfg["symbol"]
            spec = SPECS[symbol]
            old = self.prices[symbol]
            s = old*(.0003 if symbol != "EURUSD" else .00012)
            new = max(s, old+self.rng.gauss(0, s))
            self.prices[symbol] = new
            c = Candle(old, max(old, new)+abs(self.rng.gauss(0,s*.15)),
                       min(old,new)-abs(self.rng.gauss(0,s*.15)), new, utcnow())
            self.candles[symbol].append(c)
            self.candles[symbol] = self.candles[symbol][-500:]
            # Monitoring remains active even when entries are STOPPED or PAUSED.
            for p in list(self.positions):
                current = self.prices[p.symbol]
                pnl = self.net_pnl(p)
                p.peak_net = max(p.peak_net, pnl)
                if (p.side == "BUY" and current <= p.stop) or (p.side == "SELL" and current >= p.stop):
                    self._close(p, "STOP_LOSS")
                elif (p.side == "BUY" and current >= p.target) or (p.side == "SELL" and current <= p.target):
                    self._close(p, "TAKE_PROFIT")
                elif cfg["trailing"] and p.peak_net > p.commission*3 and pnl < p.peak_net*.6 and pnl > 0:
                    self._close(p, "PAPER_TRAILING")
            if self.status != "RUNNING":
                return
            today = datetime.now(timezone.utc).date().isoformat()
            if today != self.day_key:
                self.day_key = today
                self.day_start_equity = self.store.anchor("demo", self.day_key, self.equity())
            eq = self.equity()
            if eq is None or self.day_start_equity is None or eq < self.day_start_equity*(1-cfg["daily_loss_pct"]/100):
                self.status = "PAUSED"
                self.store.event(self.account, "Daily loss limit: entry paused")
                return
            self.latest_signal = decide(self.candles[symbol], spec["spread"], min_score=cfg["min_score"],
                                         use_pullback=cfg["pullback"] and cfg["mode"] != "MOMENTUM_BREAKOUT",
                                         use_breakout=cfg["breakout"] and cfg["mode"] != "SNIPER_PULLBACK")
            if self.latest_signal.side != "WAIT":
                # At most one new position per generated bar.
                idx = len(self.candles[symbol])
                if idx != self.last_entry_bar:
                    self.last_entry_bar = idx
                    self._open(self.latest_signal, cfg, symbol)

    def snapshot(self) -> dict:
        with self.lock:
            cfg = self.store.config(self.account)
            hist = self.store.history(self.account)
            eq = self.equity()
            stats = self.store.aggregates(self.account)
            return {"account": self.account, "accounts": [{k:v for k,v in a.items() if k!="initial_usd"} for a in ACCOUNTS.values()],
                    "broker": {"connected": False, "execution_enabled": False, "note": "TradeWill integration unavailable; REAL disabled"},
                    "market_source": "SYNTHETIC_PAPER_NOT_LIVE", "status": self.status,
                    "config": cfg, "equity": round(eq, 3) if eq is not None else None,
                    "balance": round(eq - sum(self.net_pnl(p) for p in self.positions), 3) if eq is not None else None,
                    "signal": asdict(self.latest_signal),
                    "price": round(self.prices[cfg["symbol"]], 6), "positions": [{**asdict(p), "net":self.net_pnl(p)} for p in self.positions],
                    "history": hist[:30], "events": self.store.events(self.account),
                    "metrics": {"trades":stats["trades"], "win_rate": round(100*stats["wins"]/stats["trades"],2) if stats["trades"] else None,
                                "realized_net":round(stats["net"],3)}}
