# Deployment Guide (Render / Railway)

## Build
```bash
npm install
npx prisma generate
npm run build
```

## Start
```bash
npx prisma migrate deploy
npm run start
```

## Required Environment Variables
- `NODE_ENV=production`
- `PORT=8000`
- `DATABASE_URL=<managed-postgres-url>`
- `JWT_SECRET=<strong-secret>`
- `JWT_EXPIRES_IN=12h`
- `CORS_ORIGIN=https://your-frontend-domain`

## Render Example
- Runtime: Node
- Build command:
  - `npm install && npx prisma generate && npm run build`
- Start command:
  - `npx prisma migrate deploy && npm run start`

## Railway/Fly.io
- Same env vars and commands
- Attach PostgreSQL service and set `DATABASE_URL`
