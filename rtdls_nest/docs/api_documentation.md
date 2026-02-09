# API Documentation

Base URL: `/api`

## Auth
- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

## Users (Admin)
- `GET /users`
- `POST /users`
- `PATCH /users/:id`

## Operations
- `GET/POST /operations/bases`
- `GET/POST /operations/crew`
- `GET/POST /operations/aircraft`
- `GET/POST /operations/flight-logs`

## Maintenance
- `GET/POST /maintenance/logs`
- `GET /maintenance/alerts`
- `PATCH /maintenance/alerts/:id/resolve`

## Dashboard
- `GET /dashboard/metrics`
- WebSocket namespace: `/dashboard`

## Reports
- `GET /reports/daily-flight?format=pdf|xlsx`
- `GET /reports/weekly-maintenance?format=pdf|xlsx`
- `GET /reports/aircraft-utilization?format=json|pdf|xlsx`

## Audit Logs
- `GET /audit-logs?limit=200`
