# quant-trade-web-admin

Lightweight web administration panel for the World Model trading system. Provides account management, strategy configuration, backtest reports, and system monitoring through a Vue 3 SPA with a FastAPI backend.

## Architecture

```
quant-trade-web-admin/
├── backend/               # FastAPI (Python)
│   ├── main.py            # Application entry point
│   ├── api/               # Route modules (portfolio, performance, trades, risk, health)
│   ├── services/          # Redis client, PostgreSQL client
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              # Vue 3 + Vite
│   ├── src/
│   │   ├── views/         # Dashboard, Trades, RiskEvents, ModelStatus
│   │   └── router/        # Vue Router config
│   ├── package.json
│   └── Dockerfile
├── nginx/                 # Reverse proxy config
├── prometheus/            # Prometheus scrape config
└── docker-compose.yml     # Standalone deployment
```

## Quick Start

```bash
# Start all services
docker-compose up --build -d

# Check health
curl http://localhost/api/v1/health

# Open web UI
open http://localhost
```

## Services

| Service    | Port  | Description |
|------------|-------|-------------|
| postgres   | 5432  | Persistent storage for trade history, account data |
| redis      | 6379  | Real-time metrics pub/sub, caching |
| backend    | —     | FastAPI REST + WebSocket server |
| nginx      | 80    | Reverse proxy (frontend static + API proxy) |
| prometheus | 9090  | Metrics collection (monitoring profile) |
| grafana    | 3000  | Dashboards (monitoring profile) |

## Relationship to Other Repos

- `world-model-spec` (submodule) — gRPC proto definitions, constants
- Shared backend services with [qt-trade-terminal](https://github.com/...) — same auth, same data

This is the **lightweight management companion** to the Qt desktop terminal:
- **Qt**: Real-time trading, order entry, position monitoring (high-performance)
- **Web**: Account management, strategy config, backtest reports, system health
