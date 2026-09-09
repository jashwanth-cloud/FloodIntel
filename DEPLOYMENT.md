# FloodIntel Deployment Guide

## Frontend
- **Command:** `npm run build` then `npm start`
- **Environment:** `NEXT_PUBLIC_API_URL` (Required, URL of backend domain)

## Backend
- **Command:** `gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app.main:app`
- **Environment:**
    - `ALLOWED_ORIGINS` (Required, comma-separated allowed frontend domains)
    - `OLLAMA_API_BASE_URL` (Required for Grounded AI)
    - `OLLAMA_MODEL` (Optional, defaults to qwen2.5)

## Health Check
- `GET /health`
