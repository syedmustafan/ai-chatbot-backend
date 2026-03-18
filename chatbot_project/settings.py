"""
Django settings for chatbot_project project.
"""

from pathlib import Path
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Empty SECRET_KEY from Secret Manager would break signing; never use blank.
_raw_secret = config('SECRET_KEY', default='') or ''
SECRET_KEY = _raw_secret.strip() or 'django-insecure-change-me-in-production'

DEBUG = config('DEBUG', default=True, cast=bool)

# Cloud Run: Host is e.g. *.run.app. Django does not treat literal "*" as "allow all".
_allowed_raw = config('ALLOWED_HOSTS', default='localhost,127.0.0.1')
_allowed_parts = [s.strip() for s in _allowed_raw.split(',') if s.strip()]
if _allowed_parts == ['*']:
    ALLOWED_HOSTS = ['.run.app', '127.0.0.1', 'localhost']
else:
    ALLOWED_HOSTS = _allowed_parts

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'chatbot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chatbot_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'chatbot_project.wsgi.application'

# Use DATABASE_URL (e.g. Cloud SQL PostgreSQL) if set; otherwise SQLite
# On Cloud Run, use /tmp for SQLite so the DB is writable (ephemeral)
import os
DATABASE_URL = (config('DATABASE_URL', default='') or '').strip()
if DATABASE_URL:
    # Cloud SQL via Unix socket (?host=/cloudsql/...) does not use TLS like a public IP connection.
    _use_ssl = '/cloudsql/' not in DATABASE_URL
    db = dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=_use_ssl,
    )
    db.setdefault('OPTIONS', {})
    # Fail fast so migrate cannot hang past Cloud Run startup (hung DB = no listener on PORT).
    if db.get('ENGINE') == 'django.db.backends.postgresql':
        db['OPTIONS'].setdefault('connect_timeout', 15)
    DATABASES = {'default': db}
else:
    sqlite_path = BASE_DIR / 'db.sqlite3'
    if os.environ.get('PORT'):  # Cloud Run sets PORT
        sqlite_path = Path('/tmp/db.sqlite3')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': sqlite_path,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS: allow frontend origins from env + any Vercel deployment (*.vercel.app)
CORS_ALLOWED_ORIGINS = config(
    'ALLOWED_ORIGINS',
    default='http://localhost:5174,http://localhost:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)
# Allow all Vercel deployment URLs (production and preview) so CORS works without updating ALLOWED_ORIGINS
CORS_ALLOWED_ORIGIN_REGEXES = [
    r'^https://[\w-]+\.vercel\.app$',
]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Optional: protect GET /api/leads/ — required when DEBUG=False; optional when DEBUG=True (local dev)
LEADS_API_KEY = (config('LEADS_API_KEY', default='') or '').strip()
