from .base import *
from .test import *
from decouple import config, Csv
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS_PROD", default="your-production-domain.com", cast=Csv())

# Fetch database credentials using python-decouple
DATABASES = {
    'default': dj_database_url.config(
        default=f"postgresql://postgres:{config('DB_PASSWORD')}@{config('DB_HOST')}:{config('DB_PORT')}/{config('DB_NAME')}",
        conn_max_age=600
    )
}

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

BASE_URL = config("BASE_URL_PROD")