# Ghana Air Force RTDLS Prototype

Web-Based Real-Time Data Logging System (RTDLS) built for the thesis:

**Design and Development of a Web-Based Real-Time Data Logging System to Enhance Ghana Air Force Flight Operations**

## Stack
- Backend: Python 3, Django 4, Django REST Framework, Django Channels
- Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
- Database: PostgreSQL (cloud-ready), SQLite fallback for local demo
- Security: Django authentication, RBAC, CSRF, HTTPS-ready settings
- Deployment: Render / Railway / Fly.io compatible

## Core Modules Implemented
- Authentication + RBAC (Admin, Flight Ops, Maintenance, Commander, Auditor)
- Digital Flight Data Logging with dedicated Pilot entity, validation, and real-time dashboard refresh
- Telemetry capture (`FlightData`) for altitude, speed, engine temperature, fuel level, and heading
- Maintenance Logging with predictive threshold alerts
- Real-Time Dashboard over WebSockets (`/ws/dashboard/`)
- Live Ghana airspace map powered by OpenSky feed (`/dashboard/api/opensky/ghana/`)
- Reporting (Daily Flight, Weekly Maintenance, Aircraft Utilization) in PDF/XLSX
- Audit Trail for login/logout, role changes, creates/updates/deletes/views

## Quick Start
1. Create virtual environment and install dependencies:
   ```bash
   cd rtdls_project
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run migrations and create admin:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```
3. Start server (works for local and remote IDE port-forwarding):
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```
4. Optional demo seed:
   ```bash
   python manage.py seed_demo_data
   ```
5. Open:
   - Local machine: `http://127.0.0.1:8000/accounts/login/`
   - Remote IDE/container: forward port `8000` and open the forwarded URL
   - API Docs (Swagger): `/api/docs/swagger/`
   - Health check: `/healthz/`

## Deployment Quick Commands (Render/Railway)
```bash
pip install -r requirements.txt
python manage.py collectstatic --noinput
gunicorn rtdls.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-2} --timeout 120 --access-logfile - --error-logfile -
```

Render recommended:
- Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Pre-Deploy Command: `python manage.py migrate --noinput`
- Start Command: `gunicorn rtdls.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-2} --timeout 120 --access-logfile - --error-logfile -`

Required production env vars:
- `DEBUG=False`
- `SECRET_KEY=<secure-random>`
- `ALLOWED_HOSTS=<your-service>.onrender.com[,<custom-domain>]`
- `CSRF_TRUSTED_ORIGINS=https://<your-service>.onrender.com[,https://<custom-domain>]`
- `DATABASE_URL=<postgres-url>`
- `REDIS_URL=<redis-url>` (recommended for Channels)
- `RECAPTCHA_ENABLED=True`
- `RECAPTCHA_SITE_KEY=<google-recaptcha-site-key>`
- `RECAPTCHA_SECRET_KEY=<google-recaptcha-secret-key>`
- `DRF_LOGIN_THROTTLE_RATE=10/minute`
- `OPENSKY_STATES_URL=https://opensky-network.org/api/states/all`
- `OPENSKY_TIMEOUT_SECONDS=8`
- `OPENSKY_DEFAULT_SCOPE=africa` (`ghana`, `west_africa`, `africa`, `global`)
- `OPENSKY_SCOPES_JSON=<optional-json-to-override-map-scopes>`
- `OPENSKY_DEMO_FALLBACK=True` (shows simulated flights when OpenSky returns empty)
- `OPENSKY_USERNAME=<optional-opensky-username>`
- `OPENSKY_PASSWORD=<optional-opensky-password>`
- `REPORTS_FLIGHT_ID_OPTIONS_LIMIT=40`
- `ALLOW_DEMO_SEED=True` (required to run `seed_demo_data`)
- `DEMO_USER_PASSWORD=<optional-demo-password>`

Important for reCAPTCHA:
- Add your Render domain (`<your-service>.onrender.com`) and any custom domain in Google reCAPTCHA allowed domains.

## Demo Roles
- `admin`
- `flight_ops`
- `maintenance`
- `commander`
- `auditor`

## Project Structure
- `accounts/`: user model, auth flows, RBAC
- `operations/`: aircraft, base, crew, flight logs
- `maintenance/`: maintenance logs, predictive alerts
- `dashboard/`: live metrics + websocket consumer
- `reports_app/`: PDF/XLSX report generation
- `audittrail/`: tamper-resistant audit chain
- `docs/`: thesis defense deliverables

## Thesis Deliverables Included
- Architecture diagram: `docs/architecture.md`
- ER diagram: `docs/er_diagram.md`
- API documentation: `docs/api_documentation.md`
- User manual: `docs/user_manual.md`
- Test report: `docs/test_report.md`
- Deployment guide: `docs/deployment_guide.md`
