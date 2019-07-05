from __future__ import absolute_import

import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'couriersite.settings')

from django.conf import settings

app = Celery('couriersite')

app.config_from_object('django.conf:settings')

app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

#app configs
from django.apps import apps
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

app.conf.update(
    CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend',
)
