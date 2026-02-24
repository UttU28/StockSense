# StockSense Frontend Backend

Python proxy used by the frontend. **All trade/stock API requests are forwarded to https://rakeshent.info/** — no local stock code runs here.

## Run

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Runs on **http://localhost:5000** by default. Override with `PORT=3000 python app.py` or set `STOCK_GITA_BACKEND_URL` to point to another StockSense API (default: `https://rakeshent.info`).

## Flow

- **Frontend** → this server (e.g. `/v1/chat/completions`, `/api/ticker/batch/...`, `/chart_v2`, `/chart_img`)
- **This server** → `https://rakeshent.info/` (same path and query)
- Responses are streamed back to the frontend

## Endpoints

- `GET /health` — local health check; returns `{"status":"ok","proxy_target":"https://rakeshent.info"}`.
- All other paths are proxied to rakeshent.info.
