from __future__ import absolute_import, unicode_literals

# 这将确保 celery app 能在 Django 启动时被加载
from .celery import app as celery_app

__all__ = ('celery_app',)
