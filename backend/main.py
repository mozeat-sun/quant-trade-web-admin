"""World Model — Web Dashboard Backend (FastAPI)."""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from prometheus_client import Counter, Gauge, Histogram, generate_latest
import asyncpg
import uvicorn

app = FastAPI(title="World Model Dashboard", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Config ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB = os.getenv("POSTGRES_DB", "world_model")
PG_USER = os.getenv("POSTGRES_USER", "wm_user")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

# --- Prometheus metrics ---
REQUEST_COUNT = Counter("wm_requests_total", "Total requests", ["endpoint"])
EQUITY_GAUGE = Gauge("wm_equity", "Current equity")
SHARPE_GAUGE = Gauge("wm_sharpe_60d", "Rolling 60-day Sharpe")
MAXDD_GAUGE = Gauge("wm_maxdd", "Max drawdown")
TRADE_COUNT = Counter("wm_trades_total", "Total trades")
RISK_EVENTS = Counter("wm_risk_events_total", "Risk events", ["rule"])

# --- Redis connection ---
redis_conn: Optional[redis.Redis] = None
pg_pool: Optional[asyncpg.Pool] = None


@app.on_event("startup")
async def startup():
    global redis_conn, pg_pool
    try:
        redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        await redis_conn.ping()
        print("Redis connected")
    except Exception as e:
        print(f"Redis unavailable: {e}")
    try:
        pg_pool = await asyncpg.create_pool(
            host=PG_HOST, port=PG_PORT, database=PG_DB, user=PG_USER, password=PG_PASSWORD,
            min_size=1, max_size=4
        )
        print("PostgreSQL connected")
    except Exception as e:
        print(f"PostgreSQL unavailable: {e}")


@app.on_event("shutdown")
async def shutdown():
    if redis_conn: await redis_conn.close()
    if pg_pool: await pg_pool.close()


# ==================== REST API ====================

@app.get("/api/v1/portfolio")
async def get_portfolio():
    """Current portfolio state."""
    REQUEST_COUNT.labels(endpoint="portfolio").inc()
    if redis_conn:
        data = await redis_conn.hgetall("wm:portfolio")
        if data:
            return {"status": "ok", "data": data}
    return {"status": "ok", "data": _mock_portfolio()}


@app.get("/api/v1/performance")
async def get_performance():
    """Strategy performance metrics."""
    REQUEST_COUNT.labels(endpoint="performance").inc()
    metrics = {
        "sharpe_60d": 1.85, "sortino_60d": 2.12, "maxdd": 0.12,
        "calmar": 1.52, "annual_return": 0.23, "win_rate": 0.58,
        "avg_turnover": 0.18, "equity": 1_234_567.89,
        "timestamp": datetime.now().isoformat(),
    }
    if redis_conn:
        cached = await redis_conn.hgetall("wm:performance")
        if cached: metrics.update({k: float(v) for k, v in cached.items()})
    EQUITY_GAUGE.set(metrics["equity"])
    SHARPE_GAUGE.set(metrics["sharpe_60d"])
    MAXDD_GAUGE.set(metrics["maxdd"])
    return {"status": "ok", "data": metrics}


@app.get("/api/v1/equity_curve")
async def get_equity_curve(days: int = 90):
    """Historical equity curve."""
    REQUEST_COUNT.labels(endpoint="equity_curve").inc()
    if pg_pool:
        async with pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT date, equity FROM equity_curve ORDER BY date DESC LIMIT $1", days
            )
            return {"status": "ok", "data": [{"date": str(r[0]), "equity": float(r[1])} for r in rows]}
    return {"status": "ok", "data": _mock_equity_curve(days)}


@app.get("/api/v1/trades")
async def get_trades(limit: int = 50):
    """Recent trades."""
    REQUEST_COUNT.labels(endpoint="trades").inc()
    return {"status": "ok", "data": _mock_trades(limit)}


@app.get("/api/v1/risk_events")
async def get_risk_events(limit: int = 20):
    """Recent risk events."""
    REQUEST_COUNT.labels(endpoint="risk_events").inc()
    if redis_conn:
        events = await redis_conn.lrange("wm:risk_events", 0, limit - 1)
        return {"status": "ok", "data": [json.loads(e) for e in events]}
    return {"status": "ok", "data": _mock_risk_events(limit)}


@app.get("/api/v1/model_status")
async def get_model_status():
    """Model health metrics."""
    REQUEST_COUNT.labels(endpoint="model_status").inc()
    return {"status": "ok", "data": {
        "z_t_norm": 1.23, "rollout_stability": 0.95,
        "last_training": "2026-06-20T10:00:00",
        "weight_version": "v1.2.3", "validity_score": 1.0,
    }}


@app.get("/api/v1/system_health")
async def get_system_health():
    """System health status."""
    REQUEST_COUNT.labels(endpoint="system_health").inc()
    import psutil
    return {"status": "ok", "data": {
        "cpu_pct": psutil.cpu_percent(),
        "memory_pct": psutil.virtual_memory().percent,
        "disk_pct": psutil.disk_usage("/").percent,
        "redis": "connected" if redis_conn else "disconnected",
        "postgres": "connected" if pg_pool else "disconnected",
        "timestamp": datetime.now().isoformat(),
    }}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return HTMLResponse(generate_latest(), media_type="text/plain")


# ==================== WebSocket ====================

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, msg: dict):
        for ws in self.active:
            try:
                await ws.send_json(msg)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(ws)


async def broadcast_loop():
    """Periodically push latest metrics to all WebSocket clients."""
    while True:
        await asyncio.sleep(5)
        if manager.active:
            perf = await get_performance()
            await manager.broadcast({"type": "performance", "data": perf["data"]})


@app.on_event("startup")
async def start_broadcast():
    asyncio.create_task(broadcast_loop())


# ==================== Mock Data ====================

def _mock_portfolio() -> dict:
    return {
        "cash": 234_567.89, "equity": 1_234_567.89,
        "positions": [
            {"symbol": "AAPL", "weight": 0.08, "pnl_pct": 0.12},
            {"symbol": "MSFT", "weight": 0.07, "pnl_pct": 0.08},
            {"symbol": "NVDA", "weight": 0.06, "pnl_pct": 0.25},
            {"symbol": "GOOGL", "weight": 0.05, "pnl_pct": -0.03},
            {"symbol": "AMZN", "weight": 0.05, "pnl_pct": 0.15},
        ]
    }


def _mock_equity_curve(days: int) -> list:
    import random
    eq = 1_000_000
    curve = []
    for d in range(days, 0, -1):
        eq *= 1.0 + random.gauss(0.0008, 0.012)
        curve.append({"date": f"2026-{(d//30)%12+1:02d}-{d%28+1:02d}", "equity": round(eq, 2)})
    return curve


def _mock_trades(limit: int) -> list:
    return [
        {"date": "2026-06-26", "symbol": "AAPL", "side": "BUY", "quantity": 100, "price": 195.30, "notional": 19530},
        {"date": "2026-06-26", "symbol": "MSFT", "side": "SELL", "quantity": 50, "price": 420.15, "notional": 21007},
    ][:limit]


def _mock_risk_events(limit: int) -> list:
    return [
        {"rule": "max_single_weight", "action": "REDUCE", "symbol": "NVDA", "severity": 0.5, "date": "2026-06-26"},
        {"rule": "stop_loss", "action": "LIQUIDATE", "symbol": "INTC", "severity": 0.8, "date": "2026-06-25"},
    ][:limit]


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
