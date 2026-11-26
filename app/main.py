"""Local-only API. No TradeWill order endpoints are used in this release."""
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
import os
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .core import Engine, Store, ACCOUNTS
from .demo_auto import DemoAuto

BASE = Path(__file__).resolve().parent
store = Store()
engine = Engine(store)

async def market_loop():
    while True:
        try:
            await asyncio.to_thread(engine.tick)
            if not ACCOUNTS[engine.account]["paper"] and engine.status == "RUNNING" and not bridge.status()["fresh"]:
                await asyncio.to_thread(engine.pause)
        except Exception:
            # Never leave an order-generating process running after an internal error.
            engine.stop()
        await asyncio.sleep(1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(market_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="Universal Quant Engine - PAPER ONLY", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

class AccountChoice(BaseModel):
    account: str

class ConfigPatch(BaseModel):
    config: dict

@app.middleware("http")
async def restrict_origin(request: Request, call_next):
    # Binding server to 127.0.0.1 is mandatory; prevent common DNS rebinding.
    host = request.url.hostname
    if host not in {"127.0.0.1", "localhost", "testserver"}:
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail":"localhost only"}, status_code=403)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin:
            from urllib.parse import urlparse
            u = urlparse(origin)
            if u.hostname not in {"127.0.0.1", "localhost"} and not (request.url.path == "/api/bridge/heartbeat" and u.scheme == "chrome-extension"):
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail":"invalid origin"},status_code=403)
    return await call_next(request)

@app.get("/")
async def index():
    return FileResponse(BASE / "static" / "index.html")

@app.get("/api/state")
async def state():
    return await asyncio.to_thread(engine.snapshot)

@app.post("/api/account")
async def account(body: AccountChoice):
    try:
        await asyncio.to_thread(engine.switch, body.account)
        return await state()
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.post("/api/config")
async def config(body: ConfigPatch):
    try:
        return {"config": await asyncio.to_thread(engine.configure, body.config)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@app.post("/api/control/{action}")
async def control(action: str):
    commands = {"start": engine.start, "pause": engine.pause, "stop": engine.stop, "emergency": engine.emergency}
    if action not in commands:
        raise HTTPException(404, "Perintah tidak dikenal")
    try:
        if action == "start" and not ACCOUNTS[engine.account]["paper"] and not bridge.status()["fresh"]:
            raise ValueError("Browser bridge disconnected; connect TradeWill first")
        await asyncio.to_thread(commands[action])
        return await state()
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc

@app.get("/api/history")
async def history():
    return await asyncio.to_thread(store.history, engine.account)

@app.get("/api/broker/status")
async def broker_status():
    return {"connected":bridge.status()["fresh"],"login":"UNVERIFIED","account_switch":"NOT_IMPLEMENTED","live_trading":"DISABLED",
            "reason":"TradeWill browser account switching/order execution requires authorized integration and verified selectors"}

@app.websocket("/ws")
async def websocket(ws: WebSocket):
    origin = ws.headers.get("origin")
    if origin:
        from urllib.parse import urlparse
        if urlparse(origin).hostname not in {"127.0.0.1", "localhost"}:
            await ws.close(code=1008)
            return
    await ws.accept()
    try:
        while True:
            await ws.send_json(await asyncio.to_thread(engine.snapshot))
            await asyncio.sleep(1.0)
    except (WebSocketDisconnect, RuntimeError):
        pass

class ExternalQuote(BaseModel):
    symbol: str
    bid: float
    ask: float
    timestamp: float
    bars: list[dict]

class VirtualBalance(BaseModel):
    amount: float

@app.post("/api/feed")
async def feed(body: ExternalQuote):
    try:
        await asyncio.to_thread(engine.ingest,body.symbol,body.bid,body.ask,body.timestamp,body.bars)
        return {"accepted":True}
    except (ValueError,KeyError,TypeError) as exc:
        raise HTTPException(422,str(exc)) from exc

@app.post("/api/virtual-balance")
async def virtual_balance(body: VirtualBalance):
    try:
        await asyncio.to_thread(engine.set_virtual_balance,body.amount)
        return await state()
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


from .browser_bridge import Bridge, Heartbeat
bridge = Bridge()
from .demo_feed import DemoFeed
demo_feed = DemoFeed()
demo_auto = DemoAuto()

@app.get("/api/bridge/pair")
async def bridge_pair(request: Request):
    if request.headers.get("sec-fetch-site") not in ("same-origin", "none"):
        raise HTTPException(403,"Open local dashboard directly")
    return {"key":bridge.key}

@app.post("/api/bridge/heartbeat")
async def bridge_heartbeat(body: Heartbeat, request: Request):
    if not bridge.accept(request.headers.get("x-bridge-key",""),body):
        raise HTTPException(403,"Pairing required")
    demo_feed.update(body)
    return {"accepted":True}

@app.get("/api/bridge/status")
async def bridge_status():
    return {**bridge.status(), "demo_strategy": demo_feed.status()}

class DemoAutoControl(BaseModel):
    enabled: bool

@app.post("/api/demo-auto/control")
async def demo_auto_control(body: DemoAutoControl):
    demo_auto.enable(body.enabled)
    return demo_auto.status()

@app.get("/api/demo-auto/status")
async def demo_auto_status():
    status = await asyncio.to_thread(demo_auto.evaluate, demo_feed, bridge, store.config("broker_demo"))
    return {**demo_auto.status(), "evaluation":status}
