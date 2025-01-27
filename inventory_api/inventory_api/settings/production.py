from .base import *
from .test import *
from decouple import config, Csv

DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS_PROD", default="your-production-domain.com", cast=Csv())

BASE_URL = config("BASE_URL_PROD")