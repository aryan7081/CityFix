# Scalability

## Current bottlenecks (honest MVP assessment)

| Area | Bottleneck | Symptom at scale |
|------|------------|------------------|
| Duplicate scan | In-Python Haversine over bbox candidates | CPU + memory as open issues grow |
| Dashboard aggregates | Full-table counts | Slow analytics under millions of rows |
| Monolith deploy | Single Django process | CPU-bound under heavy write spikes |
| Image storage | Local filesystem volume | Not multi-instance safe |
| Celery concurrency | Default low worker count | Notification lag |

## Near-term mitigations (still one codebase)

1. **Horizontal web workers** behind Nginx / gunicorn — sticky sessions unnecessary (JWT).
2. **Read replica** for analytics queries.
3. **PostGIS** + `earthdistance` / GiST indexes for geo; `pg_trgm` for text.
4. **Object storage** (S3) for images.
5. **Celery scale-out** — more workers; separate queues (`notifications`, `analytics`).
6. **Materialized views** or nightly rollups for dashboards.

## Extraction map (when justified)

| Module | Extract when | Pattern |
|--------|--------------|---------|
| `notifications` | High fan-out / multi-channel (SMS, push) | Already async; become Notification Service consuming events |
| `analytics` | Heavy OLAP | Event stream → warehouse |
| `issues` duplicates | City-wide volume | Dedicated scoring service + geo DB |
| `accounts` | SSO / multi-product identity | Auth service |

Prefer **events** (outbox → broker) over synchronous cross-service calls for status changes.

## What we deliberately did *not* add

- Kubernetes, Kafka, service mesh — complexity without traffic
- Fake “distributed” layers that aren’t used in the request path
- ML duplicate models — deterministic scoring is explainable in viva

## Capacity narrative for viva

> “Today one Postgres primary + Redis + N gunicorn/Celery workers handles a campus or small city pilot. The module boundaries mirror future services; we would split only when a domain’s scaling or ownership requires it.”
