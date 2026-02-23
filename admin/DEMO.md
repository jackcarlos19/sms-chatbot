# Admin Dashboard – Demo

## Quick start

1. **Backend** (from repo root):
   ```bash
   docker compose up -d
   ```
   Backend runs at `http://localhost:8000`. The admin UI proxies `/api` to it.

2. **Admin UI** (from this folder):
   ```bash
   npm run dev
   ```
   Opens at **http://localhost:5173/admin/**

3. **Sign in**  
   Default credentials (from backend `.env` / `config.py`):
   - **Username:** `admin`
   - **Password:** `change-this-admin-password`  
   Or, if set: `ADMIN_PASSWORD` / `ADMIN_API_KEY` (legacy).

## What to demo

- **Dashboard** – Stats, recent appointments, active conversations
- **Contacts** – List, search, filter; open a contact for thread + edit + audit
- **Appointments** – Table/calendar, detail with notes, cancel, reschedule, audit trail
- **Waitlist** – Add entry, filter by status
- **Workflows** – New workflow (trigger, offset, template)
- **Campaigns** – New campaign (name, message)
- **Conversations** – Click a row → contact detail (thread)
- **Simulator** – Send test SMS, see bot response in logs
- **Admin Users** – Add user (username + role)
- **Slots** – Availability list
- **Header** – Health dot, theme toggle, profile menu → Log out

## 404 and errors

- Visit **http://localhost:5173/admin/does-not-exist** for the 404 page.
- Any uncaught React error shows the “Something went wrong” fallback with “Refresh page”.
