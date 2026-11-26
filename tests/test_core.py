import math
import tempfile
from pathlib import Path
import pytest
from app.core import Engine, Store, Signal, SPECS, validate_config
from app.strategy import Candle, ema, rsi, atr, decide


def engine():
    t=tempfile.TemporaryDirectory()
    e=Engine(Store(Path(t.name)/'db.sqlite'), seed=123)
    return t,e


def test_indicators():
    v=list(range(1,211))
    assert 190 < ema(v,21) < 210
    assert rsi([float(x) for x in v]) == 100.
    c=[Candle(x,x+1,x-1,x) for x in v]
    assert atr(c)>0
    assert decide(c, .01).side in {'BUY','SELL','WAIT'}
    assert decide(c[:12], .1).side=='WAIT'


def test_config_safety():
    assert validate_config({})['max_positions']==1
    with pytest.raises(ValueError): validate_config({'risk_pct':10})
    with pytest.raises(ValueError): validate_config({'manual_lot':float('nan')})
    with pytest.raises(ValueError): validate_config({'max_positions':99})
    with pytest.raises(ValueError): validate_config({'direction':'HACK'})


def test_real_account_hard_locked():
    t,e=engine()
    try:
        e.switch('real_usd')
        assert e.snapshot()['balance'] is None
        with pytest.raises(ValueError,match='REAL'): e.start()
        e.switch('real_cent')
        assert e.snapshot()['equity'] is None
    finally:t.cleanup()


def test_account_switch_guard():
    t,e=engine()
    try:
        e.start()
        with pytest.raises(ValueError):e.switch('real_usd')
        e.stop();e.switch('real_usd')
        e.configure({'manual_lot':.04})
        e.switch('demo')
        assert e.snapshot()['config']['manual_lot']==.01
        e.switch('real_usd')
        assert e.snapshot()['config']['manual_lot']==.04
    finally:t.cleanup()


def test_lot_is_bounded_by_risk():
    t,e=engine()
    try:
        e.configure({'manual_lot':3.,'lot_mode':'MANUAL'})
        e.start()
        p=e.prices['XAUUSD']
        s=Signal('BUY','TEST',100,'test',1,p-2,p+3)
        e._open(s,e.store.config('demo'),'XAUUSD')
        assert len(e.positions)==0
        e.stop();e.configure({'manual_lot':.01})
        e.start();e._open(s,e.store.config('demo'),'XAUUSD')
        assert len(e.positions)==1
        with pytest.raises(ValueError):e.switch('real_cent')
        e.emergency()
        assert len(e.positions)==0
        assert len(e.store.history('demo'))==1
    finally:t.cleanup()


def test_broker_execution_is_absent():
    from app.main import app
    assert not any('live' in route.path or 'order' in route.path for route in app.routes)
