from decouple import config
from .base import *
from .test import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

BASE_URL = config("BASE_URL_DEV")