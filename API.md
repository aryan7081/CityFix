# API Reference (`/api/v1`)

Interactive docs: [Swagger UI](http://localhost:8000/api/docs/)

Auth: `Authorization: Bearer <access_token>`

## Auth

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register/` | Public | Citizen registration |
| POST | `/auth/login/` | Public | JWT pair + user payload |
| POST | `/auth/refresh/` | Public | Refresh access token |
| GET/PATCH | `/auth/me/` | User | Current profile |

## Issues

| Method | Path | Roles | Description |
|--------|------|-------|-------------|
| GET | `/issues/` | All | List (scoped by role) |
| POST | `/issues/` | Citizen+ | Create; **409** with duplicate suggestions |
| POST | `/issues/duplicates/check/` | Auth | Dry-run duplicate scan |
| GET | `/issues/duplicates/` | Admin | Stored duplicate relations |
| GET | `/issues/{uuid}/` | Auth | Detail + timeline + images |
| POST | `/issues/{uuid}/support/` | Citizen | Support existing |
| POST | `/issues/{uuid}/transition/` | Admin/Staff | Lifecycle change |
| POST | `/issues/{uuid}/assign/` | Admin | Assign team (locked) |
| POST | `/issues/{uuid}/accept/` | Maintenance | Accept assignment |
| POST | `/issues/{uuid}/resolve/` | Admin/Staff | Resolve + optional image |
| POST | `/issues/{uuid}/priority/` | Admin | Manual priority override |

### Create issue body (multipart or JSON)

`title`, `description`, `category`, `severity`, `latitude`, `longitude`, `address?`, `image?`, `force?`

**409 response** when duplicates found and `force` is false:

```json
{
  "success": false,
  "duplicate_suggestions": [{ "public_id": "...", "score": 0.82, "distance_meters": 12.4 }],
  "message": "Possible duplicate issues found..."
}
```

## Teams

| Method | Path | Roles |
|--------|------|-------|
| GET/POST/PATCH | `/teams/` | List: auth; mutate: admin |

## Notifications

| Method | Path |
|--------|------|
| GET | `/notifications/` |
| GET | `/notifications/unread-count/` |
| POST | `/notifications/mark-all-read/` |
| POST | `/notifications/{id}/read/` |

## Analytics & health

| Method | Path | Notes |
|--------|------|-------|
| GET | `/analytics/dashboard/` | Admin; Redis cached; `?bypass_cache=1` |
| GET | `/analytics/public/` | Public summary |
| POST | `/analytics/cache/invalidate/` | Admin |
| GET | `/analytics/system-health/` | Runtime probes |
| GET | `/health/` | Liveness |

## Error shape

```json
{
  "success": false,
  "error": { "status_code": 400, "detail": "..." }
}
```

Pagination: `?page=1&page_size=20` → `{ count, next, previous, results }`.
