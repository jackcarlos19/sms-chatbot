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
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
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
   - `pytest`
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
