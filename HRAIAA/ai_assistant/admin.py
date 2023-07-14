from django.contrib import admin
from .models import Conversation, Message, UserNeed  # 引入新的 UserNeed 模型
from .models import CustomUser

admin.site.register(Conversation)
admin.site.register(Message)  # 在 admin 站点注册 Message 模型
admin.site.register(UserNeed)  # 在 admin 站点注册 UserNeed 模型
admin.site.register(CustomUser)# 在 admin 站点注册 CustomUser 模型