# API Documentation

Base URL: `/api/`
Authentication: Session or Token (`/api/users/login/`)

## Authentication
- `POST /api/users/login/`
- `POST /api/users/logout/`

## User Management (Admin)
- `GET /api/users/`
- `POST /api/users/`
- `GET /api/users/{id}/`
- `PATCH /api/users/{id}/`

## Operations
- `GET/POST /api/aircraft/`
- `GET/PATCH/DELETE /api/aircraft/{id}/`
- `GET/POST /api/bases/`
- `GET/POST /api/crew/`
- `GET/POST /api/pilots/`
- `GET/POST /api/flight-logs/`
- `GET/PATCH/DELETE /api/flight-logs/{id}/`
- `GET/POST /api/flight-data/`
- `GET/PATCH/DELETE /api/flight-data/{id}/`

## Maintenance
- `GET/POST /api/maintenance-logs/`
- `GET/PATCH/DELETE /api/maintenance-logs/{id}/`
- `GET /api/alerts/`
- `PATCH /api/alerts/{id}/`

## Reports
- `GET /reports/daily-flight/?format=pdf|xlsx`
- `GET /reports/weekly-maintenance/?format=pdf|xlsx`
- `GET /reports/aircraft-utilization/?format=pdf|xlsx|json`

## Live Dashboard
- WebSocket endpoint: `/ws/dashboard/`
- Events: `initial_state`, `flight_log_created`, `flight_data_logged`, `maintenance_alert`, `dashboard_refresh`

## API Schema
- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/swagger/`
- ReDoc: `/api/docs/redoc/`
