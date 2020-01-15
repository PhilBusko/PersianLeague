"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
DJANGO SETTINGS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


# CONFIG BASED ON HOST

import socket
import ipgetter
host = socket.gethostname()

if host.startswith('test'):
    DEBUG = True #False
    hostIP = ipgetter.myip()
    ALLOWED_HOSTS = [hostIP]
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'HOST': 'localhost',
            'PORT': '',
            'NAME': 'UFOdb',
            'USER': 'testor',
            'PASSWORD': '123qwe',
        }
    }
    
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'asgi_redis.RedisChannelLayer',
            'CONFIG': {
                'hosts': [('localhost', 6379)],
            },
            'ROUTING': 'app_proj.routing.channel_routing',
        }
    }
    
    # SECURE_SSL_REDIRECT = True
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True
    # SECURE_HSTS_SECONDS = 31536000
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    

elif host.startswith('prod'):
    DEBUG = False
    hostIP = ipgetter.myip()
    ALLOWED_HOSTS = [hostIP, 'lige-ma.com']
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'HOST': 'localhost',
            'PORT': '',
            'NAME': 'UFOdb',
            'USER': 'mastor',
            'PASSWORD': 'v2b1n4h5y6g7d8k9r0',
        }
    }
    
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'asgi_redis.RedisChannelLayer',
            'CONFIG': {
                'hosts': [('localhost', 6379)],
            },
            'ROUTING': 'app_proj.routing.channel_routing',
        }
    }
    
    # SECURE_SSL_REDIRECT = True
    # SESSION_COOKIE_SECURE = True
    # CSRF_COOKIE_SECURE = True
    # SECURE_HSTS_SECONDS = 31536000
    # SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


else:       # running on dev machine
    DEBUG = True
    ALLOWED_HOSTS = []
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'HOST': 'localhost',
            'PORT': '',
            'NAME': 'UFOdb',
            'USER': 'postgres',
            'PASSWORD': '123qwe',
        }
    }

    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'asgiref.inmemory.ChannelLayer',
            'ROUTING': 'app_proj.routing.channel_routing',
        },
    }


# WEBSERVER

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Build paths like this: os.path.join(settings.BASE_DIR, ...) ... must not start with /
#from django.conf import settings
EXPORT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..', "Exports"))

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "app_proj/static/")

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

SECRET_KEY = '2=x@(p3j9dib)ychr0#$$c)07iu(jin*la)kccvl_w-0fghy^2'
WSGI_APPLICATION = 'app_proj.wsgi.application'
INTERNAL_IPS = ('127.0.0.1',)


# APPLICATION 

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',    
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',  
    'django.contrib.sites',         # needed by allauth
    'djangosecure',
    'channels',
    'postman',
    'paypal.standard.ipn',
    'members',                      # before allauth to override templates
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    #'allauth.socialaccount.providers.facebook',
    'common',
    'football',
    'prediction',
    'central'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'djangosecure.middleware.SecurityMiddleware',
    'members.middleware.RequestMiddleware',     
)

from django.conf import global_settings
TEMPLATE_CONTEXT_PROCESSORS = list(
    global_settings.TEMPLATE_CONTEXT_PROCESSORS) + [
    'django.core.context_processors.request',           # allauth
    'central.models.central.context_profile',           # add rosters to every context
    'central.models.central.context_background',         
    #'django.contrib.auth.context_processors.auth',
    #'allauth.account.context_processors.account',
    #'allauth.socialaccount.context_processors.socialaccount',
    ]

ROOT_URLCONF = 'app_proj.urls'


# INTERNATIONALIZATION

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# LOGGING: CRITICAL, ERROR, WARNING, INFO and DEBUG

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,

    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    
    'formatters': {
        'simple': {	
            '()': 'common.utility.SimpleFmt'
        },
        'complete': {	
            '()': 'common.utility.CompleteFmt'
        },
    },
    
    'handlers': {
        'console': {
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'console_error': {
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'complete'
        },
        'logfile': {
            'class': 'logging.FileHandler',
            'filename': 'logfile.log',
            'formatter': 'complete'
        }
    },
    
    'loggers': {
        'progress': {
            'handlers': ['console'],
            'level': 'DEBUG',
         },
        'exception': {
            'handlers': ['console_error', 'logfile'],
            'level': 'WARNING',
        }
    }
}


# OTHERS

ADMINS = (('Sherwin Busko','lig3ma@gmail.com'))

MANAGERS = ADMINS


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
OTHER APP SETTINGS
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

# AUTH & ALLAUTH

AUTHENTICATION_BACKENDS = (
    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",
    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend"
)

SITE_ID = 1
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/home/'

SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'SCOPE': ['email', 'publish_stream'],
        'METHOD': 'js_sdk'  # instead of 'oauth2'
    }
}

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'        # users can login with username or email
ACCOUNT_EMAIL_REQUIRED = True                           # require each account to be associated with an email
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'                # 'mandatory' | 'optional' 
ACCOUNT_UNIQUE_EMAIL = True                             # one account per email address
ACCOUNT_SESSION_REMEMBER = False                        # remove remember checkbox from login form
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""                       # override allauth bullshit


# POSTMAN

POSTMAN_AUTO_MODERATE_AS = True         # disable all moderation
POSTMAN_DISALLOW_ANONYMOUS = True       # only registered users may send messages
POSTMAN_DISABLE_USER_EMAILING = True    # disable default mailings


# DJANGO E-MAIL

EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'postmaster@mg.lige-ma.com'
EMAIL_HOST_PASSWORD = 'cattacBLUE'
EMAIL_USE_TLS = True

# necessary for allauth emails
DEFAULT_FROM_EMAIL = "Lige Ma <no_reply@mg.lige-ma.com>"

# for dev, route emails to console
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# OTHERS

GEOIP_PATH = os.path.join(BASE_DIR, 'members/static/data_sets')

PAYPAL_TEST = False     # True is default


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
END OF FILE
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""