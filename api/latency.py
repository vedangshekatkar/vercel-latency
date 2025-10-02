# api/latency.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from statistics import fmean
from pathlib import Path
import json, math

app = FastAPI()

# CORS: allow POST + OPTIONS (preflight) from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load telemetry at cold start, fail early if missing
DATA_PATH = Path(__file__).resolve().with_name("q-vercel-latency.json")
with DATA_PATH.open("r") as f:
    TELEMETRY = json.load(f)

class Payload(BaseModel):
    regions: list[str]
    threshold_ms: int

def p95(values: list[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    # 95th percentile index (ceil), zero-based, clamped
    k = max(0, min(len(s) - 1, math.ceil(0.95 * len(s)) - 1))
    return float(s[k])

@app.post("/")
async def latency(payload: Payload):
    result = {}
    for region in payload.regions:
        rows = [r for r in TELEMETRY if r.get("region") == region]
        if not rows:
            continue
        latencies = [float(r["latency_ms"]) for r in rows if "latency_ms" in r]
        uptimes   = [float(r["uptime"])     for r in rows if "uptime"     in r]
        result[region] = {
            "avg_latency": round(fmean(latencies), 2),
            "p95_latency": p95(latencies),
            "avg_uptime": round(fmean(uptimes), 4) if uptimes else None,
            "breaches": int(sum(1 for x in latencies if x > payload.threshold_ms)),
        }
    return result
