# ETIP — Development Log

A running record of progress sessions, decisions, and challenges encountered during
the implementation of the Electricity Token Intermediary Platform.

---

## Session 1 — 2026-02-24

### Goal
Bootstrap the local development environment using Docker Compose.

### What Was Accomplished

| # | Task | Status |
|---|------|--------|
| 1 | Confirmed Docker Desktop is installed and available | ✅ |
| 2 | Identified missing `backend/.env` file (existed but was hidden from file search) | ✅ |
| 3 | Diagnosed `api` container not starting — root cause: build failure | ✅ |
| 4 | Fixed `pycairo` build failure by adding system dependencies to Dockerfile | ✅ |
| 5 | Successfully built all 4 Docker images | ✅ |
| 6 | Started all 5 containers (db, redis, api, celery_worker, flower) | ✅ |
| 7 | Ran all database migrations (`manage.py migrate`) | ✅ |
| 8 | Created Django superuser | ✅ |
| 9 | Verified Swagger API docs at `http://localhost:8000/api/docs/` | ✅ |
| 10 | Verified Flower (Celery monitoring) at `http://localhost:5555` | ✅ |

---

### Challenges & Fixes

#### 1. `docker init` nearly overwrote `docker-compose.yml`
- **What happened:** `docker init` was run in the project root, prompting to overwrite the existing `docker-compose.yml` with a generic template.
- **Fix:** Cancelled with `Ctrl+C` before any files were overwritten.

#### 2. `service "api" is not running` on `docker compose exec`
- **What happened:** `docker compose exec api ...` was run before `docker compose up -d`, so no containers existed yet.
- **Fix:** Always run `docker compose up -d` first.

#### 3. `version` attribute obsolete warning
- **What happened:** `docker-compose.yml` had `version: "3.9"` which is now ignored by modern Docker Compose.
- **Fix:** The line can be safely removed from `docker-compose.yml`.

#### 4. `pycairo` build failure (main blocker)
- **Root cause:** `xhtml2pdf` → `svglib` → `rlpycairo` → `pycairo` requires the `cairo` C library and `pkg-config` to compile from source. These were missing from `python:3.13-slim`.
- **Error:** `Run-time dependency cairo found: NO` / `Pkg-config for machine host machine not found`
- **Fix:** Added to `backend/Dockerfile`:
  ```dockerfile
  RUN apt-get update && apt-get install -y \
      libpq-dev \
      gcc \
      pkg-config \
      libcairo2-dev \
      && rm -rf /var/lib/apt/lists/*