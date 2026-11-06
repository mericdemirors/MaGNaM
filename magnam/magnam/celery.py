import os
import logging
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "magnam.settings.development")

# Silence noisy libraries
for logger_name in [
    "pdfminer",
    "pdfminer.psparser",
    "pdfminer.pdfinterp",
    "pdfminer.converter",
    "PIL",
]:
    logging.getLogger(logger_name).setLevel(logging.WARNING)

app = Celery("magnam")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()