# User Manual

## 1. Login
1. Open `/accounts/login/`
2. Enter username and password.
3. Access is granted based on assigned role.

## 2. Role Workflows
- Admin: manage users, aircraft, crew, and system configuration via Admin/API.
- Flight Operations Officer: submit flight logs from `Operations > Flight Log`.
- Maintenance Officer: submit maintenance logs from `Maintenance` and track alerts.
- Commander: view dashboard analytics and download reports.
- Auditor: read-only access to dashboards and reports.

## 3. Digital Flight Logbook
1. Go to `/operations/flight-logs/new/`.
2. Complete aircraft, pilot, crew, mission, route, hours, and fuel.
3. Submit. Dashboard metrics update in real time.

## 4. Telemetry Logging (`FlightData`)
1. Use the API endpoint `/api/flight-data/` to log live telemetry per flight.
2. Required telemetry fields: timestamp, altitude, speed, engine temperature, fuel level, heading.
3. Telemetry updates trigger real-time dashboard sync events.

## 5. Maintenance + Predictive Alerts
1. Go to `/maintenance/logs/new/`.
2. Record total flight hours and component condition.
3. If hours exceed threshold, a maintenance alert is generated automatically.

## 6. Dashboard
- View live cards for aircraft availability, flights today, active missions, alerts, and crew availability.
- Dashboard syncs using WebSockets for multi-base operations.

## 7. Reports
- Download Daily Flight, Weekly Maintenance, and Aircraft Utilization reports in PDF/XLSX.

## 8. Audit Trail
- Critical actions are logged with user, timestamp, and checksum chain.
