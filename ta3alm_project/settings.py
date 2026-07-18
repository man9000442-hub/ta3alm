"""
Django settings for ta3alm_project project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from django.utils.translation import gettext_lazy as _

# ==========================================================
# المسارات الأساسية
# ==========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# تحميل ملف .env
load_dotenv(BASE_DIR / '.env')

# ==========================================================
# الإعدادات الأساسية (Core Settings)
# ==========================================================
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set. Check your .env file.")

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1'
).split(',')

# ==========================================================
# التطبيقات المثبتة (Installed Apps)
# ==========================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    # Third party
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'cloudinary_storage',
    'cloudinary',
    'robots',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    # Local Apps
    'core',
    'accounts',
    'teachers',
    'students',
    'exams',
    'centers',
    'assistants',
    'bot_api',
    'dashboard_admin',   # ✅ لوحة الإدارة المستقلة
]

AUTH_USER_MODEL = 'accounts.User'

# ==========================================================
# Cache — locmem للتطوير، Redis للإنتاج
# ==========================================================
REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "ta3alm-cache",
        }
    }

# ==========================================================
# Middleware
# ==========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'ta3alm_project.middleware.TokenAuthMiddleware',
    'ta3alm_project.middleware.BanMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'ta3alm_project.middleware.MaintenanceMiddleware',
]

# ==========================================================
# Django REST Framework
# ==========================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# ==========================================================
# CORS — تحديد النطاقات المسموح بها (لا wildcard في الإنتاج)
# ==========================================================
CORS_ALLOW_ALL_ORIGINS = DEBUG  # True فقط في التطوير المحلي

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://127.0.0.1:3000'
    ).split(',')
    if origin.strip()
]

# ==========================================================
# إعدادات الأمان (Security Settings)
# ==========================================================
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
X_FRAME_OPTIONS = 'DENY'

CSRF_TRUSTED_ORIGINS = [
    'https://ta3alm.online',
    'https://www.ta3alm.online',
    'https://ta3alm-production.up.railway.app',
]

# ==========================================================
# Authentication Backends
# ==========================================================
AUTHENTICATION_BACKENDS = [
    'accounts.backends.MultiFieldAuthBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]



ROOT_URLCONF = 'ta3alm_project.urls'

# ==========================================================
# Templates
# ==========================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'ta3alm_project.wsgi.application'

# ==========================================================
# قاعدة البيانات (Database)
# ==========================================================
USE_SQLITE = os.environ.get('USE_SQLITE', 'True') == 'True'

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'postgres'),
            'USER': os.environ.get('DB_USER', ''),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {
                'connect_timeout': 10,
            },
        }
    }

# ==========================================================
# التحقق من كلمات المرور
# ==========================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==========================================================
# التدويل (Internationalization)
# ==========================================================
LANGUAGE_CODE = 'ar'
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'Africa/Cairo'

LANGUAGES = [
    ('ar', _('Arabic')),
    ('en', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# ==========================================================
# الملفات الثابتة والوسائط (Static & Media Files)
# ==========================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ==========================================================
# Cloudinary — تخزين الصور والميديا
# ==========================================================
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY':    os.environ.get('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
    'SECURE': True,
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'

# ==========================================================
# AllAuth — إعدادات المصادقة
# ==========================================================
SITE_ID = 1
PREPEND_WWW = not DEBUG

LOGIN_REDIRECT_URL = 'custom_login_redirect'
LOGOUT_REDIRECT_URL = '/'

ACCOUNT_LOGIN_METHODS = {'email'}                          # تسجيل الدخول بالإيميل فقط
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']  # الحقول المطلوبة عند التسجيل
ACCOUNT_EMAIL_VERIFICATION = 'none'                        # لا إيميل تفعيل
ACCOUNT_LOGOUT_ON_GET = False                              # ✅ حماية من CSRF على Logout

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_QUERY_EMAIL = True

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'EMAIL_AUTHENTICATION': True,
    }
}

# ==========================================================
# Paymob — بوابة الدفع
# ==========================================================
PAYMOB_API_KEY = os.environ.get('PAYMOB_API_KEY', '')
PAYMOB_INTEGRATION_ID = int(os.environ.get('PAYMOB_INTEGRATION_ID', '0'))
PAYMOB_IFRAME_ID = int(os.environ.get('PAYMOB_IFRAME_ID', '0'))
PAYMOB_WALLET_INTEGRATION_ID = int(os.environ.get('PAYMOB_WALLET_INTEGRATION_ID', '0'))

# ==========================================================
# Bot API Key
# ==========================================================
BOT_API_KEY = os.environ.get('BOT_API_KEY', '')
if not BOT_API_KEY and not DEBUG:
    raise ValueError("BOT_API_KEY environment variable is not set.")

# ==========================================================
# Logging (تسجيل الأحداث)
# ==========================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO' if DEBUG else 'WARNING',
            'propagate': False,
        },
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
