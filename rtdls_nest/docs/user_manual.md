# User Manual

## Login
1. POST credentials to `/api/auth/login`.
2. Use returned JWT as `Authorization: Bearer <token>`.

## Role Capabilities
- ADMIN: manage users, aircraft, crew, bases.
- FLIGHT_OPS: create flight logs, view dashboards and reports.
- MAINTENANCE: create maintenance logs, resolve alerts.
- COMMANDER: view analytics/reports.
- AUDITOR: read-only logs/reports.

## Flight Logging
- Endpoint: `POST /api/operations/flight-logs`
- Required fields include aircraft, pilot, mission, datetime, hours, fuel, departure/arrival.

## Maintenance + Alerts
- Endpoint: `POST /api/maintenance/logs`
- If `totalFlightHours >= maintenanceThresholdHours`, alert is auto-generated.

## Dashboard
- REST metrics: `GET /api/dashboard/metrics`
- Realtime: connect socket to `/dashboard` with JWT token.

## Reports
- Daily Flight, Weekly Maintenance, Aircraft Utilization in PDF/XLSX.

## Audit Trail
- Endpoint: `GET /api/audit-logs`
- Audit records contain user/action/entity/timestamp and checksum chain.
