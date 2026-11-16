# Evaluation Guide — Live Demonstration Script

Prerequisites: `docker compose up --build` and open http://localhost:5174

---

## Scenario 1 — Duplicate Detection

1. Login as **citizen1** / `citizen123`.
2. Note seeded issue “Large pothole on MG Road” (or open My Issues).
3. Logout → login as **citizen2** / `citizen123`.
4. Go to **Report** and submit:
   - Title: `Pothole near MG Road bus stop`
   - Description: `Deep pothole by the bus stop on MG Road damaging vehicles`
   - Category: `POTHOLE`
   - Lat/Lng: `12.97165` / `77.59455`
5. API returns **409** with suggestions (UI shows amber panel).
6. Click **Support this issue** instead of forcing create.
7. Explain: geo proximity + category + text similarity; support increments `support_count` and refreshes priority — reduces duplicate work orders.

---

## Scenario 2 — Asynchronous Processing

1. As citizen, submit a unique issue (different location, e.g. lat `12.980000`).
2. Observe **immediate** success response / redirect.
3. Open Docker logs: `docker compose logs celery -f`
4. See `Notification created ... kind=ISSUE_REPORTED`.
5. Open **Notifications** — message appears without blocking the create request.
6. Explain: Redis broker + Celery worker; `enqueue_notification.delay()`.

---

## Scenario 3 — Caching

1. Login as **admin** / `admin123`.
2. Open **Dashboard**, then **System Health** — note cache hits/misses.
3. Click **Demo cache miss → hit** on Dashboard (or call twice):
   - `GET /api/v1/analytics/dashboard/?bypass_cache=1`
   - `GET /api/v1/analytics/dashboard/`
4. Backend logs show `CACHE MISS` then `CACHE HIT`.
5. Verify/assign any issue → invalidation log `CACHE INVALIDATE`.
6. Explain: TTL + explicit invalidation; not every endpoint is cached.

---

## Scenario 4 — Concurrency

1. As admin, open a **VERIFIED** issue (seed “Large pothole…” or verify one).
2. In two terminals (or Swagger), fire concurrent assigns:

```bash
TOKEN=<admin_access_token>
ID=<issue_uuid>
curl -X POST http://localhost:8000/api/v1/issues/$ID/assign/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"team_id":1}' &
curl -X POST http://localhost:8000/api/v1/issues/$ID/assign/ \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"team_id":2}' &
wait
```

3. Only **one active** `TeamAssignment` remains; status history shows reassignment.
4. Explain: `select_for_update` + partial unique constraint.

---

## Scenario 5 — Issue Lifecycle

1. Admin: REPORTED → Under review → Verify → Assign **Road Repair Unit**.
2. Login **staff1** / `staff123` → Accept → Mark resolved with notes.
3. Login **citizen1** → open issue → show full timeline.
4. Explain: validated state machine + append-only history.

---

## Scenario 6 — Failure Handling

1. Stop Redis: `docker compose stop redis`
2. Hit Dashboard / create issue — API should still respond (cache degraded).
3. System Health shows Redis `down`.
4. Restart Redis: `docker compose start redis`
5. Stop Celery: `docker compose stop celery` → create issue → API OK; notification delayed.
6. Start Celery → queued tasks process (retries/backoff configured on task).
7. Explain: never block UX on nonessential async; don’t swallow errors silently (logs + health).

---

## Talking points checklist

- [ ] Why modular monolith first
- [ ] Where business logic lives (services, not views)
- [ ] Index → query mapping
- [ ] Cache consistency story
- [ ] How this evolves toward services (see SCALABILITY.md)
