# api/latency.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from statistics import fmean
from pathlib import Path
import json, math

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

DATA_PATH = Path(__file__).with_name("q-vercel-latency.json")
DATA = json.loads(DATA_PATH.read_text())

class Payload(BaseModel):
    regions: list[str]
    threshold_ms: int

def p95(values):
    if not values:
        return None
    s = sorted(values)
    k = max(0, min(len(s)-1, math.ceil(0.95*len(s)) - 1))
    return float(s[k])

@app.post("/")
def latency(payload: Payload):
    out = {}
    for region in payload.regions:
        rows = [r for r in DATA if r.get("region") == region]

        latencies = [float(r["latency_ms"]) for r in rows if "latency_ms" in r]
        uptimes   = [float(r["uptime"])     for r in rows if "uptime"     in r]
        if not latencies:
            continue

        out[region] = {
            "avg_latency": round(fmean(latencies), 2),
            "p95_latency": p95(latencies),
            "avg_uptime": round(fmean(uptimes), 4) if uptimes else None,
            "breaches": int(sum(1 for x in latencies if x > payload.threshold_ms)),
        }
    return out
