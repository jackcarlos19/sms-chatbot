# Admin Dashboard — Autonomous Build Spec v2

> **Instructions for Cursor:** Read this ENTIRE file top to bottom before writing any code. Execute each phase in order. After each phase, run the specified verification steps. Fix any failures before committing. Do not skip phases. Do not reorder steps. Do not add CORS middleware — the Vite dev proxy and Docker same-origin handle this. Do not install any UI component libraries (no shadcn, MUI, Ant Design, Chakra). Use Tailwind utility classes only.

---

## Project Context

This is an SMS appointment booking chatbot for home services companies. The backend is FastAPI + PostgreSQL + Redis, fully functional with 43 passing tests.

**Existing backend capabilities:**
- Inbound SMS → AI intent detection → booking/cancel/reschedule flows
- Outbound campaigns with Redis-based rate limiting
- 24-hour appointment reminders (cron)
- Simulator API at `POST /api/simulate/inbound`
- Existing demo chat UI at `/demo` (keep this — do not remove it)

**What you're building:** A React admin dashboard at `/admin` where business owners manage contacts, view conversations, see appointments, run campaigns, and monitor system health.

---

## Architecture Decisions (Non-Negotiable)

1. **React SPA** — Vite + React 18 + TypeScript + Tailwind CSS v4
2. **Location:** `admin/` directory at project root (sibling to `app/`, `tests/`, `scripts/`)
3. **Build output:** `admin/dist/` — FastAPI serves this as static files in production
4. **Routing:** React Router v6 with `<BrowserRouter basename="/admin">`
5. **API calls:** Thin fetch wrapper hitting `/api/*` with `X-API-Key` header
6. **Auth:** Admin enters API key once, stored in `sessionStorage` (cleared on tab close)
7. **Styling:** Tailwind utility classes only. No external UI or icon libraries
8. **Icons:** Inline SVGs or Unicode characters (📊 📋 📅 💬 📣 🧪 🗓️)
9. **No CORS middleware** — Do NOT add CORS to FastAPI. The Vite dev proxy handles dev, and production is same-origin
10. **Do not remove or modify** the existing `/demo` route or `app/static/simulator.html`

---

## Existing API Endpoints (Already Built — Do NOT Modify)

All require `X-API-Key` header matching `ADMIN_API_KEY` env var (default: `change-this-admin-key`).

```
GET    /api/contacts?limit=100&offset=0
  → [{id, phone_number, first_name, last_name, timezone, opt_in_status, created_at}]

GET    /api/campaigns?limit=100&offset=0
  → [{id, name, status, scheduled_at, total_recipients, sent_count, delivered_count, failed_count, reply_count, created_at}]

POST   /api/campaigns
  Body: {name, message_template, recipient_filter: {}}
  → {id, name, status, total_recipients}

PATCH  /api/campaigns/{campaign_id}
  Body: {status?, scheduled_at?}
  → {id, name, status, scheduled_at}

GET    /api/appointments?contact_id={uuid}      ← REQUIRED param, returns 422 without it
  → [{id, contact_id, slot_id, status, booked_at, cancelled_at, rescheduled_from_id}]

GET    /api/messages?contact_id={uuid}           ← REQUIRED param, returns newest first
  → [{id, contact_id, direction, body, sms_sid, status, error_code, campaign_id, created_at}]

GET    /api/health
  → {status: "green", db: "ok", redis: "ok"}

POST   /api/simulate/inbound
  Body: {phone_number: "+15551234567", message: "text"}
  → {responses: ["..."], conversation_state: "idle", context: {}}
```

**Important notes for the frontend:**
- `/api/messages` returns newest-first. Reverse the array in the UI for chat display (oldest at top).
- `/api/appointments?contact_id=...` requires contact_id. For the "all appointments" view, use the NEW endpoint below.
- Campaign `create` response has fewer fields than `list` response. After creating, refetch the campaigns list.

---

## Database Models Reference (Read-Only — Do NOT Modify)

**contacts:** id (UUID), phone_number (str, unique), first_name (str, nullable), last_name (str, nullable), timezone (str, default 'America/New_York'), opt_in_status (str, default 'opted_in'), opt_in_date (datetime, nullable), opt_out_date (datetime, nullable), metadata (JSONB), created_at, updated_at

**appointments:** id (UUID), contact_id (FK→contacts), slot_id (FK→availability_slots), status (str, default 'confirmed'), booked_at (datetime), cancelled_at (datetime, nullable), cancellation_reason (text, nullable), rescheduled_from_id (FK→appointments, nullable), notes (text, nullable), version (int), created_at, updated_at

**messages:** id (UUID), contact_id (FK→contacts, nullable), direction (str: 'inbound'|'outbound'), body (text), sms_sid (str, nullable, unique), status (str, default 'queued'), error_code (str, nullable), error_message (text, nullable), campaign_id (FK→campaigns, nullable), created_at, updated_at

**campaigns:** id (UUID), name (str), message_template (text), status (str, default 'draft'), scheduled_at (datetime, nullable), quiet_hours_start (time), quiet_hours_end (time), respect_timezone (bool), total_recipients (int), sent_count (int), delivered_count (int), failed_count (int), reply_count (int), created_at, updated_at

**campaign_recipients:** id (UUID), campaign_id (FK→campaigns), contact_id (FK→contacts), status (str, default 'pending'), sent_at (datetime, nullable), delivered_at (datetime, nullable)

**conversation_states:** id (UUID), contact_id (FK→contacts, unique), current_state (str, default 'idle'), context (JSONB), last_message_at (datetime, nullable), expires_at (datetime, nullable), created_at, updated_at

**availability_slots:** id (UUID), provider_id (UUID, nullable), start_time (datetime), end_time (datetime), buffer_minutes (int, default 0), slot_type (str, default 'standard'), is_available (bool, default true), created_at

---

## Phase 1: New Backend API Endpoints

Add these to `app/api/admin.py`. All must use `dependencies=[Depends(verify_admin_api_key)]`.

### New imports needed at the top of admin.py

```python
# Add these to existing imports in app/api/admin.py
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import case, func, and_
from app.models.conversation import ConversationState
from app.models.availability import AvailabilitySlot
```

### Endpoint 1: Dashboard Stats

```python
@router.get("/dashboard/stats", dependencies=[Depends(verify_admin_api_key)])
async def dashboard_stats() -> dict:
```

**Route path:** `/api/dashboard/stats`

Returns:
```json
{
  "contacts_total": 47,
  "contacts_opted_in": 42,
  "contacts_opted_out": 5,
  "appointments_today": 3,
  "appointments_upcoming": 12,
  "appointments_total": 89,
  "messages_today": 24,
  "messages_inbound_today": 11,
  "messages_outbound_today": 13,
  "conversations_active": 2,
  "campaigns_active": 1,
  "campaigns_total": 5
}
```

**Implementation details — follow exactly:**
- Use 4 queries, not one per field:
  - Query 1: Contacts — `func.count()` with `case()` for opt_in/opt_out
  - Query 2: Appointments — **JOIN with AvailabilitySlot** to get slot times. "Today" means `AvailabilitySlot.start_time` falls on today's UTC date (NOT `booked_at`). "Upcoming" means `Appointment.status == 'confirmed'` AND `AvailabilitySlot.start_time > now`.
  - Query 3: Messages — count with `case()` for direction + today filter on `Message.created_at`
  - Query 4: Conversations + Campaigns combined or separate
- Calculate today boundaries:
  ```python
  now = datetime.now(timezone.utc)
  today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
  today_end = today_start + timedelta(days=1)
  ```
- "Active conversations" = `ConversationState.current_state != 'idle'`
- "Active campaigns" = `Campaign.status == 'active'`

### Endpoint 2: All Appointments (global list, not per-contact)

```python
@router.get("/appointments/all", dependencies=[Depends(verify_admin_api_key)])
async def list_all_appointments(
    limit: int = 50, offset: int = 0, status: Optional[str] = None
) -> list[dict]:
```

**Route path:** `/api/appointments/all`

**CRITICAL:** This route MUST be defined BEFORE the existing `/appointments` route in the file to prevent FastAPI from trying to match "all" as a `contact_id` query param. Actually — the existing route is `GET /appointments` with `contact_id` as a query param, and this is `GET /appointments/all` with a different path, so ordering doesn't matter. But place it directly above the existing `list_appointments` function for readability.

Returns appointments **joined with Contact and AvailabilitySlot**:
```json
[{
  "id": "uuid",
  "contact_id": "uuid",
  "contact_phone": "+15551234567",
  "contact_name": "John Doe",
  "slot_start": "2026-02-23T10:00:00+00:00",
  "slot_end": "2026-02-23T10:30:00+00:00",
  "status": "confirmed",
  "booked_at": "2026-02-22T15:00:00+00:00"
}]
```

**Implementation:**
```python
query = (
    select(Appointment, Contact, AvailabilitySlot)
    .join(Contact, Appointment.contact_id == Contact.id)
    .join(AvailabilitySlot, Appointment.slot_id == AvailabilitySlot.id)
)
if status:
    query = query.where(Appointment.status == status)
query = query.order_by(AvailabilitySlot.start_time.asc()).offset(offset).limit(limit)
```

**Contact name construction** (use this pattern everywhere you display a name):
```python
def _display_name(contact: Contact) -> str:
    parts = [contact.first_name or "", contact.last_name or ""]
    name = " ".join(p for p in parts if p).strip()
    return name if name else contact.phone_number
```
Define this as a module-level helper function at the top of admin.py.

### Endpoint 3: Conversation States

```python
@router.get("/conversations", dependencies=[Depends(verify_admin_api_key)])
async def list_conversations(limit: int = 50, offset: int = 0) -> list[dict]:
```

**Route path:** `/api/conversations`

Returns conversation states **joined with Contact**:
```json
[{
  "id": "uuid",
  "contact_id": "uuid",
  "contact_phone": "+15551234567",
  "contact_name": "John Doe",
  "current_state": "showing_slots",
  "last_message_at": "2026-02-22T15:00:00+00:00",
  "updated_at": "2026-02-22T15:00:00+00:00"
}]
```

Use the same `_display_name()` helper for contact_name. Order by `updated_at DESC`.

### Endpoint 4: Availability Slots

```python
@router.get("/slots", dependencies=[Depends(verify_admin_api_key)])
async def list_slots(days_ahead: int = 7) -> list[dict]:
```

**Route path:** `/api/slots`

**IMPORTANT:** Return ALL slots in the date range, not just available ones. The frontend needs both to show a weekly calendar with available (green) and booked (red/strikethrough) slots.

```python
now = datetime.now(timezone.utc)
end = now + timedelta(days=days_ahead)
query = (
    select(AvailabilitySlot)
    .where(AvailabilitySlot.start_time >= now, AvailabilitySlot.start_time <= end)
    .order_by(AvailabilitySlot.start_time.asc())
)
```

Returns:
```json
[{
  "id": "uuid",
  "start_time": "2026-02-23T10:00:00+00:00",
  "end_time": "2026-02-23T10:30:00+00:00",
  "is_available": true,
  "slot_type": "standard"
}]
```

### Endpoint 5: Contact Detail (single contact)

```python
@router.get("/contacts/{contact_id}", dependencies=[Depends(verify_admin_api_key)])
async def get_contact(contact_id: str) -> dict:
```

**Route path:** `/api/contacts/{contact_id}`

**CRITICAL:** This route MUST be defined AFTER the existing `list_contacts` route (`GET /contacts`). FastAPI matches routes top-down — if this comes first, `GET /contacts?limit=100` would try to match `contact_id="?limit=100"` and fail. Place it immediately after `list_contacts`.

Returns the contact with their current conversation state:
```json
{
  "id": "uuid",
  "phone_number": "+15551234567",
  "first_name": "John",
  "last_name": "Doe",
  "timezone": "America/New_York",
  "opt_in_status": "opted_in",
  "created_at": "...",
  "updated_at": "...",
  "conversation_state": "idle",
  "last_message_at": null
}
```

Implementation: Query Contact by UUID, then LEFT JOIN or separate query for ConversationState where `contact_id` matches. If no conversation state exists, return `"conversation_state": "idle"` and `"last_message_at": null`.

### Phase 1 Verification

```bash
# 1. Existing tests still pass
pytest -q
# Expected: 43 passed

# 2. Rebuild and test new endpoints
docker compose up -d --build

# 3. Test each new endpoint
curl -s -H "X-API-Key: change-this-admin-key" http://localhost:8000/api/dashboard/stats | python3 -m json.tool
curl -s -H "X-API-Key: change-this-admin-key" http://localhost:8000/api/appointments/all | python3 -m json.tool
curl -s -H "X-API-Key: change-this-admin-key" http://localhost:8000/api/conversations | python3 -m json.tool
curl -s -H "X-API-Key: change-this-admin-key" http://localhost:8000/api/slots | python3 -m json.tool
curl -s -H "X-API-Key: change-this-admin-key" http://localhost:8000/api/contacts/00000000-0000-0000-0000-000000000000 2>&1 | head -5
# The last one should return 404 (no contact with that UUID) — not a 500 or 422

# 4. Fix any issues before committing
```

### Phase 1 Commit
```bash
git add app/api/admin.py
git commit -m "feat(api): add dashboard stats, all-appointments, conversations, slots, and contact detail endpoints"
git push origin main
```

---

## Phase 2: React Admin Scaffold

### Step 2.1 — Create Vite project

Run from the **project root directory** (the directory containing `app/`, `tests/`, `docker-compose.yml`):

```bash
npm create vite@latest admin -- --template react-ts
cd admin
npm install
npm install react-router-dom                        # runtime dependency — NOT -D
npm install -D tailwindcss @tailwindcss/vite         # dev dependencies
cd ..
```

**IMPORTANT:** `react-router-dom` is a runtime dependency. Do NOT use the `-D` flag for it.

### Step 2.2 — Clean up Vite boilerplate

Delete these generated files that we don't need:
```bash
rm admin/src/App.css
rm admin/src/assets/react.svg
rm admin/public/vite.svg
```

### Step 2.3 — Configure Vite

Replace `admin/vite.config.ts` entirely with:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: '/admin/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### Step 2.4 — Configure Tailwind CSS v4

Replace `admin/src/index.css` entirely with:
```css
@import "tailwindcss";
```

Do NOT create a `tailwind.config.js` — Tailwind v4 does not use one.

### Step 2.5 — Update admin entry point

Replace `admin/src/main.tsx` with:
```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter basename="/admin">
      <App />
    </BrowserRouter>
  </StrictMode>,
)
```

**CRITICAL:** `basename="/admin"` is required. Without it, all `<Link>` and `useNavigate()` calls will generate wrong paths.

### Step 2.6 — Update Dockerfile for multi-stage build

Replace the **entire** `Dockerfile` with:
```dockerfile
# Stage 1: Build admin frontend
FROM node:20-alpine AS admin-build
WORKDIR /build
COPY admin/package.json admin/package-lock.json ./
RUN npm ci
COPY admin/ ./
RUN npm run build

# Stage 2: Python application
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

COPY . /app

# Copy built admin frontend from stage 1
COPY --from=admin-build /build/dist /app/admin/dist

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2.7 — Update .dockerignore

Add these lines to `.dockerignore`:
```
admin/node_modules
admin/.git
admin/src
admin/public
admin/index.html
admin/vite.config.ts
admin/tsconfig*.json
```

This keeps the Docker context small — only `admin/package.json` and `admin/package-lock.json` are sent for the npm build stage. The COPY admin/ in the node stage grabs everything it needs before the Python stage applies the ignore rules.

Wait — actually, `.dockerignore` applies to the entire build context. We need admin source files for the node stage. Remove the admin-specific ignores and just keep:
```
admin/node_modules
```

### Step 2.8 — Serve admin SPA from FastAPI

Add to `app/main.py`. Insert these lines **AFTER** the `app.include_router(admin_router)` line and **BEFORE** the middleware:

```python
# --- Admin SPA static serving ---
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

_admin_dist = os.path.join(os.path.dirname(__file__), "..", "admin", "dist")
if os.path.isdir(_admin_dist):
    _admin_assets = os.path.join(_admin_dist, "assets")
    if os.path.isdir(_admin_assets):
        app.mount("/admin/assets", StaticFiles(directory=_admin_assets), name="admin-assets")

    @app.get("/admin")
    async def admin_root():
        return FileResponse(os.path.join(_admin_dist, "index.html"))

    @app.get("/admin/{rest_of_path:path}")
    async def admin_spa(rest_of_path: str):
        return FileResponse(os.path.join(_admin_dist, "index.html"))
```

**Why this placement matters:** FastAPI matches routes top-down. The `/admin/{rest_of_path:path}` catch-all must not interfere with `/api/*` routes. Since the routers are included first and `/admin` doesn't overlap with `/api`, this is safe. The `mount` for static assets takes priority over the catch-all for `/admin/assets/*` paths.

**Do NOT remove** the existing static mount for `/static` or the `/demo` redirect if they exist.

### Step 2.9 — Verify scaffold

```bash
cd admin
npm run build
# Must complete with 0 errors
cd ..

# Rebuild Docker
docker compose up -d --build

# Test admin route
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin
# Should return 200

pytest -q
# Must still show 43 passed
```

### Phase 2 Commit
```bash
git add -A
git commit -m "build(admin): scaffold Vite + React + TypeScript + Tailwind v4 with Docker multi-stage build"
git push origin main
```

---

## Phase 3: API Client + App Shell

### Step 3.1 — Create typed API client

Create `admin/src/api.ts` with the following:

1. **`getApiKey()` / `setApiKey()` / `clearApiKey()` / `hasApiKey()`** — sessionStorage wrappers
2. **`apiFetch<T>(path, options)`** — generic fetch wrapper that:
   - Prepends `/api` to path
   - Adds `Content-Type: application/json` and `X-API-Key` headers
   - On 401: clears API key, reloads page
   - On non-ok: throws Error with status + statusText
   - Returns `response.json()` typed as `T`
3. **`api` object** with methods for every endpoint:
   - `getDashboardStats(): Promise<DashboardStats>`
   - `getContacts(limit?, offset?): Promise<Contact[]>`
   - `getContact(id): Promise<ContactDetail>`
   - `getAllAppointments(limit?, offset?, status?): Promise<AppointmentFull[]>`
   - `getContactAppointments(contactId): Promise<Appointment[]>`
   - `getMessages(contactId): Promise<Message[]>`
   - `getConversations(limit?, offset?): Promise<Conversation[]>`
   - `getCampaigns(limit?, offset?): Promise<Campaign[]>`
   - `createCampaign(data): Promise<CampaignCreateResponse>`
   - `updateCampaign(id, data): Promise<CampaignUpdateResponse>`
   - `getSlots(daysAhead?): Promise<Slot[]>`
   - `getHealth(): Promise<HealthStatus>`
   - `simulate(phone, message): Promise<SimulateResponse>`
4. **TypeScript interfaces** for all request/response types

**Full type definitions to include:**

```typescript
export interface DashboardStats {
  contacts_total: number;
  contacts_opted_in: number;
  contacts_opted_out: number;
  appointments_today: number;
  appointments_upcoming: number;
  appointments_total: number;
  messages_today: number;
  messages_inbound_today: number;
  messages_outbound_today: number;
  conversations_active: number;
  campaigns_active: number;
  campaigns_total: number;
}

export interface Contact {
  id: string;
  phone_number: string;
  first_name: string | null;
  last_name: string | null;
  timezone: string;
  opt_in_status: string;
  created_at: string;
}

export interface ContactDetail extends Contact {
  updated_at: string;
  conversation_state: string;
  last_message_at: string | null;
}

export interface Appointment {
  id: string;
  contact_id: string;
  slot_id: string;
  status: string;
  booked_at: string;
  cancelled_at: string | null;
  rescheduled_from_id: string | null;
}

export interface AppointmentFull {
  id: string;
  contact_id: string;
  contact_phone: string;
  contact_name: string;
  slot_start: string;
  slot_end: string;
  status: string;
  booked_at: string;
}

export interface Message {
  id: string;
  contact_id: string | null;
  direction: string;   // "inbound" | "outbound"
  body: string;
  sms_sid: string | null;
  status: string;
  error_code: string | null;
  campaign_id: string | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  contact_id: string;
  contact_phone: string;
  contact_name: string;
  current_state: string;
  last_message_at: string | null;
  updated_at: string;
}

export interface Campaign {
  id: string;
  name: string;
  status: string;
  scheduled_at: string | null;
  total_recipients: number;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
  reply_count: number;
  created_at: string;
}

export interface CampaignCreateResponse {
  id: string;
  name: string;
  status: string;
  total_recipients: number;
}

export interface CampaignUpdateResponse {
  id: string;
  name: string;
  status: string;
  scheduled_at: string | null;
}

export interface Slot {
  id: string;
  start_time: string;
  end_time: string;
  is_available: boolean;
  slot_type: string;
}

export interface HealthStatus {
  status: string;
  db: string;
  redis: string;
}

export interface SimulateResponse {
  responses: string[];
  conversation_state: string;
  context: Record<string, unknown>;
}
```

### Step 3.2 — Create shared UI helpers

Create `admin/src/utils.ts`:

```typescript
/** Build display name from nullable first/last, fallback to phone */
export function displayName(contact: { first_name: string | null; last_name: string | null; phone_number?: string }): string {
  const parts = [contact.first_name || '', contact.last_name || ''].filter(Boolean);
  const name = parts.join(' ').trim();
  return name || contact.phone_number || 'Unknown';
}

/** Format ISO datetime to readable string */
export function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

/** Format ISO datetime to short date */
export function formatShortDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString();
}

/** Format ISO datetime to time only */
export function formatTime(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
```

### Step 3.3 — Replace App.tsx with app shell

Replace `admin/src/App.tsx` (Vite already created one — **replace** it, don't create a second file):

**Requirements:**

1. **Auth gate (no API key stored):**
   - Centered card on gray background
   - Title: "SMS Chatbot Admin"
   - Subtitle: "Enter your admin API key to continue"
   - Password input field for API key
   - "Connect" button
   - On submit: call `api.getHealth()` with the entered key
   - If 401 → show red error "Invalid API key"
   - If network error → show red error "Cannot reach server"
   - If 200 → store key with `setApiKey()`, set authenticated state to true

2. **Main layout (authenticated):**
   - **Sidebar** (width: 256px, fixed, full height, `bg-gray-900 text-white`):
     - Top: "SMS Chatbot" title in white, small "Admin Panel" subtitle in gray
     - Navigation items, each with icon + label:
       - 📊 Dashboard → `/admin/`
       - 👥 Contacts → `/admin/contacts`
       - 📅 Appointments → `/admin/appointments`
       - 💬 Conversations → `/admin/conversations`
       - 📣 Campaigns → `/admin/campaigns`
       - 🧪 Simulator → `/admin/simulator`
       - 🗓️ Slots → `/admin/slots`
     - Active item: `bg-gray-800` background
     - Bottom: "Logout" button that calls `clearApiKey()` and reloads
   - **Main content area** (flex-1, `bg-gray-50`, `overflow-y-auto`):
     - Top bar (h-16, white, border-bottom): page title on left, health dot on right
     - Health dot: green pulsing circle if healthy, red if unhealthy. Poll `/api/health` every 30 seconds.
     - Content area with padding below top bar
   - **Mobile responsive:** On `< md` (768px), sidebar becomes a slide-out drawer triggered by a hamburger button in the top bar

3. **Routes** (inside `<Routes>`):
   ```
   /              → <Dashboard />
   /contacts      → <Contacts />
   /contacts/:id  → <ContactDetail />
   /appointments  → <Appointments />
   /conversations → <Conversations />
   /campaigns     → <Campaigns />
   /simulator     → <Simulator />
   /slots         → <Slots />
   ```
   Note: No `/admin` prefix in route paths because `basename="/admin"` is set on `<BrowserRouter>`.

4. **Create placeholder page components** in `admin/src/pages/` — one file per page, each exporting a default function component that renders `<div><h1 className="text-2xl font-bold">Page Name</h1><p>Coming soon</p></div>`. Files:
   - `Dashboard.tsx`, `Contacts.tsx`, `ContactDetail.tsx`, `Appointments.tsx`, `Conversations.tsx`, `Campaigns.tsx`, `Simulator.tsx`, `Slots.tsx`

### Step 3.4 — Verify

```bash
cd admin
npm run build          # 0 errors
npx tsc --noEmit       # 0 errors
cd ..
docker compose up -d --build
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin  # 200
pytest -q              # 43 passed
```

### Phase 3 Commit
```bash
git add -A
git commit -m "feat(admin): add app shell with routing, sidebar nav, auth gate, and API client"
git push origin main
```

---

## Phase 4: Dashboard Page

Replace `admin/src/pages/Dashboard.tsx`.

### Design:

1. **Top row: 4 stat cards** in a responsive grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6`):
   - "Today's Appointments" — `appointments_today` — blue accent
   - "Active Conversations" — `conversations_active` — orange accent
   - "Messages Today" — `messages_today` (subtitle: `↑{inbound} ↓{outbound}`) — purple accent
   - "Total Contacts" — `contacts_total` (subtitle: `{opted_in} active`) — green accent
   - Each card: white bg, rounded-lg, shadow-sm, border, colored left border (4px), big number (text-3xl font-bold), label (text-sm text-gray-500), subtitle line

2. **Second row: 2 columns** (`grid-cols-1 lg:grid-cols-2 gap-6`):
   - **Left card: "Upcoming Appointments"**
     - Fetch from `api.getAllAppointments(5, 0, 'confirmed')`
     - Show table: Contact (name or phone, clickable → `/admin/contacts/:id`), Time (formatted slot_start), Status badge
     - If empty: "No upcoming appointments"
   - **Right card: "Active Conversations"**
     - Fetch from `api.getConversations(10)`
     - Filter client-side to only show `current_state !== 'idle'`
     - Show list: Contact phone (clickable → `/admin/contacts/:id`), state badge, last message time
     - If all idle: "No active conversations"

3. **Auto-refresh:** Use `useEffect` with `setInterval` at 15 seconds. Clear interval on unmount. Show a subtle "Last updated: HH:MM:SS" text.

4. **Loading state:** Show pulsing placeholder cards while data loads.

5. **Error state:** Show red banner at top with error message and "Retry" button.

### Phase 4 Verify & Commit
```bash
cd admin && npm run build && npx tsc --noEmit && cd ..
pytest -q
git add -A
git commit -m "feat(admin): add dashboard page with live stats and activity panels"
git push origin main
```

---

## Phase 5: Contacts List + Contact Detail

### Step 5.1 — Replace `admin/src/pages/Contacts.tsx`

1. **Filter bar:** Row with text input (placeholder "Search by phone number...") + dropdown (All, Opted In, Opted Out, Pending). Client-side filtering.
2. **Table:**
   - Columns: Phone Number, Name (use `displayName()`), Status (badge), Timezone, Created (formatted)
   - Status badge colors: opted_in → green bg, opted_out → red bg, pending → yellow bg
   - Rows are clickable → navigate to `/admin/contacts/${contact.id}`
   - Hover state: `bg-gray-50`
3. **Pagination:** "Load More" button at bottom. Start with limit=50, increment offset by 50. Disable button when fewer results than limit returned.
4. **Empty state:** "No contacts found" centered.

### Step 5.2 — Replace `admin/src/pages/ContactDetail.tsx`

Uses `useParams()` to get `id` from URL. Makes 3 API calls on mount:
1. `api.getContact(id)` → contact info + conversation state
2. `api.getMessages(id)` → message history
3. `api.getContactAppointments(id)` → appointments

**Layout:**

1. **Header bar:** Back button (← Contacts), contact name + phone number, opt-in status badge, timezone
2. **Two columns** (`grid-cols-1 lg:grid-cols-3 gap-6`):
   - **Left column (2/3): "Conversation History"**
     - Chat bubble display — **REVERSE the messages array** (API returns newest-first, display oldest-first at top)
     - Inbound messages: left-aligned, gray bubble (`bg-gray-100`)
     - Outbound messages: right-aligned, blue bubble (`bg-blue-500 text-white`)
     - Below each outbound message: small text showing delivery status (e.g., "delivered" in green, "failed" in red, "simulated" in gray). If error_code, show it.
     - Timestamp under each bubble (text-xs text-gray-400)
     - Auto-scroll to bottom on load
   - **Right column (1/3): "Details"**
     - **Conversation State card:** Current state badge + last message time
     - **Appointments card:** List of appointments, each showing: status badge, booked_at date. If cancelled, show cancelled_at. Ordered by booked_at desc.
     - Empty state: "No appointments"

### Phase 5 Verify & Commit
```bash
cd admin && npm run build && npx tsc --noEmit && cd ..
pytest -q
git add -A
git commit -m "feat(admin): add contacts list with search/filter and contact detail with chat history"
git push origin main
```

---

## Phase 6: Appointments Page

Replace `admin/src/pages/Appointments.tsx`.

1. **Filter bar:** Status dropdown (All, Confirmed, Cancelled, Rescheduled). Selecting a filter calls `api.getAllAppointments(50, 0, selectedStatus)`.
2. **Table:**
   - Columns: Contact (name + phone, clickable → `/admin/contacts/:id`), Date/Time (format `slot_start` as "Mon Feb 23, 10:00 AM"), Duration (calculate from slot_start to slot_end in minutes, show "30 min"), Status (badge: confirmed=green, cancelled=red, rescheduled=yellow), Booked (formatted `booked_at`)
   - Default sort: by slot_start ascending (upcoming first) — this is already the API default
3. **Pagination:** "Load More" button, same pattern as Contacts.
4. **Empty state:** "No appointments found"

### Phase 6 Verify & Commit
```bash
cd admin && npm run build && npx tsc --noEmit && cd ..
pytest -q
git add -A
git commit -m "feat(admin): add appointments page with status filtering"
git push origin main
```

---

## Phase 7: Campaigns Page

Replace `admin/src/pages/Campaigns.tsx`.

1. **Header row:** Page title + "New Campaign" button (right-aligned)
2. **Create form** (shown/hidden by button toggle, or always visible at top):
   - Name: text input (required)
   - Message Template: textarea, 4 rows (required). Helper text: "Use {first_name} and {last_name} for personalization"
   - "Create Campaign" submit button
   - On submit: call `api.createCampaign({name, message_template, recipient_filter: {}})`, then refetch list
3. **Campaign cards** (grid or stacked list):
   - Each card shows: Name (bold), Status badge (draft=gray, scheduled=blue, active=green, paused=yellow, completed=gray-dark), Created date
   - Stats line: "Recipients: X | Sent: X | Delivered: X | Failed: X | Replies: X"
   - **Visual delivery bar:** A horizontal stacked bar showing sent/delivered/failed proportions with colored segments (green=delivered, blue=sent-but-not-delivered, red=failed). Only show if total_recipients > 0.
   - **Action buttons per status:**
     - draft → "Schedule" button. On click, show a `<input type="datetime-local">` and "Confirm" button. Calls `api.updateCampaign(id, {status: 'scheduled', scheduled_at: value})`
     - scheduled → "Activate" button. Calls `api.updateCampaign(id, {status: 'active'})`
     - active → "Pause" button. Calls `api.updateCampaign(id, {status: 'paused'})`
     - paused → "Resume" button. Calls `api.updateCampaign(id, {status: 'active'})`
4. **Empty state:** "No campaigns yet. Create one above."

### Phase 7 Verify & Commit
```bash
cd admin && npm run build && npx tsc --noEmit && cd ..
pytest -q
git add -A
git commit -m "feat(admin): add campaigns page with create form and lifecycle management"
git push origin main
```

---

## Phase 8: Conversations Page

Replace `admin/src/pages/Conversations.tsx`.

1. **Table:**
   - Columns: Contact (phone, clickable → `/admin/contacts/:id`), Name (displayName), State (colored badge), Last Message (formatted), Updated (formatted)
   - **State badge color map:**
     - `idle` → gray (`bg-gray-100 text-gray-800`)
     - `greeting` → blue (`bg-blue-100 text-blue-800`)
     - `showing_slots` → purple (`bg-purple-100 text-purple-800`)
     - `confirming_booking` → yellow (`bg-yellow-100 text-yellow-800`)
     - `confirmed` → green (`bg-green-100 text-green-800`)
     - `cancelling` → orange (`bg-orange-100 text-orange-800`)
     - `rescheduling` → yellow (`bg-yellow-100 text-yellow-800`)
     - default/unknown → gray
   - Click row → navigate to `/admin/contacts/:id`
2. **Auto-refresh:** Poll every 10 seconds with `setInterval`. Clear on unmount.
3. **Filter toggle:** "Show idle" checkbox (default OFF — hides idle conversations to focus on active ones). Client-side filter.

### Phase 8 Verify & Commit
```bash
cd admin && npm run build && npx tsc --noEmit && cd ..
pytest -q
git add -A
git commit -m "feat(admin): add conversations monitor with auto-refresh and state badges"
git push origin main
```

---

## Phase 9: Simulator Page

Replace `admin/src/pages/Simulator.tsx`.

Port the concept from `app/static/simulator.html` into React. This is NOT an iframe — rebuild it as a React component.

1. **Layout:** Centered card (max-w-lg, full height), designed to look like a phone screen
2. **Top bar:** Phone number input (default `+15551234567`) + conversation state badge
3. **Message area:** Scrollable div with chat bubbles
   - User messages: right-aligned, blue (`bg-blue-500 text-white rounded-2xl rounded-br-sm`)
   - Bot messages: left-aligned, gray (`bg-gray-200 text-gray-900 rounded-2xl rounded-bl-sm`)
   - Show timestamps below each bubble
   - Auto-scroll to bottom when new messages appear (use `useRef` + `scrollIntoView`)
4. **Input area:** Text input + Send button (blue). Enter key also sends.
   - On send: add user message to local state immediately, call `api.simulate(phone, message)`, then add bot response(s) to local state
   - Disable input while waiting for response. Show "..." typing indicator in a bot bubble.
5. **"Clear Chat" button** in top bar — clears the local message state only (conversation state in DB persists; this is fine for demo purposes)
6. **Error handling:** If API call fails, show error in a red system message bubble

### Phase 9 Verify & Commit
```bash
cd admin && npm run build && npx tsc --noEmit && cd ..
pytest -q
git add -A
git commit -m "feat(admin): add SMS simulator with real-time AI responses"
git push origin main
```

---

## Phase 10: Slots (Availability) Page

Replace `admin/src/pages/Slots.tsx`.

1. **Week navigation:** "← Previous Week" / current week range text / "Next Week →" buttons
   - Track current week start date in state (default: start of current week, Monday)
   - Fetch slots with `api.getSlots(daysAhead)` where daysAhead covers the displayed week. For previous weeks, you'll need to adjust — actually, the API only supports `days_ahead` from now. For simplicity: only show current week forward. Disable "Previous Week" if it would go before today.
2. **Week grid:** 7 columns (Mon-Sun), each showing the date header and a vertical list of time slots
   - Group fetched slots by date (parse `start_time` into local date)
   - Each slot shown as a small card:
     - Available: green left border, white bg, shows time range (e.g., "10:00 AM - 10:30 AM")
     - Booked (is_available=false): red left border, gray bg, strikethrough text
   - If no slots for a day: show "No slots" in gray italic
3. **Stats summary** above grid: "X available / Y booked / Z total this week"

### Phase 10 Verify & Commit
```bash
cd admin && npm run build && npx tsc --noEmit && cd ..
pytest -q
git add -A
git commit -m "feat(admin): add weekly availability slots viewer"
git push origin main
```

---

## Phase 11: Visual Polish Pass

Go through EVERY page and component and apply these rules:

### Design Tokens (use consistently)
```
Cards:          bg-white rounded-lg shadow-sm border border-gray-200 p-6
Page titles:    text-2xl font-bold text-gray-900 mb-6
Section titles: text-lg font-semibold text-gray-900 mb-4
Tables:         w-full text-left text-sm
Table headers:  bg-gray-50 text-xs uppercase text-gray-500 font-medium px-4 py-3
Table cells:    px-4 py-3 border-b border-gray-100
Table hover:    hover:bg-gray-50 cursor-pointer (if clickable)
Badges:         inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
Primary btn:    bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium
Secondary btn:  bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 px-4 py-2 rounded-lg text-sm
Danger btn:     bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium
```

### Fix list:
- [ ] All pages have consistent padding (`p-6` or `p-8` in the main content area)
- [ ] All loading states show subtle pulse animation (`animate-pulse` on placeholder divs)
- [ ] All error states show red banner with retry button
- [ ] All empty states are centered with gray text and helpful message
- [ ] All tables have horizontal scroll wrapper on mobile (`overflow-x-auto`)
- [ ] All clickable rows have `cursor-pointer` and hover state
- [ ] All dates use the `formatDate()` or `formatShortDate()` utils consistently
- [ ] All contact names use `displayName()` consistently
- [ ] Sidebar mobile drawer works (hamburger button visible on `< md`)
- [ ] All `useEffect` cleanup: `setInterval` cleared, no memory leaks
- [ ] No console.log or console.error left in production code (use them during debug, remove after)

### Phase 11 Verify & Commit
```bash
cd admin && npm run build && npx tsc --noEmit && cd ..
pytest -q
git add -A
git commit -m "style(admin): apply consistent design tokens, fix responsive layout, add loading/error states"
git push origin main
```

---

## Phase 12: Final Build + Integration Test

### Step 12.1 — Full build check
```bash
cd admin
npx tsc --noEmit          # 0 type errors
npm run build             # 0 build errors, 0 warnings
cd ..
```

### Step 12.2 — Python test check
```bash
pytest -q                 # 43 passed (or more if you added endpoint tests)
```

### Step 12.3 — Docker integration
```bash
docker compose down
docker compose up -d --build
# Wait for healthy
sleep 10
```

### Step 12.4 — Endpoint smoke tests
```bash
API_KEY="change-this-admin-key"

# Health
curl -sf http://localhost:8000/api/health | python3 -m json.tool

# Admin SPA loads
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin)
[ "$STATUS" = "200" ] && echo "✓ Admin SPA" || echo "✗ Admin SPA returned $STATUS"

# Dashboard stats
curl -sf -H "X-API-Key: $API_KEY" http://localhost:8000/api/dashboard/stats | python3 -m json.tool

# All appointments
curl -sf -H "X-API-Key: $API_KEY" http://localhost:8000/api/appointments/all | python3 -m json.tool

# Conversations
curl -sf -H "X-API-Key: $API_KEY" http://localhost:8000/api/conversations | python3 -m json.tool

# Slots
curl -sf -H "X-API-Key: $API_KEY" http://localhost:8000/api/slots | python3 -m json.tool

# Contact detail (use a known contact ID from /api/contacts, or test 404)
curl -s -H "X-API-Key: $API_KEY" http://localhost:8000/api/contacts/00000000-0000-0000-0000-000000000000
# Should return 404, not 500

# Simulator
curl -sf -H "X-API-Key: $API_KEY" -X POST http://localhost:8000/api/simulate/inbound \
  -H "Content-Type: application/json" \
  -d '{"phone_number":"+15559999999","message":"hello"}' | python3 -m json.tool
```

### Step 12.5 — Fix any failures

If anything failed in 12.1-12.4, fix it now. Iterate until everything passes.

```bash
git add -A
git commit -m "fix(admin): resolve final build and integration issues"
git push origin main
```

---

## Phase 13: README + Final Commit

Add this section to `README.md`:

```markdown
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
\```bash
# Start the backend
docker compose up -d

# Start the admin dev server (hot reload, API proxied to :8000)
cd admin
npm install
npm run dev
# Open http://localhost:5173/admin
\```

### Production
The admin frontend is automatically built into the Docker image via multi-stage build. Access at `http://your-host/admin`.

### Authentication
Enter your `ADMIN_API_KEY` (from `.env`) at the login screen.
```

```bash
git add -A
git commit -m "docs: add admin dashboard documentation to README"
git push origin main
```

---

## Summary of All Commits (13 total)

| # | Commit Message | Files Changed |
|---|---------------|---------------|
| 1 | `feat(api): add dashboard stats, all-appointments, conversations, slots, and contact detail endpoints` | `app/api/admin.py` |
| 2 | `build(admin): scaffold Vite + React + TypeScript + Tailwind v4 with Docker multi-stage build` | `admin/*`, `Dockerfile`, `.dockerignore`, `app/main.py` |
| 3 | `feat(admin): add app shell with routing, sidebar nav, auth gate, and API client` | `admin/src/*` |
| 4 | `feat(admin): add dashboard page with live stats and activity panels` | `admin/src/pages/Dashboard.tsx` |
| 5 | `feat(admin): add contacts list with search/filter and contact detail with chat history` | `admin/src/pages/Contacts.tsx`, `ContactDetail.tsx` |
| 6 | `feat(admin): add appointments page with status filtering` | `admin/src/pages/Appointments.tsx` |
| 7 | `feat(admin): add campaigns page with create form and lifecycle management` | `admin/src/pages/Campaigns.tsx` |
| 8 | `feat(admin): add conversations monitor with auto-refresh and state badges` | `admin/src/pages/Conversations.tsx` |
| 9 | `feat(admin): add SMS simulator with real-time AI responses` | `admin/src/pages/Simulator.tsx` |
| 10 | `feat(admin): add weekly availability slots viewer` | `admin/src/pages/Slots.tsx` |
| 11 | `style(admin): apply consistent design tokens, fix responsive layout, add loading/error states` | `admin/src/**` |
| 12 | `fix(admin): resolve final build and integration issues` | Various |
| 13 | `docs: add admin dashboard documentation to README` | `README.md` |

## Final Verification Checklist

Before considering this complete, ALL of these must be true:

- [ ] `pytest -q` → 43+ tests pass
- [ ] `cd admin && npx tsc --noEmit` → 0 type errors
- [ ] `cd admin && npm run build` → 0 errors
- [ ] `docker compose up -d --build` → all 4 containers healthy (app, worker, db, redis)
- [ ] `curl http://localhost:8000/api/health` → `{"status":"green",...}`
- [ ] `curl http://localhost:8000/admin` → 200 with HTML content
- [ ] Browser: `/admin` → login screen renders
- [ ] Enter API key `change-this-admin-key` → dashboard loads with stat cards
- [ ] Click every sidebar link → all 7 pages render without console errors
- [ ] Dashboard: stat cards show numbers (may be 0 if DB is empty)
- [ ] Contacts: table renders (may be empty)
- [ ] Simulator: type "hello" and send → bot responds with AI-generated text
- [ ] Mobile: resize browser to 375px width → sidebar becomes hamburger menu, content stacks
- [ ] Existing routes still work: `/api/health`, `/demo`, `/webhooks/sms/inbound`
