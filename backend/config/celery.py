"""
ETIP Backend — Celery Application
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("etip")

# Read config from Django settings, using the CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks from all registered apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
