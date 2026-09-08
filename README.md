\# DevX
# DevX (Full Stack Prototype — No Database)

AI-powered mobile developer testing platform: a FastAPI backend plus a
dependency-free HTML/CSS/JS console, in one project.

## Quickest start

```bash
cd devx-backend
./start.sh
```

This creates a virtualenv, installs backend dependencies, copies
`.env.example` to `.env`, and launches both servers:

- Console: http://127.0.0.1:5500
- API + docs: http://127.0.0.1:8000/docs

Ctrl+C stops both. Everything below explains what `start.sh` does, for
when you want to run or deploy the pieces separately.

This is a **prototype**:
all data (users, sessions, metrics, interactions, screenshots, AI reports)
lives in an **in-memory store** (`app/store.py`) instead of PostgreSQL.
Restarting the server wipes all data. There is no Alembic, no `schema.sql`,
and no `DATABASE_URL` — none of that is needed for this version.

The rest of the architecture (layered services, JWT auth, Pydantic schemas,
rule-based AI engine) is written the way it would be with a real database
behind it, so swapping the in-memory store for PostgreSQL/SQLAlchemy later
is a contained change — see "Extending this" below.

## Architecture

```
app/
    main.py            FastAPI app, CORS, routers, health checks
    config.py           Settings (env vars)
    enums.py             SessionStatus, InteractionType, IssueType, Severity
    schemas.py           All Pydantic request/response models
    security.py          Password hashing, JWT issuing/verification, auth dependency
    store.py              In-memory "database" (dict-backed tables)
    exceptions.py         Custom exceptions + global JSON error handlers
    services/             Business logic (auth, session, metric, interaction,
                           screenshot, ai, replay)
    routers/               FastAPI routers/controllers, one per resource
tests/                    pytest suite covering every endpoint
```

Request flow: **router → service → store**. Routers never touch `store`
directly and never contain business logic; services never format HTTP
responses.

## Requirements

- Python 3.11+ (3.12 recommended)
- No database, Docker, or external services required

## Manual installation (backend)

```bash
cd devx-backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

```bash
cp .env.example .env
```

Edit `.env` if you want (at minimum, change `JWT_SECRET_KEY` for anything
beyond local testing):

```
APP_NAME=DevX Backend
DEBUG=true
JWT_SECRET_KEY=CHANGE_THIS_SECRET
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:3000,http://localhost:8081
```

## Running

```bash
uvicorn app.main:app --reload
```

- API base: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/health

## Running tests

```bash
pytest -v
```

Each test gets a fresh in-memory store (see `tests/conftest.py`), so tests
don't leak state into each other.

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | /api/auth/register | No | Register a new user |
| POST | /api/auth/login | No | Get a JWT access token |
| GET | /api/auth/profile | Yes | Get the current user |
| POST | /api/session/start | Yes | Start a test session |
| PUT | /api/session/end | Yes | End a test session |
| GET | /api/session/{session_id} | Yes | Get a session |
| POST | /api/metrics | Yes | Record a performance metric |
| GET | /api/metrics/session/{session_id} | Yes | List metrics for a session |
| POST | /api/interactions | Yes | Record a user interaction |
| GET | /api/interactions/session/{session_id} | Yes | List interactions (ordered) |
| POST | /api/screenshots | Yes | Record screenshot metadata |
| GET | /api/screenshots/session/{session_id} | Yes | List screenshot metadata |
| POST | /api/ai/analyze | Yes | Run rule-based analysis on a session |
| GET | /api/ai/report/{session_id} | Yes | Get stored AI reports |
| GET | /api/replay/{session_id} | Yes | Get chronological interaction replay |
| GET | /health | No | Liveness check |
| GET | /health/db | No | Store availability check (always up — no external DB) |

All authenticated endpoints expect `Authorization: Bearer <access_token>`.

## Example requests

**Register**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com", "password": "password123"}'
```

**Login**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "password123"}'
```

Response:

```json
{
  "success": true,
  "message": "Login successful",
  "data": { "access_token": "eyJ...", "token_type": "bearer" }
}
```

**Start a session** (replace `TOKEN`)

```bash
curl -X POST http://127.0.0.1:8000/api/session/start \
  -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"app_name": "Instagram", "device_model": "iQOO 13", "android_version": "15"}'
```

**Record a metric**

```bash
curl -X POST http://127.0.0.1:8000/api/metrics \
  -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID", "fps": 22, "memory_usage": 70, "battery_usage": 3, "cpu_usage": 65, "temperature": 39, "frame_drops": 12}'
```

**Run AI analysis**

```bash
curl -X POST http://127.0.0.1:8000/api/ai/analyze \
  -H "Authorization: Bearer TOKEN" -H "Content-Type: application/json" \
  -d '{"session_id": "SESSION_ID"}'
```

With the metric above (fps 22, frame_drops 12), this returns `PERFORMANCE`
and `FRAME_DROP` findings.

## Error format

```json
{ "success": false, "message": "Session not found", "error_code": "SESSION_NOT_FOUND" }
```

FastAPI validation errors are converted to the same shape with
`error_code: "VALIDATION_ERROR"`.

## Frontend (DevX Console)

`start.sh` runs this for you automatically. To run it by hand instead:

`frontend/` is a small dependency-free HTML/CSS/JS single-page app — no
npm, no build step — that exercises every endpoint above: register/login,
start/end sessions, record metrics/interactions/screenshots, run AI
analysis, and step through a replay.

Run the backend first (see above), then in a second terminal:

```bash
cd devx-backend/frontend
python3 -m http.server 5500
```

Open http://127.0.0.1:5500 — the "API base" field in the left rail already
points at `http://127.0.0.1:8000`, and `5500` is included in the backend's
default `CORS_ORIGINS`, so it should work immediately. If you serve the
frontend from a different port, either add it to `CORS_ORIGINS` in `.env`
and restart the backend, or just edit the API base field (CORS still
applies either way — it's enforced by the browser against the backend's
configured origins, not by this field).

Sessions you start are tracked client-side per browser tab (the backend
has no "list my sessions" endpoint by design) — refreshing the page clears
the session list, though the sessions themselves still exist in the
backend's in-memory store until it restarts.

## What I'd extend first

1. **Swap the in-memory store for real persistence.** `store.py` is the only
   place that knows data is in-memory. Replace it with SQLAlchemy models +
   a Postgres connection, and change each `service/*.py` to call a
   repository instead of `store.<table>` — the routers and schemas don't
   need to change at all.
2. **Wire a real LLM into `ai_service.py`.** `AnalysisEngine` is already an
   abstract interface; `RuleBasedAnalysisEngine` is the only implementation.
   Add e.g. `LLMAnalysisEngine` that calls the Anthropic/OpenAI API with the
   session's metrics/interactions and swap the instance at the bottom of
   the file.
3. **Real screenshot storage.** Right now `/api/screenshots` only stores
   metadata (as specified). Add actual file upload (S3/local disk) and
   return signed URLs.
4. **Pagination** on the list endpoints (`GET .../session/{id}`) once
   sessions can have thousands of metrics/interactions.
5. **Refresh tokens** — currently only short-lived access tokens exist;
   add a refresh-token flow so mobile clients aren't forced to re-login
   every `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`.
6. **Rate limiting / request size limits** on the ingestion endpoints
   (metrics/interactions), since a real mobile SDK could stream these at
   high frequency.
7. **A `GET /api/session` list endpoint** so the frontend (and any other
   client) can recover a user's sessions after a page refresh instead of
   relying on client-side tracking for the current tab.
