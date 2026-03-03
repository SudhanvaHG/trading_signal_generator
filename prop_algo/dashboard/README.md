# PropAlgo Trading Dashboard

Production-grade algorithmic trading dashboard built on the PropAlgo signal engine.

## Features

| Feature | Details |
|---|---|
| **Live Signal Feed** | Real-time signals via WebSocket, auto-refresh every 60s |
| **Backtest Engine** | Full historical simulation with equity curve, trade log |
| **Telegram Alerts** | Bot sends signals & risk alerts instantly |
| **Email Alerts** | HTML-formatted signals via any SMTP provider |
| **SMS Alerts** | Twilio-powered SMS for critical signals |
| **Risk Dashboard** | Live risk rule enforcement display |
| **Strategy Breakdown** | Per-strategy and per-asset analytics |
| **Dark UI** | Professional trading terminal aesthetic |

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- The `prop_algo` source folder must be at `../prop_algo` relative to `dashboard/`

### 1. Configure environment

```bash
cd dashboard
cp .env.example .env
# Edit .env with your notification credentials
```

### 2. Start (Linux/Mac)

```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

### 2. Start (Windows)

```bat
scripts\start.bat
```

### 3. Open dashboard

| Service | URL |
|---|---|
| Dashboard | http://localhost:80 |
| API Docs (Swagger) | http://localhost:80/api/docs |
| API Docs (ReDoc) | http://localhost:80/api/redoc |
| WebSocket | ws://localhost:80/ws |

## Notification Setup

### Telegram
1. Create bot via `@BotFather` → get **Bot Token**
2. Get your **Chat ID** via `@userinfobot`
3. Set in `.env`:
   ```
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

### Email (Gmail)
1. Enable 2FA on your Google account
2. Create an **App Password** at https://myaccount.google.com/apppasswords
3. Set in `.env`:
   ```
   EMAIL_ENABLED=true
   SMTP_USERNAME=you@gmail.com
   SMTP_PASSWORD=your_app_password
   EMAIL_RECIPIENTS=["you@gmail.com"]
   ```

### SMS (Twilio)
1. Create a Twilio account at https://twilio.com
2. Get a phone number (free trial available)
3. Set in `.env`:
   ```
   SMS_ENABLED=true
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_token
   TWILIO_FROM_NUMBER=+1xxxxxxxxxx
   SMS_RECIPIENTS=["+1xxxxxxxxxx"]
   ```

## Architecture

```
┌─────────────┐    ┌──────────────────────────────────────────┐
│   Browser   │────│              Nginx :80                   │
└─────────────┘    └────────┬────────────────────┬────────────┘
                            │                    │
                   ┌────────▼──────┐    ┌────────▼──────┐
                   │  Next.js :3000│    │  FastAPI :8000│
                   │  (Frontend)   │    │  (Backend)    │
                   └───────────────┘    └────────┬──────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │    PropAlgo Engine       │
                                    │  (Signal + Backtest)    │
                                    └────────────┬────────────┘
                                                 │
                                    ┌────────────▼────────────┐
                                    │    Redis + SQLite        │
                                    └─────────────────────────┘
```

## Docker Services

| Service | Image | Port (internal) |
|---|---|---|
| nginx | nginx:1.27-alpine | 80 |
| frontend | node:20-alpine | 3000 |
| backend | python:3.11-slim | 8000 |
| redis | redis:7-alpine | 6379 |

## Useful Commands

```bash
# View logs
docker compose logs -f
docker compose logs -f backend

# Restart a service
docker compose restart backend

# Stop everything
./scripts/stop.sh

# Rebuild after code changes
docker compose up -d --build

# Access backend shell
docker compose exec backend bash
```

## Pages

| Page | Path | Description |
|---|---|---|
| Dashboard | `/` | Overview — signals, KPIs, equity curve |
| Live Signals | `/signals` | Full signal feed with filters |
| Backtest | `/backtest` | Run historical simulation |
| Notifications | `/notifications` | Configure & test alert channels |
| Settings | `/settings` | System config & parameters |
