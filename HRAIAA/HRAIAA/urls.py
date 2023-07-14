from django.contrib import admin
from django.urls import path
from ai_assistant.views import home, register, UserLoginView, chat, get_chat_history,show_user_needs,superuser_login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('chat/', chat, name='chat'),
    path('chat/history/', get_chat_history, name='chat_history'),  # 添加这一行
    path('user_needs/',show_user_needs, name='user_needs'),
    path('houtaidenglu/',superuser_login, name='superuser_login')
]
