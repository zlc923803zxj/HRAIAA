from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.contrib.auth import get_user_model
class CustomUser(AbstractUser):
    last_activity = models.DateTimeField(auto_now=True)
# Conversation模型表示一次对话。对于一次对话，我们只需要知道参与者以及对话创建的时间。
class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)  # 这记录了对话创建的时间
    last_message_at = models.DateTimeField(auto_now=True)  # 这记录了对话的最后消息发送时间

# 新的Message模型表示一条消息。每条消息都属于一个对话，并有一个发送者。每个消息还包含了角色（用户或者助手），消息的内容，消息发送的时间，以及 token 数量。
class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)  # 这是与对话的关联
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)  # 新增的 role 字段
    content = models.TextField()  # 这是消息的内容
    created_at = models.DateTimeField(auto_now_add=True)  # 这记录了消息发送的时间
    token_count = models.IntegerField(default=0)  # 新增的 token_count 字段

# 表示用户的需求，包含了用户，对应的对话，需求内容，以及创建时间。
class UserNeed(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    need = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

