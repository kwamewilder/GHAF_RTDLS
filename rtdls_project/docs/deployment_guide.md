# Deployment Guide (Render - Demo Friendly)

## 1. Repository Setup
- Push `rtdls_project/` to GitHub.
- If your repository root is `GHAF_RTDLS/` (with app inside `rtdls_project/`), set Render **Root Directory** to `rtdls_project`.

## 2. Create PostgreSQL
- On Render: create PostgreSQL instance.
- Copy `DATABASE_URL`.

## 3. Create Web Service
- Runtime: Python
- Build Command:
  ```bash
  pip install -r requirements.txt && python manage.py collectstatic --noinput
  ```
- Pre-Deploy Command:
  ```bash
  python manage.py migrate --noinput
  ```
- Start Command:
  ```bash
  gunicorn rtdls.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-2} --timeout 120 --access-logfile - --error-logfile -
  ```
- Health Check Path:
  - `/healthz/`

## 4. Environment Variables
- `DEBUG=False`
- `SECRET_KEY=<secure-random>`
- `ALLOWED_HOSTS=<your-service>.onrender.com[,<custom-domain>]`
- `CSRF_TRUSTED_ORIGINS=https://<your-service>.onrender.com[,https://<custom-domain>]`
- `DATABASE_URL=<from-postgres-service>`
- `REDIS_URL=<render-key-value-url>` (recommended for Channels/WebSockets)
- `WEB_CONCURRENCY=2`
- `RECAPTCHA_ENABLED=True`
- `RECAPTCHA_SITE_KEY=<google-site-key>`
- `RECAPTCHA_SECRET_KEY=<google-secret-key>`
- `RECAPTCHA_VERIFY_URL=https://www.google.com/recaptcha/api/siteverify`
- `DRF_LOGIN_THROTTLE_RATE=10/minute`
- `REPORTS_FLIGHT_ID_OPTIONS_LIMIT=40`

## 5. HTTPS
- Render provides TLS automatically for hosted domains.
- App is configured with secure cookie + SSL redirect in production.

## 6. Post-Deploy
- Run `createsuperuser` using Render Shell.
- Create demo users for each role.
- Verify endpoints:
  - `/healthz/`
  - `/accounts/login/`
  - `/dashboard/`
  - `/api/docs/swagger/`

## 7. reCAPTCHA Domain Allowlist
- In Google reCAPTCHA admin, add:
  - `<your-service>.onrender.com`
  - your custom domain (if any)
- If this is missing, login page will show domain errors and captcha will fail.

## Railway / Fly.io
- Same env vars and build/start commands apply.
- Ensure PostgreSQL and Redis add-ons are attached.
