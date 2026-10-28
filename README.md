# CityFix — Public Infrastructure Maintenance Management System

CityFix is a modular-monolith MVP for civic issue reporting, duplicate detection, prioritized maintenance assignment, and transparent lifecycle tracking.

## Stack

- **Backend:** Django + DRF + JWT + Celery + Redis + PostgreSQL
- **Frontend:** React + Vite + TypeScript + Tailwind + Axios
- **Infra:** Docker Compose

## Quick start (Docker)

Start **Docker Desktop**, then:

```bash
cp .env.example .env   # already present for local demo
docker compose up --build
```

> Production-shaped stack uses PostgreSQL + Redis + Celery. Keep Docker running for the full evaluation scenarios (cache, async, failure demos).

| Service   | URL                          |
|-----------|------------------------------|
| Frontend  | http://localhost:5174        |
| API       | http://localhost:8000/api/v1 |
| Swagger   | http://localhost:8000/api/docs/ |
| Admin     | http://localhost:8000/admin/ |
| Postgres  | localhost:5433 (mapped)      |

> Host ports: Postgres uses **5433** and Vite **5174** if 5432/5173 are already taken on your machine.

### Demo accounts (seeded automatically)

| Username  | Password    | Role         |
|-----------|-------------|--------------|
| admin     | admin123    | ADMIN        |
| citizen1  | citizen123  | CITIZEN      |
| citizen2  | citizen123  | CITIZEN      |
| staff1    | staff123    | MAINTENANCE  |
| staff2    | staff123    | MAINTENANCE  |

## Offline / no-Docker backend (SQLite)

Useful when Docker Desktop is unavailable. **Not** a substitute for the evaluation demo of Redis/Celery.

```bash
cd backend
source .venv/bin/activate
export CITYFIX_USE_SQLITE=1 CITYFIX_USE_LOCMEM_CACHE=1 CELERY_TASK_ALWAYS_EAGER=1
export DJANGO_SECRET_KEY=dev
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

## Local development (without full Compose)

```bash
# Terminal 1 — Postgres + Redis
docker compose up db redis

# Terminal 2 — API
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export POSTGRES_HOST=localhost REDIS_URL=redis://localhost:6379/0
export CELERY_BROKER_URL=redis://localhost:6379/1
export CELERY_RESULT_BACKEND=redis://localhost:6379/2
python manage.py migrate
python manage.py seed_data
python manage.py runserver

# Terminal 3 — Celery
cd backend && source .venv/bin/activate
celery -A config worker -l info

# Terminal 4 — Frontend
cd frontend && npm install && npm run dev
```

## Tests

```bash
cd backend && source .venv/bin/activate
export POSTGRES_HOST=localhost
python manage.py test issues
```

## Documentation

| Doc | Purpose |
|-----|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Component responsibilities |
| [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | HLD / LLD / trade-offs |
| [DATABASE.md](DATABASE.md) | Schema, indexes, ER |
| [API.md](API.md) | REST API reference |
| [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) | Live demo script |
| [SCALABILITY.md](SCALABILITY.md) | Bottlenecks & scale-out |

## System design concepts demonstrated

1. Modular monolith (domain apps + services)
2. Duplicate detection (geo + category + text)
3. Redis caching with hit/miss logging + invalidation
4. Celery async notifications
5. Atomic assignment with `select_for_update` + unique active constraint
6. Validated issue lifecycle + status history
7. JWT + role-based permissions
8. Health endpoints and graceful Redis degradation
