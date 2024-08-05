from celery import Celery
import os

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance.settings')

# Create an instance of the Celery application.
app = Celery('finance')

# Configure the Celery application.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django app configs.
app.autodiscover_tasks()
