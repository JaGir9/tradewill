"""Observed M1 candles, never synthetic. Advisory signals only."""
from collections import deque
from time import time
from .strategy import Candle, decide

class DemoFeed:
    def __init__(self):
        self.symbol = ""
        self.bars = deque(maxlen=500)
        self.current = None
        self.minute = None
        self.last = 0
    def update(self, d):
        if "demo" not in d.account_hint.lower().split() or d.login_form or not d.trading_ui or not d.symbol or not d.bid or not d.ask or d.ask < d.bid:
            self.__init__()
            return
        now = time()
        minute = int(now // 60)
        if self.symbol != d.symbol or (self.last and now-self.last > 15):
            self.__init__()
        self.symbol = d.symbol
        self.last = now
        p = (d.bid+d.ask)/2
        if self.minute != minute:
            if self.current and minute == self.minute+1:
                self.bars.append(Candle(*self.current, timestamp=str(self.minute*60)))
            elif self.current:
                self.bars.clear()
            self.minute = minute
            self.current = [p,p,p,p]
        else:
            self.current[1] = max(self.current[1],p)
            self.current[2] = min(self.current[2],p)
            self.current[3] = p
        self.spread = d.ask-d.bid
    def status(self):
        fresh = bool(self.last and time()-self.last < 10)
        s = decide(list(self.bars),self.spread) if fresh else None
        return {"fresh":fresh,"symbol":self.symbol,"closed_candles":len(self.bars),"required":210,"signal":s.__dict__ if s else None,"execution":"MANUAL_ONLY"}
