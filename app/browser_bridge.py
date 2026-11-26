"""Read-only DOM observations; not proof of authentication or executable quotes."""
import secrets
import time
from threading import Lock
from pydantic import BaseModel, Field

class Heartbeat(BaseModel):
    account_hint: str = Field(default="",max_length=80)
    balance_text: str = Field(default="",max_length=80)
    account_visible: bool = False

class Bridge:
    def __init__(self):
        self.key = secrets.token_urlsafe(32)
        self.lock = Lock()
        self.last = 0.0
        self.data = {}
    def accept(self,key,body):
        if not secrets.compare_digest(key,self.key):
            return False
        with self.lock:
            self.last = time.monotonic()
            self.data = body.model_dump()
        return True
    def status(self):
        with self.lock:
            fresh = self.last > 0 and time.monotonic()-self.last < 15
            return {"fresh":fresh,"observation":self.data if fresh else {},
                    "authentication":"UNVERIFIED","market_feed":"NOT_IMPLEMENTED",
                    "broker_orders":"DISABLED"}
