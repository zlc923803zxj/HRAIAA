import os
from celery import Celery
from celery.schedules import crontab
from datetime import datetime, timedelta
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HRAIAA.settings')

# Force Django to load all applications.
import django
django.setup()

from ai_assistant.tasks import show_user_needs

app = Celery('HRAIAA')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(1800.0, show_user_needs.s(), name='analyze user needs every 30 minutes')

@app.task
def analyze_user_needs():
    from ai_assistant.models import CustomUser  # 将模型的导入语句移到这里
    from .tasks import analyze_user_interaction  # 将任务的导入语句移到这里

    all_users = CustomUser.objects.all()

    for user in all_users:
        if user.last_activity < datetime.now() - timedelta(minutes=30):
            analyze_user_interaction.delay(user)
