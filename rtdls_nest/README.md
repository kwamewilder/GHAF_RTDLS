# GAF RTDLS (NestJS + TypeScript Methodology)

Prototype: Web-Based Real-Time Data Logging System for Ghana Air Force Flight Operations.

## Stack
- Backend: Node.js, NestJS, TypeScript
- Real-time: Socket.IO WebSocket gateway
- Database: PostgreSQL + Prisma ORM
- Auth: JWT + role guards (RBAC)
- Reports: PDF (`pdfkit`) + XLSX (`exceljs`)
- Deployment: Render / Railway / Fly.io

## Implemented Roles
- `ADMIN`
- `FLIGHT_OPS`
- `MAINTENANCE`
- `COMMANDER`
- `AUDITOR`

## Core Modules
- Auth + RBAC (`/api/auth/*`)
- Flight operations (`/api/operations/*`)
- Maintenance + predictive alerts (`/api/maintenance/*`)
- Live dashboard metrics (`/api/dashboard/metrics`, WebSocket namespace `/dashboard`)
- Audit trail (`/api/audit-logs`)
- Reports (`/api/reports/*`)

## Local Run
1. Install dependencies:
```bash
npm install
```
2. Configure env:
```bash
cp .env.example .env
```
3. Start PostgreSQL (Docker):
```bash
docker compose up -d db
```
4. Generate Prisma client + migrate + seed:
```bash
npx prisma generate
npx prisma migrate dev --name init
npm run seed
```
5. Start API:
```bash
npm run start:dev
```

API base: `http://localhost:8000/api`

## Demo Users (after seed)
Password for all: `DemoPass123!`
- `admin_demo`
- `flight_ops_demo`
- `maintenance_demo`
- `commander_demo`
- `auditor_demo`

## Key Endpoints
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/dashboard/metrics`
- `POST /api/operations/flight-logs`
- `POST /api/maintenance/logs`
- `GET /api/maintenance/alerts`
- `GET /api/reports/daily-flight?format=pdf|xlsx`
- `GET /api/reports/weekly-maintenance?format=pdf|xlsx`
- `GET /api/reports/aircraft-utilization?format=json|pdf|xlsx`

## WebSocket (Realtime Dashboard)
- Namespace: `/dashboard`
- Auth: JWT token via `socket.auth.token`
- Events emitted:
  - `dashboard.initial`
  - `dashboard.refresh`
  - `flight_log_created`
  - `maintenance.alert`
  - `alert_resolved`

## Deployment Notes
- Set environment variables from `.env.example`
- Use managed PostgreSQL on Render/Railway/Fly
- Run `prisma migrate deploy` during build/start

See docs in `docs/` for architecture, ER diagram, API doc, test report, and deployment guide.
