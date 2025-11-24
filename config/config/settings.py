"""
Django settings for Mahad Group Accounting Suite
File: config/settings.py
"""

from pathlib import Path
from datetime import timedelta
import os

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = 'django-insecure-f6fk)435xot49ya=pm2ib5$hx4&c=q-n6l5gaz(25_2$4!l!%d'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    
    # Local apps
    'authentications.apps.AuthenticationsConfig',  # Custom auth app
    'core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Custom middleware
    # Custom middleware
    'authentications.middleware.UserActivityMiddleware',
    'authentications.middleware.SecurityHeadersMiddleware',
    'authentications.middleware.AccountLockoutMiddleware',
    'authentications.middleware.EmailVerificationMiddleware',
]

# Custom User Model
AUTH_USER_MODEL = 'authentications.User'

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# Static & Media
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://localhost:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:3000',
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type', 'dnt', 'origin',
    'user-agent', 'x-csrftoken', 'x-requested-with',
]

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
}

# Simple JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'ISSUER': 'mahad-accounting',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# Email
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'your-email@gmail.com'
    EMAIL_HOST_PASSWORD = 'your-app-password'

DEFAULT_FROM_EMAIL = 'noreply@mahadgroup.com'
SERVER_EMAIL = DEFAULT_FROM_EMAIL
FRONTEND_URL = 'http://localhost:5173'

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 1209600
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

# Logging
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} - {message}', 'style': '{', 'datefmt': '%Y-%m-%d %H:%M:%S'},
        'simple': {'format': '[{levelname}] {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'level': 'INFO', 'class': 'logging.StreamHandler', 'formatter': 'simple'},
        'file': {'level': 'INFO', 'class': 'logging.handlers.RotatingFileHandler', 'filename': LOGS_DIR / 'django.log', 'maxBytes': 1024*1024*10, 'backupCount': 10, 'formatter': 'verbose'},
        'auth_file': {'level': 'DEBUG', 'class': 'logging.handlers.RotatingFileHandler', 'filename': LOGS_DIR / 'auth.log', 'maxBytes': 1024*1024*5, 'backupCount': 5, 'formatter': 'verbose'},
    },
    'loggers': {
        'django': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'django.request': {'handlers': ['file'], 'level': 'ERROR', 'propagate': False},
        'authentications': {'handlers': ['console', 'auth_file'], 'level': 'DEBUG' if DEBUG else 'INFO', 'propagate': False},
    },
    'root': {'handlers': ['console', 'file'], 'level': 'INFO'},
}

# Custom settings
SUPPORTED_CURRENCIES = ['INR', 'KES', 'AED', 'QAR', 'PHP', 'USD', 'EUR']
DEFAULT_CURRENCY = 'USD'
SUPPORTED_COUNTRIES = [('IN', 'India'), ('KE', 'Kenya'), ('AE', 'UAE'), ('QA', 'Qatar'), ('PH', 'Philippines')]
TAX_RATES = {'IN': 0.18, 'KE': 0.16, 'AE': 0.05, 'QA': 0.00, 'PH': 0.12}
FILE_UPLOAD_MAX_MEMORY_SIZE = 10*1024*1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10*1024*1024
ALLOWED_DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'jpg', 'jpeg', 'png', 'gif']
DATE_INPUT_FORMATS = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']

# Dev helpers
if DEBUG:
    try:
        import importlib
        if importlib.util.find_spec('debug_toolbar') is not None:
            debug_toolbar = importlib.import_module('debug_toolbar')
            INSTALLED_APPS += ['debug_toolbar']
            MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
            INTERNAL_IPS = ['127.0.0.1']
    except Exception:
        pass

print(f"""
╔══════════════════════════════════════════════════════════╗
║   Mahad Group Accounting Suite - Settings Loaded        ║
╠══════════════════════════════════════════════════════════╣
║   Environment: {'DEVELOPMENT' if DEBUG else 'PRODUCTION'} ║
║   Database: {DATABASES['default']['ENGINE'].split('.')[-1].upper()} ║
║   Email Backend: {'Console' if DEBUG else 'SMTP'}        ║
║   Frontend URL: {FRONTEND_URL}                           ║
╚══════════════════════════════════════════════════════════╝
""")
