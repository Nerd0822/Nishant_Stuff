import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ.get("DJANGO_SETTINGS_MODULE", "SERVER.settings"))

app = Celery("raahi")
app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()