from django.urls import path
from .views import *

urlpatterns = [
    path('crontab/', manageCrontab.as_view(), name='crontab'),
    path('interval/', managerInterval.as_view(), name='interval'),
]