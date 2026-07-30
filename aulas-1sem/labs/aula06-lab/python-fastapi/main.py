# main.py (FastAPI)
from fastapi import FastAPI
app = FastAPI()

class LegacyTrackingAPI:
    def get_status(self, code: str) -> str:
        return "ENTREGUE_LEGADO"

class TrackingAdapter:
    def __init__(self, legacy: LegacyTrackingAPI):
        self.legacy = legacy
    def track(self, code: str) -> dict:
        status = self.legacy.get_status(code)
        return {"code": code, "status": status.lower(), "modern": True}

@app.get("/track/{code}")
def track_order(code: str):
    adapter = TrackingAdapter(LegacyTrackingAPI())
    return adapter.track(code)
