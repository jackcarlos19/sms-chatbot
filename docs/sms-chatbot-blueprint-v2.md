# SMS Appointment Chatbot — MVP Blueprint v2

## Changelog from v1

> **21 issues identified and fixed.** Key changes:
>
> **Critical Bugs Fixed:**
> 1. ~~Messages table forward-references campaigns table~~ → Reordered SQL; campaigns defined first
> 2. ~~EXCLUDE constraint missing btree_gist extension~~ → Added `CREATE EXTENSION` + removed for MVP (overkill — FOR UPDATE + partial unique index is sufficient)
> 3. ~~EXCLUDE constraint breaks on NULL provider_id~~ → Removed EXCLUDE; defense-in-depth via row lock + partial index
> 4. ~~UNIQUE on appointments.slot_id blocks re-booking cancelled slots~~ → Changed to partial unique index `WHERE status IN ('confirmed', 'rescheduled')`
> 5. ~~Webhook processes AI inline → Twilio 15s timeout risk~~ → Webhook returns 200 immediately, processes via background task
> 6. ~~No webhook idempotency → Twilio retries cause duplicate processing~~ → Added MessageSid dedup check
> 7. ~~Celery overkill for MVP~~ → Replaced with `arq` (lightweight async Redis queue) for campaigns; FastAPI BackgroundTasks for webhook processing
>
> **Design Issues Fixed:**
> 8. Added ngrok for local Twilio development
> 9. Added conversation history management (last 10 messages, token cap)
> 10. ~~System prompt says "under 160 chars"~~ → Changed to "under 320 chars, max 480" (slot lists need space)
> 11. Added RESCHEDULE_SHOW_SLOTS intermediate state to state machine
> 12. ~~15min conversation timeout too short for SMS~~ → Changed to 2 hours
> 13. Added slot staleness check — re-verify at booking time with recovery flow
> 14. Moved `parse_slot_selection` to AIService where it belongs (NLU task)
> 15. Added configurable buffer_minutes between appointments
> 16. Added campaign template variable interpolation spec ({first_name}, etc.)
> 17. Added Twilio send retry logic (3 attempts, exponential backoff)
> 18. Added SQLAlchemy `onupdate=func.now()` for updated_at columns
>
> **Missing Elements Added:**
> 19. Full git workflow with branching strategy and per-phase commits
> 20. .gitignore, pyproject.toml, pre-commit hooks
> 21. Restructured Cursor prompts to include git commands

---

## Project Overview

A custom, production-ready SMS chatbot system that sends outbound messages to opted-in contacts, handles inbound replies with AI-powered natural language understanding, reads real-time availability from a SQL database, and books appointments with concurrency-safe logic. Fully self-hosted, no white-label platforms.

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Runtime** | Python 3.12+ | Async-first, rich ecosystem for SMS/AI |
| **Framework** | FastAPI | Native async, auto-docs, webhook handling |
| **Database** | PostgreSQL 16 | ACID transactions, row-level locking for booking |
| **ORM** | SQLAlchemy 2.0 (async) | Type-safe models, transaction management |
| **Migrations** | Alembic | Schema versioning |
| **SMS Provider** | Twilio | Industry standard, excellent webhook support |
| **AI/LLM** | Anthropic Claude API (claude-sonnet-4-20250514) | Structured output, intent detection, cost-effective |
| **Cache** | Redis | Rate limiting, idempotency keys, campaign queuing |
| **Task Queue** | arq (async Redis queue) | Lightweight async alternative to Celery; campaign batches + scheduled sends |
| **Tunnel (Dev)** | ngrok | Expose local webhook endpoint to Twilio during development |
| **Containerization** | Docker + Docker Compose | Reproducible dev/prod environments |
| **Testing** | pytest + pytest-asyncio | Async test support |
| **VCS** | Git | Version control with feature branch workflow |

**Why arq over Celery:** Celery adds significant operational overhead (separate worker process, flower for monitoring, complex config). `arq` is native async Python, uses Redis directly, and fits an MVP perfectly. We can migrate to Celery later if campaign volume demands it.

---

## Git Workflow

### Repository Setup (Phase 0)

```bash
# Initialize repo
git init sms-chatbot
cd sms-chatbot
git checkout -b main

# First commit: project skeleton
git add .
git commit -m "chore: initialize project skeleton"

# Create develop branch
git checkout -b develop
```

### Branching Strategy

```
main              ← Production-ready code only (tagged releases)
  └── develop     ← Integration branch
       ├── feature/phase-1-foundation
       ├── feature/phase-2-sms-integration
       ├── feature/phase-3-ai-layer
       ├── feature/phase-4-scheduling
       ├── feature/phase-5-conversation
       └── feature/phase-6-campaigns
```

### Per-Phase Git Flow

```bash
# Start each phase
git checkout develop
git pull
git checkout -b feature/phase-N-description

# Commit frequently with conventional commits
git add .
git commit -m "feat(sms): add Twilio webhook handler with signature validation"
git commit -m "feat(sms): implement STOP/START/HELP compliance"
git commit -m "test(sms): add webhook and compliance unit tests"

# Complete phase
git checkout develop
git merge feature/phase-N-description --no-ff
git tag -a vN.0.0 -m "Phase N complete: description"
git push origin develop --tags
```

### Commit Convention

```
feat(scope): description     — New feature
fix(scope): description      — Bug fix
test(scope): description     — Tests
refactor(scope): description — Code restructuring
docs: description            — Documentation
chore: description           — Build, deps, config
```

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
.venv/
venv/

# Environment
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp

# Docker
docker-compose.override.yml

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/

# Logs
*.log
logs/
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      EXTERNAL LAYER                           │
│  [Contact Phone] ←→ [Twilio] ←→ [ngrok (dev) / LB (prod)]  │
└─────────────────────────────┬────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────┐
│                     API LAYER (FastAPI)                        │
│                                                               │
│  /webhooks/sms/inbound  — Receive SMS (returns 200 immediately│
│                           then processes via BackgroundTask)   │
│  /webhooks/sms/status   — Delivery status callbacks           │
│  /api/campaigns         — Campaign CRUD + launch              │
│  /api/appointments      — Appointment CRUD                    │
│  /api/contacts          — Contact management                  │
│  /api/health            — Health check (DB + Redis)           │
└──────┬──────────┬──────────┬─────────────────────────────────┘
       │          │          │
┌──────▼──┐ ┌────▼─────┐ ┌──▼──────────────┐
│ SMS     │ │ AI/LLM   │ │ Scheduling      │
│ Service │ │ Service   │ │ Engine          │
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

**Key change from v1:** Webhook handler returns `200 OK` immediately after idempotency check, then dispatches processing to a FastAPI BackgroundTask. This prevents Twilio's 15-second timeout from causing retries during slow AI processing.

---

## Database Schema

### Prerequisites

```sql
-- Required for UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Note: btree_gist NOT needed for MVP.
-- We use SELECT FOR UPDATE + partial unique index instead of EXCLUDE constraints.
-- EXCLUDE constraints are elegant but add complexity and require btree_gist.
-- For MVP, our 2-layer defense (row lock + partial index) is equally safe and simpler.
```

### Core Tables

```sql
-- ============================================================
-- CAMPAIGNS (defined first — referenced by messages)
-- ============================================================
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    message_template TEXT NOT NULL,  -- Supports {first_name}, {business_name} vars
    status VARCHAR(20) DEFAULT 'draft',  -- draft, scheduled, active, paused, completed
    scheduled_at TIMESTAMPTZ,
    quiet_hours_start TIME DEFAULT '21:00',
    quiet_hours_end TIME DEFAULT '09:00',
    respect_timezone BOOLEAN DEFAULT TRUE,
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    delivered_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- CONTACTS
-- ============================================================
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,  -- E.164 format: +1234567890
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    opt_in_status VARCHAR(20) DEFAULT 'opted_in',  -- opted_in, opted_out, pending
    opt_in_date TIMESTAMPTZ,
    opt_out_date TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_contacts_phone ON contacts(phone_number);
CREATE INDEX idx_contacts_opt_in ON contacts(opt_in_status);

-- ============================================================
-- MESSAGES (references campaigns — now safe since campaigns defined first)
-- ============================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id UUID REFERENCES contacts(id),
    direction VARCHAR(10) NOT NULL,  -- inbound, outbound
    body TEXT NOT NULL,
    sms_sid VARCHAR(64) UNIQUE,  -- Twilio MessageSid — UNIQUE for idempotency lookups
    status VARCHAR(20) DEFAULT 'queued',  -- queued, sent, delivered, failed, received
    error_code VARCHAR(10),
    error_message TEXT,
    campaign_id UUID REFERENCES campaigns(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_contact ON messages(contact_id, created_at DESC);
CREATE INDEX idx_messages_sms_sid ON messages(sms_sid);  -- For idempotency + status lookups
CREATE INDEX idx_messages_campaign ON messages(campaign_id);

-- ============================================================
-- AVAILABILITY SLOTS
-- ============================================================
CREATE TABLE availability_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID,  -- Optional: if multiple service providers
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    buffer_minutes INTEGER DEFAULT 0,  -- Buffer after this slot (cleanup, travel, etc.)
    slot_type VARCHAR(50) DEFAULT 'standard',
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()

    -- NOTE: No EXCLUDE constraint. We use SELECT FOR UPDATE + partial unique index
    -- on appointments for double-booking prevention. Simpler, equally safe for MVP.
);

CREATE INDEX idx_availability_available ON availability_slots(start_time)
    WHERE is_available = TRUE;
CREATE INDEX idx_availability_provider ON availability_slots(provider_id, start_time)
    WHERE is_available = TRUE;

-- ============================================================
-- APPOINTMENTS
-- ============================================================
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id UUID REFERENCES contacts(id) NOT NULL,
    slot_id UUID REFERENCES availability_slots(id) NOT NULL,
    status VARCHAR(20) DEFAULT 'confirmed',  -- confirmed, cancelled, rescheduled, completed, no_show
    booked_at TIMESTAMPTZ DEFAULT NOW(),
    cancelled_at TIMESTAMPTZ,
    cancellation_reason TEXT,
    rescheduled_from_id UUID REFERENCES appointments(id),  -- Links to original appointment
    notes TEXT,
    version INTEGER DEFAULT 1,  -- Optimistic locking for concurrent updates
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- CRITICAL FIX: Partial unique index instead of plain UNIQUE.
-- Plain UNIQUE on slot_id would block re-booking a slot after cancellation.
-- This only enforces uniqueness for ACTIVE appointments.
CREATE UNIQUE INDEX idx_appointments_active_slot
    ON appointments(slot_id)
    WHERE status IN ('confirmed', 'rescheduled');

CREATE INDEX idx_appointments_contact ON appointments(contact_id, status);

-- ============================================================
-- CAMPAIGN RECIPIENTS
-- ============================================================
CREATE TABLE campaign_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) NOT NULL,
    contact_id UUID REFERENCES contacts(id) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, sent, delivered, failed, skipped
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,

    CONSTRAINT unique_campaign_contact UNIQUE (campaign_id, contact_id)
);

-- ============================================================
-- CONVERSATION STATE
-- ============================================================
CREATE TABLE conversation_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id UUID REFERENCES contacts(id) UNIQUE NOT NULL,
    current_state VARCHAR(50) DEFAULT 'idle',
    -- States: idle, showing_slots, confirming_booking, confirming_cancel,
    --         reschedule_show_slots, confirming_reschedule, awaiting_info
    context JSONB DEFAULT '{}',
    last_message_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,  -- Auto-reset after 2 hours of inactivity
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversation_expires ON conversation_states(expires_at)
    WHERE current_state != 'idle';
```

### SQLAlchemy Model Notes

```python
# CRITICAL: All models with updated_at must use onupdate:
updated_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    onupdate=func.now()  # Auto-updates on any row change
)

# For the partial unique index in SQLAlchemy:
from sqlalchemy import Index
Index(
    'idx_appointments_active_slot',
    Appointment.slot_id,
    unique=True,
    postgresql_where=(Appointment.status.in_(['confirmed', 'rescheduled']))
)
```

---

## Phase Breakdown

---

### PHASE 0: Git Init & Project Skeleton
**Goal:** Initialize repository, create project skeleton with config files only.

**Git Commands:**
```bash
git init sms-chatbot
cd sms-chatbot

# Create skeleton files
# (Cursor creates: .gitignore, pyproject.toml, docker-compose.yml,
#  Dockerfile, .env.example, README.md, empty directory structure)

git add .
git commit -m "chore: initialize project skeleton with docker and config"
git checkout -b develop
```

**Directory Structure:**
```
sms-chatbot/
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml                # Project metadata, deps, tool config
├── requirements.txt              # Pinned deps (generated from pyproject.toml)
├── docker-compose.yml
├── docker-compose.dev.yml        # Dev overrides (ngrok, debug mode)
├── Dockerfile
├── .env.example
├── README.md
├── alembic.ini
├── alembic/
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry
│   ├── config.py                 # Pydantic Settings
│   ├── database.py               # Async SQLAlchemy engine/session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── contact.py
│   │   ├── message.py
│   │   ├── appointment.py
│   │   ├── availability.py
│   │   ├── campaign.py
│   │   └── conversation.py
│   ├── schemas/                  # Pydantic request/response models
│   │   ├── __init__.py
│   │   ├── contact.py
│   │   ├── message.py
│   │   ├── appointment.py
│   │   └── campaign.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py             # Main router aggregator
│   │   ├── deps.py               # Shared dependencies (get_db, get_services)
│   │   ├── webhooks.py           # SMS webhooks
│   │   ├── campaigns.py          # Campaign endpoints
│   │   ├── appointments.py       # Appointment endpoints
│   │   └── contacts.py           # Contact endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── sms_service.py        # Twilio send/receive/retry
│   │   ├── ai_service.py         # LLM integration
│   │   ├── scheduling_service.py # Availability + booking logic
│   │   ├── campaign_service.py   # Campaign orchestration
│   │   └── conversation_service.py # State machine
│   ├── core/
│   │   ├── __init__.py
│   │   ├── compliance.py         # STOP/START/HELP handling
│   │   ├── quiet_hours.py        # Timezone-aware quiet hours
│   │   ├── idempotency.py        # Webhook dedup via Redis/MessageSid
│   │   └── exceptions.py         # Custom exceptions
│   └── workers/
│       ├── __init__.py
│       └── tasks.py              # arq task definitions (campaigns, expiry)
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Fixtures: test DB, mock Twilio, mock Claude
│   ├── test_sms_webhook.py
│   ├── test_compliance.py
│   ├── test_booking.py
│   ├── test_ai_service.py
│   ├── test_conversation.py
│   ├── test_campaign.py
│   └── test_integration.py
└── scripts/
    ├── seed_availability.py      # Dev seed data
    └── setup_ngrok.sh            # Dev tunnel setup helper
```

**Acceptance Criteria:**
- [ ] `git log` shows initial commit
- [ ] develop branch created
- [ ] All config files present and valid
- [ ] `.env` is gitignored, `.env.example` is tracked

---

### PHASE 1: Foundation & Database
**Goal:** Docker environment, database models, migrations, health check.

**Git Branch:** `feature/phase-1-foundation`

**Tasks:**
1. Create `docker-compose.yml` with PostgreSQL 16, Redis 7, and app service
2. Create `docker-compose.dev.yml` with ngrok service for Twilio webhook tunneling
3. Set up FastAPI app with health check endpoint (verifies DB + Redis connectivity)
4. Configure async SQLAlchemy with connection pooling (`pool_size=5, max_overflow=10`)
5. Create all SQLAlchemy models matching the corrected schema above
6. Set up Alembic with async engine support
7. Run initial migration to create all tables
8. Create seed script for test availability slots (next 7 days, 9AM-5PM, 30-min slots)
9. Create Pydantic settings class with validation

**docker-compose.dev.yml (dev overrides):**
```yaml
# Extends docker-compose.yml for local development
services:
  ngrok:
    image: ngrok/ngrok:latest
    restart: unless-stopped
    command: http app:8000
    environment:
      - NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN}
    ports:
      - "4040:4040"  # ngrok inspect UI
    depends_on:
      - app

  app:
    environment:
      - APP_ENV=development
      - DEBUG=true
    volumes:
      - ./app:/app/app  # Hot reload
```

**Config (.env.example):**
```env
# App
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
SECRET_KEY=change-me-in-production
BUSINESS_NAME="Acme Services"

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/sms_chatbot
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://redis:6379/0

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_STATUS_CALLBACK_URL=https://your-domain.com/webhooks/sms/status
TWILIO_MAX_RETRIES=3

# Anthropic
ANTHROPIC_API_KEY=your_api_key
AI_MODEL=claude-sonnet-4-20250514
AI_MAX_TOKENS=300

# Campaign Defaults
DEFAULT_QUIET_HOURS_START=21:00
DEFAULT_QUIET_HOURS_END=09:00

# Dev only
NGROK_AUTHTOKEN=your_ngrok_token
```

**Git Commits:**
```bash
git checkout -b feature/phase-1-foundation
# ... build ...
git commit -m "feat(infra): add Docker Compose with PostgreSQL, Redis, ngrok"
git commit -m "feat(db): add SQLAlchemy models for all entities"
git commit -m "feat(db): add Alembic migrations with async support"
git commit -m "feat(api): add FastAPI app with health check endpoint"
git commit -m "chore: add seed script for test availability slots"
git checkout develop && git merge feature/phase-1-foundation --no-ff
git tag -a v0.1.0 -m "Phase 1: Foundation complete"
```

**Acceptance Criteria:**
- [ ] `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up` starts all services including ngrok
- [ ] `GET /api/health` returns 200 with `{"db": "ok", "redis": "ok"}`
- [ ] All tables created via Alembic migration
- [ ] Seed script populates 7 days of availability slots
- [ ] ngrok tunnel accessible at `http://localhost:4040`

---

### PHASE 2: SMS Integration (Twilio)
**Goal:** Send and receive SMS with idempotent webhooks, compliance handling, retry logic, full message logging.

**Git Branch:** `feature/phase-2-sms-integration`

**Key Files:**
- `app/services/sms_service.py`
- `app/api/webhooks.py`
- `app/core/compliance.py`
- `app/core/idempotency.py`

**Idempotency Handler (NEW — prevents duplicate processing on Twilio retries):**

```python
# app/core/idempotency.py
"""
Webhook idempotency via Redis.

WHY THIS IS NEEDED:
Twilio retries webhooks if it doesn't get a 200 response within 15 seconds.
If our AI processing takes too long on first attempt, Twilio sends the same
message again. Without idempotency, we'd process and reply twice.

MECHANISM:
- On inbound webhook: SET message:{sms_sid} EX 3600 NX
  - NX = only set if not exists
  - Returns True if new (process it), False if duplicate (skip it)
- TTL of 1 hour covers Twilio's retry window with margin

is_duplicate(sms_sid: str) -> bool
    Returns True if we've already seen this MessageSid.
    
mark_processed(sms_sid: str) -> None
    Mark a MessageSid as processed (set Redis key).
"""
```

**SMS Service (updated with retry logic):**

```python
# app/services/sms_service.py
"""
Core SMS service wrapping Twilio.

RETRY LOGIC:
- On send failure: retry up to 3 times with exponential backoff (1s, 2s, 4s)
- Retry on: network errors, 429 rate limits, 5xx Twilio errors
- Do NOT retry on: invalid number (21211), unsubscribed (21610), etc.
- Log each attempt with retry count

SEND FLOW:
1. Validate phone format (E.164 regex: ^\+[1-9]\d{1,14}$)
2. Check contact opt-in status (raise ContactOptedOutError if opted out)
3. Create message record with status='queued'
4. Send via Twilio with status callback URL
5. Update message record with sms_sid and status='sent'
6. On failure: retry or update status='failed' with error details
"""

class SMSService:
    """
    Methods:
    - async send_message(to: str, body: str, campaign_id: str = None) -> Message
        Full send flow with retry. Returns Message ORM object.

    - async handle_inbound(from_number: str, body: str, sms_sid: str) -> None
        Called by webhook AFTER idempotency check.
        1. Check compliance keywords first
        2. If compliance: handle and respond
        3. If not: dispatch to conversation_service.process_inbound_message()

    - async update_status(sms_sid: str, status: str, error_code: str = None) -> None
        Idempotent status update (uses sms_sid lookup via unique index).

    - validate_signature(url: str, params: dict, signature: str) -> bool
        Wraps Twilio RequestValidator. Raises 403 on failure.
    """
```

**Webhook Endpoints (updated — async processing):**

```python
# app/api/webhooks.py
"""
CRITICAL DESIGN: Return 200 immediately, process in background.

POST /webhooks/sms/inbound
Flow:
1. Validate Twilio signature → 403 if invalid
2. Extract From, Body, MessageSid from form data
3. Idempotency check (Redis) → if duplicate, return 200 and stop
4. Mark MessageSid as processing in Redis
5. Return 200 with empty TwiML: <Response></Response>
6. Dispatch to BackgroundTask: sms_service.handle_inbound(...)

WHY: AI intent detection can take 2-5 seconds. If we process inline,
slow responses risk Twilio's 15-second timeout + retry, causing
duplicate processing. The idempotency layer is our safety net,
but returning immediately avoids the problem entirely.

POST /webhooks/sms/status
1. Validate Twilio signature
2. Extract MessageSid, MessageStatus, ErrorCode, ErrorMessage
3. Call sms_service.update_status() — lightweight, can be inline
4. Return 200
"""
```

**Compliance Handler:**

```python
# app/core/compliance.py
"""
TCPA/CTIA Compliance — MUST be checked BEFORE any AI processing.

Keywords (case-insensitive, stripped of whitespace):
- OPT-OUT: STOP, STOPALL, UNSUBSCRIBE, CANCEL, END, QUIT
  → Set contact.opt_in_status = 'opted_out', contact.opt_out_date = now()
  → Send: "You have been unsubscribed and will not receive further messages. Reply START to re-subscribe."
  → NOTE: Twilio's Advanced Opt-Out handles this at the carrier level too,
    but we MUST also handle it in our system for data consistency.

- OPT-IN: START, YES, UNSTOP
  → Set contact.opt_in_status = 'opted_in', contact.opt_in_date = now()
  → Send: "You have been re-subscribed to {business_name} messages. Reply STOP to unsubscribe."

- HELP: HELP, INFO
  → Send: "{business_name}: For support call {support_number}. Msg frequency varies. Msg&data rates may apply. Reply STOP to cancel."

is_compliance_keyword(text: str) -> tuple[bool, str | None]
handle_compliance(contact_id: str, keyword_type: str) -> str
"""
```

**Git Commits:**
```bash
git checkout -b feature/phase-2-sms-integration
git commit -m "feat(sms): add Twilio SMS service with retry logic"
git commit -m "feat(sms): add webhook endpoints with async background processing"
git commit -m "feat(core): add Redis-based webhook idempotency handler"
git commit -m "feat(core): add TCPA/CTIA compliance keyword handler"
git commit -m "test(sms): add webhook, compliance, and idempotency tests"
git checkout develop && git merge feature/phase-2-sms-integration --no-ff
git tag -a v0.2.0 -m "Phase 2: SMS integration complete"
```

**Acceptance Criteria:**
- [ ] Can send SMS to a test number via API endpoint
- [ ] Inbound webhook returns 200 immediately, processes in background
- [ ] Duplicate MessageSid detected and skipped (test with same SID twice)
- [ ] STOP/START/HELP keywords handled correctly
- [ ] All messages logged with sms_sid, status, timestamps
- [ ] Twilio signature validation rejects forged requests
- [ ] Status callback updates message records
- [ ] Failed sends retry up to 3 times with backoff

---

### PHASE 3: AI Layer (Intent Detection + NLU)
**Goal:** Use Claude to detect user intent, extract time preferences, parse slot selections, and generate conversational responses.

**Git Branch:** `feature/phase-3-ai-layer`

**Key Files:**
- `app/services/ai_service.py`

**AI Service Design:**

```python
# app/services/ai_service.py
"""
LLM-powered intent detection and response generation.
Uses Anthropic Claude API with tool_use for structured outputs.

INTENTS:
- BOOK: User wants to schedule an appointment
- RESCHEDULE: User wants to change existing appointment
- CANCEL: User wants to cancel an appointment
- QUESTION: General question about services, hours, location
- CONFIRM: Affirmative response (yes, sure, that works, confirm)
- DENY: Negative response (no, that doesn't work, nevermind)
- SELECT_SLOT: User is picking from presented options ("2", "the 3pm one")
- UNCLEAR: Can't determine intent

STRUCTURED OUTPUT (via tool_use):
{
    "intent": "BOOK",
    "confidence": 0.95,
    "extracted_data": {
        "date_preference": "2026-03-15",    // ISO date or null
        "time_preference": "afternoon",      // morning/afternoon/evening/specific time
        "day_preference": "next tuesday",    // Natural language day reference
        "service_type": "consultation",      // If mentioned
        "slot_selection": null               // Number or description when selecting
    },
    "response_text": "I'd love to help you book! Let me check what's available next Tuesday afternoon.",
    "needs_info": ["date", "time"]
}

CONVERSATION HISTORY MANAGEMENT:
- Include last 10 messages (5 pairs of user/assistant)
- Cap total context at ~2000 tokens to keep costs low
- Always include current conversation state in system prompt
- Trim oldest messages first if over token budget

FALLBACK BEHAVIOR:
- If Anthropic API is down: return generic "Sorry, having a brief issue.
  Please try again in a moment." with intent=UNCLEAR
- If response parsing fails: same fallback
- Log all API errors with full request context for debugging
"""

class AIService:
    """
    Methods:
    - async detect_intent(
        message: str,
        conversation_history: list[dict],  # Last 10 messages
        available_slots: list[dict] = None,
        current_appointment: dict = None,
        conversation_state: str = "idle"
      ) -> IntentResult
        Primary intent detection. Returns structured IntentResult.

    - async parse_slot_selection(
        message: str,
        presented_slots: list[dict]
      ) -> str | None
        MOVED FROM SchedulingService (v1 bug: this is an NLU task, not scheduling).
        Maps "2", "the second one", "the 3pm one", "Tuesday" to a slot_id.
        Uses Claude with the slot list as context for fuzzy matching.
        Returns slot_id or None if can't determine.

    - generate_slot_presentation(
        slots: list[dict],
        timezone: str
      ) -> str
        Formats slots into SMS-friendly numbered list.
        Converts UTC times to contact's timezone.
        Example output:
        "Here are some available times:
        1) Tue Mar 15, 2:00 PM
        2) Tue Mar 15, 3:30 PM
        3) Wed Mar 16, 10:00 AM
        Reply with a number to book!"

    - generate_confirmation(appointment: dict, timezone: str) -> str
        "You're all set! Your appointment is confirmed for Tue Mar 15 at 2:00 PM.
        Reply CANCEL to cancel or RESCHEDULE to change."

    - generate_error_response(error_type: str) -> str
        Friendly error messages per error type. No AI call needed — templates.
    """
```

**Claude System Prompt Template (revised):**

```
You are a friendly, professional appointment scheduling assistant for {business_name}.
You communicate via SMS, so keep responses concise (under 320 characters when possible, max 480).

Current date/time: {current_datetime} ({contact_timezone})
Conversation state: {current_state}

Your job:
1. Understand what the user wants (book, reschedule, cancel, or ask a question)
2. Extract any time/date preferences from their message
3. Guide them through the booking process naturally

Rules:
- Be warm but efficient — SMS, not email
- When showing time slots, number them for easy reply
- Always confirm before finalizing a booking
- If unsure, ask ONE simple clarifying question
- NEVER fabricate availability — only reference slots provided to you
- If the user seems confused, gently explain what they can do: "book", "reschedule", or "cancel"

{context_section}

Use the provided tool to return your structured response.
```

**Git Commits:**
```bash
git checkout -b feature/phase-3-ai-layer
git commit -m "feat(ai): add AIService with Claude tool_use intent detection"
git commit -m "feat(ai): add slot selection parsing via NLU"
git commit -m "feat(ai): add response generation (slots, confirmation, errors)"
git commit -m "feat(ai): add conversation history management with token cap"
git commit -m "test(ai): add intent detection and slot parsing tests with mocked API"
git checkout develop && git merge feature/phase-3-ai-layer --no-ff
git tag -a v0.3.0 -m "Phase 3: AI layer complete"
```

**Acceptance Criteria:**
- [ ] Intent detection works for all 8 intent types
- [ ] Time preferences extracted from natural language ("next Tuesday", "this afternoon", "March 15th", "in 2 days")
- [ ] Slot selection parsing handles: numbers ("2"), ordinals ("the second one"), time refs ("the 3pm one")
- [ ] Responses stay under 480 characters
- [ ] Confidence scores returned; < 0.6 triggers clarification prompt
- [ ] Conversation history capped at 10 messages
- [ ] AI service failure returns graceful fallback response (no crash)

---

### PHASE 4: Scheduling Engine (Availability + Booking)
**Goal:** Fetch real-time availability, book with concurrency-safe transactions, handle reschedule/cancel with slot staleness protection.

**Git Branch:** `feature/phase-4-scheduling`

**Key Files:**
- `app/services/scheduling_service.py`

```python
# app/services/scheduling_service.py
"""
All appointment logic with concurrency-safe booking.

DOUBLE-BOOKING PREVENTION (2 layers):
1. SELECT FOR UPDATE — row-level lock during booking transaction
2. Partial unique index on appointments(slot_id) WHERE status IN ('confirmed','rescheduled')

BOOKING FLOW:
1. Fetch available slots matching preferences
2. Present options to user (AI formats)
3. User selects a slot (could be minutes/hours later via SMS)
4. BEGIN TRANSACTION:
   a. SELECT slot FOR UPDATE (acquires row lock — other transactions wait)
   b. Verify slot.is_available is still TRUE
   c. If FALSE → raise SlotUnavailableError (another user booked it)
   d. Set slot.is_available = FALSE
   e. INSERT appointment record (partial unique index provides final safety net)
   f. COMMIT (releases row lock)
5. Send confirmation SMS
6. On SlotUnavailableError → re-fetch and present alternative slots

SLOT STALENESS PROTECTION:
When user picks a slot, it may have been minutes since they saw the list.
Always re-verify at booking time. If their chosen slot was taken:
1. Acknowledge: "Sorry, that slot was just booked by someone else."
2. Immediately fetch and present fresh alternatives
3. Transition back to SHOWING_SLOTS state (not IDLE)

RESCHEDULE ATOMICITY:
Reschedule must be a single transaction:
1. BEGIN TRANSACTION
2. Lock OLD slot (FOR UPDATE)
3. Lock NEW slot (FOR UPDATE)
4. Verify new slot available
5. Set old slot.is_available = TRUE
6. Set new slot.is_available = FALSE
7. Update old appointment status = 'rescheduled'
8. Create new appointment with rescheduled_from_id = old.id
9. COMMIT
If new slot unavailable → ROLLBACK (old appointment untouched)
"""

class SchedulingService:
    """
    Methods:
    - async get_available_slots(
        date_from: datetime,
        date_to: datetime,
        provider_id: str = None,
        limit: int = 5
      ) -> list[AvailabilitySlot]
        Returns available slots ordered by start_time.
        Accounts for buffer_minutes (doesn't show slots that overlap with buffers).

    - async book_appointment(
        contact_id: str,
        slot_id: str
      ) -> Appointment
        RAISES: SlotUnavailableError if slot taken.
        Uses SELECT FOR UPDATE inside async session transaction.

    - async cancel_appointment(
        appointment_id: str,
        reason: str = None
      ) -> Appointment
        Transaction: mark appointment cancelled + re-open slot.
        Uses optimistic locking (version check) to prevent stale cancellations.

    - async reschedule_appointment(
        appointment_id: str,
        new_slot_id: str
      ) -> Appointment
        Single transaction: free old slot + book new slot.
        Returns new Appointment with rescheduled_from_id set.
        RAISES: SlotUnavailableError if new slot taken (old appointment unchanged).

    - async get_contact_appointments(
        contact_id: str,
        status_filter: list[str] = ['confirmed']
      ) -> list[Appointment]
        Returns contact's appointments with eager-loaded slot data.

    - async get_fresh_alternatives(
        exclude_slot_ids: list[str],
        date_from: datetime = None,
        limit: int = 5
      ) -> list[AvailabilitySlot]
        Fetch new options excluding already-shown-and-taken slots.
        Used in staleness recovery flow.
    """
```

**Git Commits:**
```bash
git checkout -b feature/phase-4-scheduling
git commit -m "feat(scheduling): add availability slot queries with buffer support"
git commit -m "feat(scheduling): add concurrency-safe booking with FOR UPDATE"
git commit -m "feat(scheduling): add atomic cancel with slot re-opening"
git commit -m "feat(scheduling): add atomic reschedule (single transaction)"
git commit -m "feat(scheduling): add slot staleness recovery flow"
git commit -m "test(scheduling): add concurrent booking test (10 requests, 1 wins)"
git commit -m "test(scheduling): add cancel re-booking and reschedule tests"
git checkout develop && git merge feature/phase-4-scheduling --no-ff
git tag -a v0.4.0 -m "Phase 4: Scheduling engine complete"
```

**Acceptance Criteria:**
- [ ] Available slots fetched with correct date filtering and buffer accounting
- [ ] Booking is atomic — concurrent test (10 requests, same slot) → exactly 1 succeeds
- [ ] Cancelled appointment's slot becomes re-bookable
- [ ] Reschedule succeeds atomically or rolls back entirely
- [ ] Slot staleness: booking a taken slot returns alternatives instead of crashing
- [ ] Partial unique index allows re-booking cancelled slots

---

### PHASE 5: Conversation State Machine
**Goal:** Orchestrate the full conversation flow from inbound message to resolution.

**Git Branch:** `feature/phase-5-conversation`

**Key Files:**
- `app/services/conversation_service.py`

**State Machine (revised — added RESCHEDULE_SHOW_SLOTS and AWAITING_INFO):**

```
                      ┌───────────┐
          ┌──────────►│   IDLE    │◄─────────────────────────────┐
          │           └─────┬─────┘                              │
          │                 │ (inbound msg)                       │
          │                 ▼                                     │
          │        ┌────────────────┐                            │
          │        │ AI CLASSIFIES  │                            │
          │        │ (detect_intent)│                            │
          │        └──┬──┬──┬──┬───┘                            │
          │    BOOK   │  │  │  │  CANCEL                        │
          │           │  │  │  │                                │
          │    ┌──────┘  │  │  └──────┐                         │
          │    ▼         │  │         ▼                          │
          │ ┌──────────┐ │  │  ┌──────────────┐                 │
          │ │ SHOWING  │ │  │  │ CONFIRMING   │─── yes ────────►│
          │ │ SLOTS    │ │  │  │ CANCEL       │                 │
          │ └────┬─────┘ │  │  └──────┬───────┘                 │
          │      │       │  │         │ no                       │
          │      │ pick  │  │         └──────────────────────────┤
          │      ▼       │  │                                    │
          │ ┌──────────┐ │  │ RESCHEDULE                        │
          │ │CONFIRMING│ │  │                                    │
          │ │ BOOKING  │ │  └──────┐                             │
          │ └──┬───┬───┘          ▼                              │
          │    │   │     ┌──────────────────┐                    │
          │ yes│   │no   │ RESCHEDULE       │                    │
          │    │   │     │ SHOW_SLOTS       │──pick──►CONFIRMING │
          │    │   │     └────────┬─────────┘         RESCHEDULE │
          │    │   │              │ (shows new slots,             │
          │    │   └──►SHOWING   │  keeps old appt until         │
          │    │       SLOTS     │  new one confirmed)            │
          │    │                 │                                │
          │    ▼                 │         ┌──────────────┐       │
          │  BOOK ──────────────┼────────►│  DONE        │───────┘
          │  SUCCESS            │         └──────────────┘
          │                     │
          │                     │
          │  ┌──────────────┐   │
          │  │ AWAITING_INFO│◄──┘  (AI needs more details)
          │  │ (loops back  │
          │  │  to classify)│
          │  └──────────────┘
          │
          │  ┌──────────────────┐
          └──┤ TIMEOUT (2 hours)│
             └──────────────────┘
```

```python
# app/services/conversation_service.py
"""
Central orchestrator. Routes inbound messages through the state machine.

INBOUND MESSAGE PROCESSING:
1. Look up contact by phone number
2. If unknown number: create contact record with opt_in_status='pending'
   (they texted us, so they're initiating — but we should confirm opt-in)
3. Compliance check FIRST (STOP/START/HELP) — short-circuits everything
4. Load conversation state (DB, with Redis cache for hot conversations)
5. Route to appropriate state handler
6. Update state + send response SMS

STATE CONTEXT (conversation_states.context JSONB):
{
    "presented_slots": [            // Currently shown options
        {"index": 1, "slot_id": "...", "display": "Tue 3/15 2:00 PM"},
        {"index": 2, "slot_id": "...", "display": "Tue 3/15 3:30 PM"}
    ],
    "selected_slot_id": "...",      // Pending confirmation
    "pending_appointment_id": "...", // For cancel/reschedule
    "original_appointment_id": "...", // During reschedule
    "last_intent": "BOOK",
    "retry_count": 0,               // Max 3 retries before reset
    "campaign_id": "..."
}

TIMEOUT HANDLING:
- Each state update sets expires_at = now() + 2 hours
- arq periodic task checks for expired conversations every 5 minutes
- Expired conversations: reset to IDLE, optionally send
  "Looks like we got disconnected. Text us anytime to book!"
"""

class ConversationService:
    """
    Methods:
    - async process_inbound_message(phone_number: str, body: str, sms_sid: str) -> None
        Main entry point. Full orchestration.

    - async _handle_idle(contact, message, state) -> tuple[str, str]
        AI classifies intent → route to appropriate next state.

    - async _handle_showing_slots(contact, message, state) -> tuple[str, str]
        Parse slot selection via AI.
        Valid pick → CONFIRMING_BOOKING
        Invalid → re-prompt (increment retry_count, max 3)
        New intent detected (e.g., "actually I want to cancel") → re-route

    - async _handle_confirming_booking(contact, message, state) -> tuple[str, str]
        CONFIRM → attempt booking
          If slot still available → book, send confirmation, → IDLE
          If slot taken (staleness) → fetch alternatives, → SHOWING_SLOTS
        DENY → "No problem!" → SHOWING_SLOTS or IDLE

    - async _handle_confirming_cancel(contact, message, state) -> tuple[str, str]
        CONFIRM → cancel appointment, → IDLE
        DENY → "OK, your appointment is still on the books." → IDLE

    - async _handle_reschedule_show_slots(contact, message, state) -> tuple[str, str]
        Same as SHOWING_SLOTS but preserves original_appointment_id in context.
        On confirmation: calls scheduling_service.reschedule_appointment() atomically.

    - async _handle_awaiting_info(contact, message, state) -> tuple[str, str]
        AI got partial info last round. Re-run intent detection with updated context.
        If now have enough info → transition to appropriate next state.

    - async _expire_stale_conversations() -> None
        arq periodic task. Resets expired conversations.
    """
```

**Git Commits:**
```bash
git checkout -b feature/phase-5-conversation
git commit -m "feat(conversation): add state machine with all state handlers"
git commit -m "feat(conversation): add slot staleness recovery in booking flow"
git commit -m "feat(conversation): add reschedule flow with original appointment tracking"
git commit -m "feat(conversation): add timeout expiration via arq periodic task"
git commit -m "test(conversation): add full flow integration tests (book, cancel, reschedule)"
git commit -m "test(conversation): add edge case tests (staleness, timeout, mid-flow intent change)"
git checkout develop && git merge feature/phase-5-conversation --no-ff
git tag -a v0.5.0 -m "Phase 5: Conversation state machine complete"
```

**Acceptance Criteria:**
- [ ] Full booking flow: inbound → intent → slots → pick → confirm → booked → confirmation SMS
- [ ] Cancel flow: "cancel" → show appointment → confirm → cancelled → confirmation SMS
- [ ] Reschedule flow: "reschedule" → show new slots → pick → confirm → atomic swap → confirmation
- [ ] Staleness recovery: pick taken slot → "sorry, that's taken" → fresh alternatives
- [ ] Conversations expire after 2 hours of inactivity
- [ ] Mid-flow intent change handled (user says "cancel" while in booking flow)
- [ ] Unknown numbers get contact record created
- [ ] retry_count prevents infinite loops (max 3 re-prompts then reset)

---

### PHASE 6: Campaign Engine (Outbound)
**Goal:** Batch outbound SMS with quiet hours, timezone awareness, template variables, and state tracking.

**Git Branch:** `feature/phase-6-campaigns`

**Key Files:**
- `app/services/campaign_service.py`
- `app/workers/tasks.py`
- `app/core/quiet_hours.py`

```python
# app/services/campaign_service.py
"""
Campaign lifecycle: CREATE → SCHEDULE → EXECUTE → TRACK

TEMPLATE VARIABLES:
message_template supports:
- {first_name} — contact's first name (fallback: "there")
- {business_name} — from config
- {phone_number} — business phone for callbacks
Custom vars can be added via campaign metadata.

Example: "Hi {first_name}! {business_name} has openings this week.
Reply BOOK to schedule your appointment."

QUIET HOURS LOGIC (app/core/quiet_hours.py):
- Convert current UTC time to contact's timezone
- Check if local time falls within quiet_hours_start..quiet_hours_end
- If in quiet hours: calculate seconds until quiet_hours_end, schedule delayed delivery
- Edge case: quiet hours that span midnight (21:00 → 09:00) — handle wraparound

RATE LIMITING:
- Twilio long code: ~1 msg/sec
- Twilio toll-free: ~25 msg/sec (if registered)
- We batch at 1 msg/sec by default (configurable per campaign)
- Track via Redis: sms_rate:{phone_number} with TTL
"""

class CampaignService:
    """
    Methods:
    - async create_campaign(
        name: str,
        message_template: str,
        recipient_filter: dict = None
      ) -> Campaign
        Creates campaign, resolves recipients from filter, sets total_recipients.

    - async schedule_campaign(campaign_id: str, send_at: datetime) -> Campaign
        Validates send_at is in the future. Enqueues arq task for execution.

    - async execute_campaign(campaign_id: str) -> None
        Enqueues batch processing tasks via arq.
        Batches of 50 recipients per task.

    - async pause_campaign(campaign_id: str) -> Campaign
    - async resume_campaign(campaign_id: str) -> Campaign

    - async get_campaign_stats(campaign_id: str) -> CampaignStats
        Aggregates from campaign_recipients + messages tables.
    """

# app/workers/tasks.py
"""
arq task definitions.

async def process_campaign_batch(ctx, campaign_id: str, offset: int, batch_size: int = 50):
    For each recipient in batch:
    1. Re-check contact opt-in status (could have changed)
    2. Render template with contact's variables
    3. Check quiet hours for contact's timezone
       - In quiet hours → enqueue delayed task at quiet_hours_end
       - Clear → send now
    4. Send via sms_service.send_message()
    5. Update campaign_recipients.status
    6. Sleep 1 second (rate limiting)
    7. On batch complete: enqueue next batch if more recipients

async def expire_conversations(ctx):
    Periodic task (every 5 minutes).
    Finds conversation_states where expires_at < now() and current_state != 'idle'.
    Resets to idle, optionally sends timeout message.

async def retry_failed_sends(ctx):
    Periodic task (every 10 minutes).
    Re-attempts messages stuck in 'queued' status for > 5 minutes.
"""
```

**Git Commits:**
```bash
git checkout -b feature/phase-6-campaigns
git commit -m "feat(campaign): add campaign CRUD with template variable support"
git commit -m "feat(campaign): add quiet hours with timezone wraparound handling"
git commit -m "feat(workers): add arq batch processing with rate limiting"
git commit -m "feat(workers): add periodic tasks (conversation expiry, failed send retry)"
git commit -m "test(campaign): add batch send, quiet hours, and template rendering tests"
git checkout develop && git merge feature/phase-6-campaigns --no-ff
git tag -a v0.6.0 -m "Phase 6: Campaign engine complete"
```

**Acceptance Criteria:**
- [ ] Campaign creates with resolved recipient list
- [ ] Template variables render correctly ({first_name} fallback works)
- [ ] Messages sent in batches at 1/sec rate
- [ ] Quiet hours respected per contact timezone (including midnight wraparound)
- [ ] Pause stops sending, resume continues from where it left off
- [ ] Campaign stats accurate (sent/delivered/failed/reply counts)
- [ ] Replies from campaign-initiated contacts tracked back to campaign

---

### PHASE 7: Polish & Hardening
**Goal:** Error handling, logging, admin endpoints, comprehensive tests, documentation.

**Git Branch:** `feature/phase-7-polish`

**Tasks:**
1. Global exception handler with correlation IDs
2. Structured JSON logging (structlog) with phone number masking
3. Admin API endpoints with API key auth:
   - `GET/POST/DELETE /api/contacts`
   - `GET/POST/PATCH /api/campaigns`
   - `GET /api/appointments?contact_id=...`
   - `GET /api/messages?contact_id=...`
4. API documentation (FastAPI auto-generates OpenAPI, add descriptions)
5. Integration tests: full end-to-end flows with mocked Twilio + mocked Claude
6. Load test: concurrent booking stress test
7. README with setup instructions, architecture diagram, and dev workflow
8. Pre-commit hooks: ruff (linting), black (formatting), mypy (type checking)

**Git Commits:**
```bash
git checkout -b feature/phase-7-polish
git commit -m "feat(core): add global exception handler with correlation IDs"
git commit -m "feat(core): add structured logging with phone masking"
git commit -m "feat(api): add admin endpoints with API key authentication"
git commit -m "test: add end-to-end integration tests"
git commit -m "test: add concurrent booking load test"
git commit -m "docs: add comprehensive README and API documentation"
git commit -m "chore: add pre-commit hooks (ruff, black, mypy)"
git checkout develop && git merge feature/phase-7-polish --no-ff
git checkout main && git merge develop --no-ff
git tag -a v1.0.0 -m "MVP complete: SMS appointment chatbot"
```

---

## Cross-Cutting Concerns

### Error Handling Strategy
```python
# app/core/exceptions.py
class SMSChatbotError(Exception):
    """Base exception — all custom errors inherit from this."""
    def __init__(self, message: str, user_message: str = None):
        self.message = message
        # user_message = what to SMS back. None = don't send anything.
        self.user_message = user_message

class SlotUnavailableError(SMSChatbotError):
    """Slot was booked between presentation and selection."""
    def __init__(self, slot_id: str):
        super().__init__(
            f"Slot {slot_id} no longer available",
            user_message=None  # Handled by staleness recovery, not error handler
        )

class ContactOptedOutError(SMSChatbotError):
    """Attempted to send to opted-out contact."""

class QuietHoursError(SMSChatbotError):
    """Send attempted during contact's quiet hours."""

class AIServiceError(SMSChatbotError):
    """LLM API failure."""
    def __init__(self, original_error: Exception):
        super().__init__(
            f"AI service error: {original_error}",
            user_message="Sorry, I'm having a brief technical issue. Please try again in a moment!"
        )

class WebhookValidationError(SMSChatbotError):
    """Twilio signature validation failed."""

# Global handler in main.py:
@app.exception_handler(SMSChatbotError)
async def handle_chatbot_error(request, exc):
    log.error("chatbot_error", error=exc.message, correlation_id=request.state.correlation_id)
    if exc.user_message and hasattr(request.state, 'reply_phone'):
        await sms_service.send_message(request.state.reply_phone, exc.user_message)
    return JSONResponse(status_code=500, content={"error": exc.message})
```

### Security
- Twilio webhook signature validation on ALL webhook endpoints
- API key auth on admin/management endpoints (header: `X-API-Key`)
- Database credentials via environment variables only
- Phone numbers masked in all logs: `+1234***7890`
- SQL injection prevention via ORM (no raw queries anywhere)
- Rate limiting on API endpoints via Redis (slowapi or custom middleware)
- CORS disabled on webhook endpoints
- Input validation via Pydantic schemas on all endpoints

### Testing Strategy
```
tests/
├── conftest.py                # Shared fixtures
│   ├── test_db (PostgreSQL test container)
│   ├── mock_twilio_client (intercepts sends, returns fake SIDs)
│   ├── mock_anthropic_client (returns canned IntentResults)
│   ├── test_contact, test_slot factories
├── test_sms_webhook.py        # Signature validation, async dispatch, idempotency
├── test_compliance.py         # All keyword variants, case insensitivity
├── test_booking.py            # Book, cancel, reschedule + concurrency + staleness
├── test_ai_service.py         # Intent detection, slot parsing, fallback behavior
├── test_conversation.py       # Full state machine: every path + edge cases
├── test_campaign.py           # Batch send, quiet hours, templates, pause/resume
└── test_integration.py        # End-to-end: SMS in → booking → confirmation out
```

---

## Cursor Prompt Sequence (Revised)

Each prompt should reference this blueprint document. Preface all prompts with:
> "Refer to the SMS Chatbot Blueprint v2 document for full specifications, schema, and architecture decisions."

**Prompt 0:** "Initialize a git repository called 'sms-chatbot'. Create the project skeleton with: .gitignore, pyproject.toml (with deps: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, twilio, anthropic, redis, arq, pydantic-settings, structlog, pytest, pytest-asyncio, httpx), docker-compose.yml, docker-compose.dev.yml (with ngrok), Dockerfile, .env.example, and the empty directory structure from the blueprint. Commit to main, then create a develop branch."

**Prompt 1:** "Branch feature/phase-1-foundation from develop. Build: FastAPI app with health check (verify DB + Redis), async SQLAlchemy models for ALL entities (use the corrected schema from the blueprint — note the partial unique index on appointments, onupdate for updated_at, campaigns defined before messages), Alembic async migrations, Pydantic config class, and seed script for 7 days of availability slots. Commit with conventional commits and merge to develop with tag v0.1.0."

**Prompt 2:** "Branch feature/phase-2-sms-integration. Build: Twilio SMS service with 3-retry exponential backoff, webhook endpoints that return 200 IMMEDIATELY and process via BackgroundTasks, Redis-based idempotency handler (MessageSid dedup), TCPA/CTIA compliance handler (STOP/START/HELP). Add tests for webhooks, idempotency, and compliance. Merge to develop, tag v0.2.0."

**Prompt 3:** "Branch feature/phase-3-ai-layer. Build: AI service using Anthropic Claude with tool_use for structured intent detection (8 intent types), slot selection parsing via NLU (moved from scheduling service), response generation methods, conversation history management (last 10 messages, ~2000 token cap), graceful fallback on API failure. Add tests with mocked Anthropic client. Merge to develop, tag v0.3.0."

**Prompt 4:** "Branch feature/phase-4-scheduling. Build: scheduling service with SELECT FOR UPDATE concurrency-safe booking, partial unique index support, atomic cancel-with-reopen, atomic reschedule (single transaction), slot staleness recovery (re-fetch alternatives), buffer_minutes support. Write the concurrent booking test (10 simultaneous requests → exactly 1 succeeds). Merge to develop, tag v0.4.0."

**Prompt 5:** "Branch feature/phase-5-conversation. Build: conversation state machine with states: idle, showing_slots, confirming_booking, confirming_cancel, reschedule_show_slots, confirming_reschedule, awaiting_info. Include: staleness recovery flow, 2-hour timeout via arq periodic task, mid-flow intent change detection, retry_count cap (3), unknown number handling. Add integration tests for every flow path. Merge to develop, tag v0.5.0."

**Prompt 6:** "Branch feature/phase-6-campaigns. Build: campaign service with template variable interpolation ({first_name}, {business_name}), arq batch processing at 1 msg/sec, timezone-aware quiet hours with midnight wraparound, pause/resume, stats aggregation. Add periodic tasks: conversation expiry (5 min), failed send retry (10 min). Tests for all campaign flows. Merge to develop, tag v0.6.0."

**Prompt 7:** "Branch feature/phase-7-polish. Add: global exception handler with SMSChatbotError hierarchy and correlation IDs, structured JSON logging with phone masking, admin API endpoints with API key auth, comprehensive integration tests (end-to-end with mocked Twilio + Claude), README with setup/architecture/dev workflow. Merge to develop, then develop to main, tag v1.0.0."

---

## Deployment Notes

### Production Checklist
- [ ] Twilio webhook URLs configured with HTTPS (no ngrok!)
- [ ] A2P 10DLC registration completed (REQUIRED for US SMS at scale)
- [ ] Database connection pooling tuned (pool_size=10, max_overflow=20 for production)
- [ ] Redis persistence configured (AOF recommended)
- [ ] arq workers running with appropriate concurrency
- [ ] Structured logging shipping to aggregator (Datadog, CloudWatch, etc.)
- [ ] Health check endpoint monitored with alerting
- [ ] Database backups scheduled (pg_dump or managed service snapshots)
- [ ] SSL/TLS on all endpoints
- [ ] Environment variables via secrets manager (not .env files)
- [ ] API keys rotated and stored securely
- [ ] Twilio phone number(s) toll-free or short code for higher throughput

### Scaling Path (Post-MVP)
- Migrate arq → Celery when campaign volume exceeds single-worker capacity
- Add PostgreSQL read replicas for availability queries
- Redis cluster for high-volume campaigns
- Twilio Messaging Service for multi-number sending pools
- Add webhook queue (SQS/RabbitMQ) between Twilio and app for burst handling
- Admin dashboard UI (React) for campaign management
