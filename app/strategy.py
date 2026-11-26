"""Deterministic signal generation. Scores are NOT win probabilities."""
from dataclasses import dataclass
from typing import Literal
import math


@dataclass(frozen=True)
class Candle:
    open: float
    high: float
    low: float
    close: float
    timestamp: str = ""


@dataclass(frozen=True)
class Signal:
    side: Literal["BUY", "SELL", "WAIT"]
    strategy: str
    score: int
    reason: str
    atr: float = 0.0
    stop: float = 0.0
    target: float = 0.0


def ema(values: list[float], n: int) -> float:
    if len(values) < n:
        raise ValueError("insufficient candles")
    k = 2.0 / (n + 1)
    x = sum(values[:n]) / n
    for value in values[n:]:
        x = (value - x) * k + x
    return x


def atr(candles: list[Candle], n: int = 14) -> float:
    if len(candles) < n + 1:
        raise ValueError("insufficient candles")
    trs = []
    for prev, cur in zip(candles[-n-1:-1], candles[-n:]):
        trs.append(max(cur.high - cur.low, abs(cur.high - prev.close), abs(cur.low - prev.close)))
    return sum(trs) / n


def rsi(values: list[float], n: int = 14) -> float:
    if len(values) < n + 1:
        raise ValueError("insufficient candles")
    changes = [b-a for a, b in zip(values[-n-1:-1], values[-n:])]
    gain = sum(max(0.0, x) for x in changes) / n
    loss = sum(max(0.0, -x) for x in changes) / n
    if gain == 0 and loss == 0:
        return 50.0
    if loss == 0:
        return 100.0
    return 100.0 - 100.0 / (1.0 + gain/loss)


def decide(candles: list[Candle], spread: float, *, min_score: int = 85,
           use_pullback: bool = True, use_breakout: bool = True) -> Signal:
    """Uses closed OHLC bars; simple V1 entry rules, no look-ahead."""
    if len(candles) < 210:
        return Signal("WAIT", "NONE", 0, "Menunggu minimal 210 candle")
    if spread < 0 or not math.isfinite(spread):
        return Signal("WAIT", "NONE", 0, "Spread tidak valid")
    closes = [c.close for c in candles]
    a = atr(candles)
    if a <= 0 or not math.isfinite(a) or spread > max(0.01, a * 0.2):
        return Signal("WAIT", "NONE", 0, "Volatilitas atau spread tidak memenuhi batas", a)
    e9, e21, e50, e200 = (ema(closes, n) for n in (9, 21, 50, 200))
    mom = rsi(closes)
    cur, prev = candles[-1], candles[-2]
    trend_up = e9 > e21 > e50 > e200 and cur.close > e21
    trend_dn = e9 < e21 < e50 < e200 and cur.close < e21
    width = cur.high - cur.low
    if width <= 0:
        return Signal("WAIT", "NONE", 0, "Candle kosong", a)
    body = abs(cur.close - cur.open) / width
    candidates: list[Signal] = []
    # Signal score = rule checklist; not calibrated confidence.
    if use_pullback:
        if trend_up and prev.low <= e21 + 0.30*a and cur.close > cur.open and 48 <= mom <= 75:
            score = 60 + (10 if body > .5 else 0) + (10 if cur.close > prev.close else 0) + (10 if spread < a*.05 else 0) + (10 if 52 <= mom <= 68 else 0)
            stop = cur.close - max(1.5*a, cur.close-min(prev.low, cur.low))
            candidates.append(Signal("BUY", "SNIPER_PULLBACK", min(score, 100), "Pullback bullish terkonfirmasi", a, stop, cur.close + 1.5*(cur.close-stop)))
        if trend_dn and prev.high >= e21 - .30*a and cur.close < cur.open and 25 <= mom <= 52:
            score = 60 + (10 if body > .5 else 0) + (10 if cur.close < prev.close else 0) + (10 if spread < a*.05 else 0) + (10 if 32 <= mom <= 48 else 0)
            stop = cur.close + max(1.5*a, max(prev.high, cur.high)-cur.close)
            candidates.append(Signal("SELL", "SNIPER_PULLBACK", min(score, 100), "Pullback bearish terkonfirmasi", a, stop, cur.close - 1.5*(stop-cur.close)))
    if use_breakout:
        prev20 = candles[-21:-1]
        top = max(c.high for c in prev20)
        bottom = min(c.low for c in prev20)
        if cur.close > top and cur.close > e50 and body >= .6 and 55 <= mom <= 80:
            score = 65 + (10 if e50 > e200 else 0) + (10 if width > 1.2*a else 0) + (10 if spread < .05*a else 0) + (5 if cur.close > cur.open else 0)
            stop = cur.close-1.5*a
            candidates.append(Signal("BUY", "MOMENTUM_BREAKOUT", min(score, 100), "Breakout bullish", a, stop, cur.close+2*(cur.close-stop)))
        if cur.close < bottom and cur.close < e50 and body >= .6 and 20 <= mom <= 45:
            score = 65 + (10 if e50 < e200 else 0) + (10 if width > 1.2*a else 0) + (10 if spread < .05*a else 0) + (5 if cur.close < cur.open else 0)
            stop = cur.close+1.5*a
            candidates.append(Signal("SELL", "MOMENTUM_BREAKOUT", min(score, 100), "Breakout bearish", a, stop, cur.close-2*(stop-cur.close)))
    selected = max(candidates, key=lambda s: s.score, default=None)
    if selected is None:
        return Signal("WAIT", "NONE", 0, "Tidak ada setup valid", a)
    if selected.score < min_score:
        return Signal("WAIT", selected.strategy, selected.score, "Score di bawah ambang", a)
    return selected
