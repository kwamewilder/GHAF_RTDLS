from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local .env automatically for dev/IDE runs (without requiring manual export).
ENV_FILE = BASE_DIR / '.env'
if ENV_FILE.exists():
    for raw_line in ENV_FILE.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)

SECRET_KEY = os.getenv('SECRET_KEY', 'development-only-secret-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

raw_allowed_hosts = os.getenv('ALLOWED_HOSTS')
if raw_allowed_hosts:
    ALLOWED_HOSTS = [h.strip() for h in raw_allowed_hosts.split(',') if h.strip()]
else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']
    if DEBUG:
        ALLOWED_HOSTS = ['*']

render_external_hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_external_hostname and render_external_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_external_hostname)

if not DEBUG and SECRET_KEY == 'development-only-secret-key':
    raise ImproperlyConfigured('SECRET_KEY must be set in production.')

if not DEBUG and not raw_allowed_hosts and not render_external_hostname:
    raise ImproperlyConfigured('ALLOWED_HOSTS must be set in production.')

default_csrf_origins = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Common remote IDE preview/tunnel domains for thesis demo environments.
if DEBUG:
    default_csrf_origins.extend(
        [
            'https://*.githubpreview.dev',
            'https://*.app.github.dev',
            'https://*.gitpod.io',
        ]
    )

raw_csrf_trusted_origins = os.getenv('CSRF_TRUSTED_ORIGINS')
if raw_csrf_trusted_origins:
    CSRF_TRUSTED_ORIGINS = [
        origin.strip()
        for origin in raw_csrf_trusted_origins.split(',')
        if origin.strip()
    ]
else:
    CSRF_TRUSTED_ORIGINS = default_csrf_origins

if render_external_hostname:
    render_origin = f'https://{render_external_hostname}'
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'drf_spectacular',
    'channels',
    'accounts',
    'operations',
    'maintenance',
    'dashboard',
    'reports_app',
    'audittrail',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'audittrail.middleware.CurrentUserAuditMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'rtdls.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'rtdls.wsgi.application'
ASGI_APPLICATION = 'rtdls.asgi.application'

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url

    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=not DEBUG),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

REDIS_URL = os.getenv('REDIS_URL')
if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [REDIS_URL]},
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Accra'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# Prevent hard failures if a referenced static asset is missing from the manifest.
# Useful for demo deployments where branding files can be swapped late.
WHITENOISE_MANIFEST_STRICT = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'login'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_RATES': {
        'login': os.getenv('DRF_LOGIN_THROTTLE_RATE', '10/minute'),
    },
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'GAF RTDLS API',
    'DESCRIPTION': 'Real-time data logging system API for Ghana Air Force flight operations.',
    'VERSION': '1.0.0',
}

RECAPTCHA_SITE_KEY = os.getenv('RECAPTCHA_SITE_KEY', '').strip()
RECAPTCHA_SECRET_KEY = os.getenv('RECAPTCHA_SECRET_KEY', '').strip()
RECAPTCHA_VERIFY_URL = os.getenv('RECAPTCHA_VERIFY_URL', 'https://www.google.com/recaptcha/api/siteverify').strip()
RECAPTCHA_TIMEOUT_SECONDS = int(os.getenv('RECAPTCHA_TIMEOUT_SECONDS', '5'))
raw_recaptcha_enabled = os.getenv('RECAPTCHA_ENABLED')
if raw_recaptcha_enabled is None:
    RECAPTCHA_ENABLED = bool(RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY)
else:
    RECAPTCHA_ENABLED = raw_recaptcha_enabled.lower() == 'true'

if RECAPTCHA_ENABLED and (not RECAPTCHA_SITE_KEY or not RECAPTCHA_SECRET_KEY):
    raise ImproperlyConfigured('RECAPTCHA_ENABLED=True requires RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY.')

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 60 * 60 * 8
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 3600 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

REPORTS_FLIGHT_ID_OPTIONS_LIMIT = max(1, int(os.getenv('REPORTS_FLIGHT_ID_OPTIONS_LIMIT', '40')))
