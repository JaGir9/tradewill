from types import SimpleNamespace
from app.demo_auto import DemoAuto
from app.core import DEFAULT_CONFIG
from app.strategy import Candle

class FakeBridge:
    def __init__(self, fresh=True, account="demo"):
        self.fresh=fresh
        self.account=account
    def status(self):
        return {"fresh":self.fresh,"observation":{"domain":"tradewill.id","account_marker":True,
            "login_form":False,"trading_ui":True,"account_hint":self.account,"bid":100.0,"ask":100.01}}

class FakeFeed:
    def __init__(self):
        self.bars=[Candle(100,101,99,100,str(i*60)) for i in range(210)]
    def status(self):
        return {"fresh":True,"closed_candles":len(self.bars),"symbol":"XAUUSD"}

def test_demo_always_blocks_unverified_identity():
    e=DemoAuto()
    e.enable(True)
    r=e.evaluate(FakeFeed(),FakeBridge(),DEFAULT_CONFIG)
    assert r["status"]=="BLOCKED"
    assert "broker demo identity not authenticated" in r["reasons"]
    assert e.status()["broker_execution"]=="DISABLED"

def test_rejects_real_or_stale():
    e=DemoAuto()
    e.enable(True)
    r=e.evaluate(FakeFeed(),FakeBridge(account="real"),DEFAULT_CONFIG)
    assert "demo account not observed" in r["reasons"]
    assert "broker demo identity not authenticated" in r["reasons"]
    r=e.evaluate(FakeFeed(),FakeBridge(fresh=False),DEFAULT_CONFIG)
    assert "stale bridge" in r["reasons"]

def test_disabled_by_default():
    e=DemoAuto()
    assert e.status()["enabled"] is False
    assert e.evaluate(FakeFeed(),FakeBridge(),DEFAULT_CONFIG)["status"]=="BLOCKED"
