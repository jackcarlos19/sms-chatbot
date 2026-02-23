# SMS Chatbot

Production-oriented SMS appointment chatbot built with FastAPI, PostgreSQL, Redis, and Twilio.

## Overview

This service handles:

- inbound SMS processing through Twilio webhooks
- AI-assisted intent detection and response generation
- concurrency-safe scheduling (book/cancel/reschedule)
- campaign-style outbound batch messaging with quiet-hours support
- conversation state orchestration with timeout recovery

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                      EXTERNAL LAYER                          │
│  [Contact Phone] ←→ [Twilio] ←→ [ngrok (dev) / LB (prod)]   │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                     API LAYER (FastAPI)                      │
│                                                              │
│  /webhooks/sms/inbound  — Receive SMS (returns 200 quickly) │
│  /webhooks/sms/status   — Delivery status callbacks          │
│  /api/campaigns         — Campaign CRUD + launch             │
│  /api/appointments      — Appointment lookups                │
│  /api/contacts          — Contact management                 │
│  /api/health            — Health check (DB + Redis)          │
└──────┬──────────┬──────────┬─────────────────────────────────┘
       │          │          │
┌──────▼──┐ ┌────▼─────┐ ┌──▼──────────────┐
│ SMS     │ │ AI/LLM   │ │ Scheduling      │
│ Service │ │ Service  │ │ Engine          │
│         │ │          │ │                 │
│ • Send  │ │ • Intent │ │ • Availability  │
│ • Retry │ │ • Extract│ │ • Book (locked) │
│ • Log   │ │ • Parse  │ │ • Cancel        │
│ • Comply│ │ • Respond│ │ • Reschedule    │
└────┬────┘ └────┬─────┘ └──┬──────────────┘
     │           │           │
┌────▼───────────▼───────────▼─────────────────┐
│               DATA LAYER                      │
│  [PostgreSQL]          [Redis]                │
│  • Contacts            • Idempotency keys     │
│  • Messages            • Rate limits          │
│  • Appointments        • arq task queue       │
│  • Availability        • Conversation cache   │
│  • Campaigns                                  │
│  • Conversation State                         │
└───────────────────────────────────────────────┘
```

## Local Setup

### Requirements

- Python 3.11+
- Docker + Docker Compose
- Twilio account for SMS integration
- OpenRouter API key for AI routing

### 1) Configure environment

```bash
cp .env.example .env
```

Populate at least:

- `DATABASE_URL`
- `REDIS_URL`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`
- `OPENROUTER_API_KEY`
- `ADMIN_API_KEY`

### 2) Start dependencies and app

```bash
docker compose up -d
docker compose exec app alembic upgrade head
```

### 3) Verify health

```bash
curl http://localhost:8000/api/health
```

Expected:

```json
{"status":"green","db":"ok","redis":"ok"}
```

## Database and Migrations

Run migrations (inside app container or local venv):

```bash
alembic upgrade head
```

Seed availability:

```bash
python scripts/seed_availability.py
```

## Development Workflow

1. Branch from `develop` for each phase/feature.
2. Implement in small, conventional commits.
3. Run quality checks:
   - `ruff check .`
   - `black .`
   - `pytest tests/ -x -q`
4. Merge feature to `develop`, tag release milestone.
5. Periodically merge `develop` to `main` for production-ready snapshots.

## Admin API Security

Admin endpoints require `X-API-Key` matching `ADMIN_API_KEY`.

Examples:

- `GET /api/contacts`
- `GET /api/campaigns`
- `POST /api/campaigns`
- `PATCH /api/campaigns/{campaign_id}`
- `GET /api/appointments?contact_id=<uuid>`
- `GET /api/messages?contact_id=<uuid>`

## Notes

- Webhooks validate Twilio signatures before processing.
- Logs are structured JSON and mask phone numbers.
- Scheduling uses transactional row locks to avoid double booking.
- Campaign workers re-check opt-in status immediately before send.

## Admin Dashboard

Access the admin dashboard at `/admin` after starting the application.

### Features
- **Dashboard** — Live stats, upcoming appointments, active conversations
- **Contacts** — Browse all contacts, view conversation history, appointments
- **Appointments** — All appointments with status filtering
- **Conversations** — Real-time conversation state monitor
- **Campaigns** — Create, schedule, and manage SMS campaigns
- **Simulator** — Test the SMS chatbot without a phone number
- **Slots** — View weekly appointment availability

### Development
```bash
# Start the backend
docker compose up -d

# Start the admin dev server (hot reload, API proxied to :8000)
cd admin
npm install
npm run dev
# Open http://localhost:5173/admin
```

### Production
The admin frontend is automatically built into the Docker image via multi-stage build. Access at `http://your-host/admin`.

### Authentication
Use `ADMIN_USERNAME` and `ADMIN_PASSWORD` to sign in via `POST /api/admin/auth/login`.

## Production Deployment (VPS + Permanent Domain)

This project supports a VPS deployment pattern with Caddy TLS termination and Docker Compose.

### 1) DNS
- Point your domain `A` record to your VPS public IP.
- Optional: point `www` to the same IP.

### 2) Server prerequisites
- Ubuntu 22.04+ (or similar)
- Docker Engine + Docker Compose plugin
- Firewall allowing only `22`, `80`, and `443`

### 3) Production environment
Set these values in `.env` on the server:
- `DOMAIN`
- `ADMIN_API_KEY`
- `ADMIN_SESSION_SECRET`
- `OPENROUTER_API_KEY` and/or `VERCEL_AI_GATEWAY_API_KEY`
- `AI_PROVIDER` (`openrouter` or `vercel_gateway`)

### 4) Start production stack
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 5) Run deploy helper
```bash
export DOMAIN=yourdomain.com
./scripts/deploy_prod.sh
./scripts/healthcheck_prod.sh
```

### 6) Verify
- `https://yourdomain.com/api/health`
- `https://yourdomain.com/admin`
- `DOMAIN=yourdomain.com docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

## Admin Auth (Server Session)

Admin access now uses a server-side session cookie:
- Login endpoint: `POST /api/admin/auth/login`
- Logout endpoint: `POST /api/admin/auth/logout`
- Session check: `GET /api/admin/auth/me`

The backend still accepts `X-API-Key` for compatibility, but web UI auth should use session login.

## Twilio Webhook Setup (Dev)

Use ngrok to expose your local app to Twilio while developing:

```bash
docker compose up -d ngrok
```

Then set your Twilio webhook URL to:

- `https://<your-ngrok-domain>/webhooks/sms/inbound`
- Status callback: `https://<your-ngrok-domain>/webhooks/sms/status`
