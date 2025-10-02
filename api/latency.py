from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
import numpy as np

app = FastAPI()

# Allow CORS for POST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

@app.post("/")
async def latency(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 200)

    # Load telemetry data from q-vercel-latency.json
    data_path = Path(__file__).with_name("q-vercel-latency.json")
    with open(data_path) as f:
        telemetry = json.load(f)

    result = {}
    for region in regions:
        values = [r for r in telemetry if r["region"] == region]
        if not values:
            continue
        latencies = [r["latency_ms"] for r in values]
        uptimes = [r["uptime"] for r in values]
        breaches = sum(1 for l in latencies if l > threshold_ms)

        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": breaches,
        }

    return result
