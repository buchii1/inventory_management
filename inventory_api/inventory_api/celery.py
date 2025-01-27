from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from decouple import config

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_api.settings')

app = Celery('inventory_api')
app.conf.broker_url = config("CELERY_BROKER_URL")
app.conf.result_backend = config("CELERY_RESULT_BACKEND")

# Set the broker connection retry on startup
app.conf.broker_connection_retry_on_startup = True

# Read config from Django settings with "CELERY" prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks from all installed apps.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
