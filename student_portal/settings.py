"""
Django settings for student_portal project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
from corsheaders.defaults import default_headers

# Load environment variables from a .env file located at the project root
load_dotenv(os.path.join(Path(__file__).resolve().parent.parent, ".env"))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv("SECRET_KEY", "django-secret-key")
DEBUG = os.getenv("APP_DEBUG", "true").lower() in ("1", "true", "yes")

allowed_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "")
if allowed_hosts == "*":
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = allowed_hosts.split(",")

if DEBUG:
    ALLOWED_HOSTS.extend([
        '127.0.0.1',
        'localhost',
        '.localhost',
        '0.0.0.0',
        '*'
    ])

# Application definition - FIXED: Each app on its own line
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',  # FIXED: Separate line
    'drf_yasg',  # FIXED: Separate line
    'students',
    'storages',
    'health',
    'bank_admin',
    'student_admin',
]

AUTH_USER_MODEL = 'students.CustomUser'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    ## 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middlewares.authentication.AuthMiddleware',
]

ROOT_URLCONF = 'student_portal.urls'

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

WSGI_APPLICATION = 'student_portal.wsgi.application'

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DEFAULT_DB_NAME"),
        "USER": os.getenv("DEFAULT_DB_USER"),
        "PASSWORD": os.getenv("DEFAULT_DB_PASSWORD"),
        "HOST": os.getenv("DEFAULT_DB_HOST", "localhost"),
        "PORT": os.getenv("DEFAULT_DB_PORT", "5432"),
    }
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'student_portal.authentication.JWTAuth',
        # 'student_portal.authentication.NoAuth',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.MultiPartRenderer',
        'rest_framework.renderers.StaticHTMLRenderer',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_THROTTLE_RATES': {
        'public_bd_bank_list': '30/min',  # allow 30 requests per minute per IP
    },
}

# CORS settings
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ORIGIN_ALLOW_ALL = True
else:
    CORS_ORIGIN_WHITELIST = os.getenv("CORS_ALLOWED_ORIGINS").split(",")
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS").split(",")

CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME', 'priyo_pay_dev_docs')
GS_BUCKET_CREDENTIAL = os.getenv('GS_BUCKET_CREDENTIAL', 'priyo-pay-bucket.json')
GS_BUCKET_FILE_NAME_MAX_CHAR = 172

# Cache timeout for GCP URLs
GS_EXPIRATION = timedelta(hours=1)

# Django Storages settings
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

# Google Application Credentials (for django-storages)
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'priyo-pay-bucket.json')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'api': {
            'format': '{asctime} - {name} - {levelname} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'api'
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'students': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
# Enable Swagger conditionally
_enable_swagger_env = os.getenv("ENABLE_SWAGGER")
if _enable_swagger_env is None:
    IS_SWAGGER_ENABLED = DEBUG
else:
    IS_SWAGGER_ENABLED = _enable_swagger_env.lower() in ("1", "true", "yes")

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_DELTA = int(os.environ.get('JWT_EXPIRATION_DELTA', '86400'))

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # 1 hour
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),  # 1 week
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}
AUTH_API_BASE = os.getenv('AUTH_API_BASE')
AUTH_API_KEY = os.getenv('AUTH_API_KEY')

if not AUTH_API_BASE or not AUTH_API_KEY:
    raise ValueError("AUTH_API_BASE and AUTH_API_KEY must be set in environment variables")

PRIYOPAY_API_URL = os.getenv('PRIYOPAY_API_URL')
PRIYOPAY_API_KEY = os.getenv('PRIYOPAY_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
# Profile caching ( I wish to implement caching later on )
PROFILE_CACHE_PREFIX = "profile-"
PROFILE_CACHE_TTL = int(os.getenv('PROFILE_CACHE_TTL', 300))  # 5 minutes

# Swagger Configuration
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT Authorization header using the Bearer scheme. Format: "Bearer {token}"'
        }
    },
    'SECURITY_REQUIREMENTS': [],
    'USE_SESSION_AUTH': False,
    'LOGIN_URL': None,
    'LOGOUT_URL': None,
    'PERSIST_AUTH': True,
    'REFETCH_SCHEMA_WITH_AUTH': True,
    'REFETCH_SCHEMA_ON_LOGOUT': True,
    'DEFAULT_MODEL_RENDERING': 'example',
    'DEFAULT_MODEL_DEPTH': 2,
    'SUPPORTED_SUBMIT_METHODS': [
        'get', 'post', 'put', 'delete', 'patch'
    ],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'SHOW_COMMON_EXTENSIONS': True,
}

CORS_ALLOW_HEADERS = list(default_headers) + [
    "x-api-key",
    "device-fingerprint",
    "device-type"
]
