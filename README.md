# celery_template
save celery settings for use faster :D
install reqs packages with 
```shell
pip install -r reqs.txt
```

create ```celery.py``` in root folder and add :
```python
from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
#TODO
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '<appName>.settings')
#TODO
app = Celery('<appName>')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
```

add celery app to ```__init__.py```:
```python
from __future__ import absolute_import

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app
__all__ = ('celery_app',)
```

add this settings to your ```settings.py```:
```python
INSTALLED_APPS = [
    .
    .
    .
    'django_celery_beat',
    'django_celery_results',
    .
    .
    .
]

BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERYBEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tehran'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'default'
CELERY_RESULT_EXTENDED = True
```

run command for create tables in database:
```shell
python manage.py migrate
```

add ```tasks.py``` to your each app and develop:
```python
from celery import shared_task
import sys
from loguru import logger

logger.add(sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>")
#TODO change name and queue
@shared_task(max_retries=5, name='<taskName>', queue='<queueName>')
def checkDate():
    logger.add("test__{time}.log")
    logger.info('Logger message')
    raise Exception ('<Error message>')
```

run celery worker with :
```shell
celery -A <appName> worker -Q <queueName> -l info
```

run celery-beat with :
```shell
celery -A <appName> beat -l info 
```

