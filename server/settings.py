"""
Django settings for the Transportation Portal project.
"""

import os, sys, logging

# Load environment settings with:
# set -a; source .env; set +a

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('TP_SECRET', default='ThisShouldBeChanged1!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('TP_DEBUG', default='false') == 'true'

#ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS").split(" ")
ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    # Stock apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',

    # Third party apps
    'corsheaders',
    'social_django',
    'oauth2_provider',
    'rest_framework_social_oauth2',
    'crispy_forms',
    'django_tables2',
    'django_tables2_column_shifter',
    'django_filters',
    'widget_tweaks',
    'tempus_dominus',
    'phone_field',
    'django_bootstrap_breadcrumbs',

    # Local apps
    'transportation'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'server.urls'


# Templates

CRISPY_TEMPLATE_PACK = 'bootstrap4'

DJANGO_TABLES2_TEMPLATE = 'django_tables2/bootstrap4.html'


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
                'social_django.context_processors.backends',  # <--
                'social_django.context_processors.login_redirect', # <--
            ],
        },
    },
]

TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'templates'),)


WSGI_APPLICATION = 'server.wsgi.application'


# Sites Framework
SITE_ID = 1


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('DB_NAME', default='transportation'),
        'USER': os.environ.get('DB_USER', default='postgres'),
        'PASSWORD': os.environ.get('DB_PASS', default='password'),
        'HOST': os.environ.get('DB_HOST', default='localhost'),
        'PORT': os.environ.get('DB_PORT', default=5432),
    }
}


# Cache
# https://docs.djangoproject.com/en/3.0/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Logging
# https://docs.djangoproject.com/en/3.0/topics/logging/
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#     'formatters': {
#         'standard': {
#             'format': '[%(levelname)s] [%(asctime)s] %(module)s %(name)s.%(funcName)s:%(lineno)s - %(message)s'
#         },
#     },
#     'handlers': {
#         'stdout': {
#             'class': 'logging.StreamHandler',
#             'stream': sys.stdout,
#             'formatter': 'standard',
#         },
#         'file': {
#             'class': 'logging.handlers.RotatingFileHandler',
#             'level': 'DEBUG',
#             'filename': '/app/log/transportation-portal/transportation.log',
#             'maxBytes': 1024*1024*5, # 5 MB
#             'backupCount': 5,
#             'formatter': 'standard',
#         },
#         'django_handler': {
#             'level':'INFO',
#             'class':'logging.handlers.RotatingFileHandler',
#             'filename': '/app/log/transportation-portal/django.log',
#             'maxBytes': 1024*1024*5, # 5 MB
#             'backupCount': 5,
#             'formatter':'standard',
#         }
#     },
#     'loggers': {
#         'transportation': {
#             'handlers': ['file','stdout'],
#             'level': 'DEBUG',
#             'propagate': True,
#         },
#         'django': {
#             'handlers': ['django_handler'],
#             'level': 'INFO',
#             'propagate': False
#         }
#     }
# }


AUTH_USER_MODEL = 'transportation.User'

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    'social_core.backends.azuread.AzureADOAuth2',
]

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/sign-in/'

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = os.environ.get('TP_LANG', default='en-us')

TIME_ZONE = os.environ.get('TP_TZ', default='UTC')

TEMPUS_DOMINUS_LOCALIZE = False

DATETIME_INPUT_FORMATS = ['%m/%d/%Y %I:%M %p', ]

DATE_INPUT_FORMATS = ['%m/%d/%Y', ]

TIME_INPUT_FORMATS = ['%I:%M %p', ]

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATIC_URL = '/static/'


if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', default='localhost')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', default=None)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASS', None)
EMAIL_PORT = os.environ.get('EMAIL_PORT', default=25)
EMAIL_USE_TLS = os.environ.get('EMAIL_TLS', default='false') == 'true'
TP_DEFAULT_FROM_EMAIL = os.environ.get('TP_FROM_EMAIL', default=EMAIL_HOST_USER)


SOCIAL_AUTH_AZUREAD_OAUTH2_KEY = os.environ.get('AZUREAD_KEY', None)
SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET = os.environ.get('AZUREAD_SECRET', None)
SOCIAL_AUTH_AZUREAD_OAUTH2_WHITELISTED_DOMAINS = os.environ.get('AZUREAD_WHITELISTED_DOMAINS', '').split(',')
SOCIAL_AUTH_USER_MODEL = 'transportation.User'


SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details'
)
