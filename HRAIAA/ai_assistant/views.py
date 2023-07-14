#from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse,HttpResponseRedirect
import openai
import json
import logging
from django.core import serializers
#from django.contrib.auth.models import User
from .models import Conversation, Message  # 引入新的 Message 模型
from django.contrib import messages
from django.contrib.auth import authenticate
import tiktoken
from django.contrib.auth import login
from django.urls import reverse
from ai_assistant.models import CustomUser
from django import forms
from ai_assistant.forms import CustomUserCreationForm
from django.contrib.auth.forms import UserCreationForm
from datetime import datetime
from .tasks import analyze_user_interaction, show_user_needs
from .utils import get_conversation_history_for_model
openai.api_key = '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'

logger = logging.getLogger(__name__)



def user_needs_view(request):
    # 获取所有的UserNeed模型，并将它们传递给模板
    user_needs = UserNeed.objects.all()
    return render(request, 'ai_assistant/user_needs.html', {'user_needs': [user_need.need for user_need in user_needs]})


# 超级用户登录视图函数
@csrf_exempt
def superuser_login(request):
    if request.method == 'POST':
        print(request.POST)  # 添加这行代码来打印 request.POST
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return HttpResponseRedirect(reverse('user_needs'))
        else:
            # 返回一个错误消息
            return JsonResponse({'success': False, 'error': '无效的超级用户用户名或密码'})
    else:
        form = AuthenticationForm()  # 创建一个表单实例
        return render(request, 'ai_assistant/houtaidenglu.html', {'form': form})

@csrf_exempt
def chat(request):
    conversation, created = Conversation.objects.get_or_create(user=request.user)  # 假设每个用户只有一个对话

    # 更新用户的最后活动时间
    request.user.last_activity = datetime.now()
    request.user.save()

    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        logger.info(f"Request body: {body_unicode}")

        if not body_unicode:
            logger.error("Received empty request body")
            return HttpResponse(status=400)

        try:
            data = json.loads(body_unicode)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return HttpResponse(status=400)

        message = data.get('message')
        conversation_history = data.get('conversation_history', [])

        messages = []
        print("Preparing messages for OpenAI API:")
        for msg in conversation_history:
            print(msg)
            messages.append({'role': msg['role'], 'content': msg['content']})

        messages.append({'role': 'user', 'content': message})

        # 定义一个函数来计算消息的token数量
        def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):
            try:
                encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                print("Warning: model not found. Using cl100k_base encoding.")
                encoding = tiktoken.get_encoding("cl100k_base")

            tokens_per_message = 4  # for gpt-3.5-turbo, every message follows {role/name}\n{content}\n
            tokens_per_name = -1  # if there's a name, the role is omitted

            num_tokens = 0
            for message in messages:
                num_tokens += tokens_per_message
                for key, value in message.items():
                    num_tokens += len(encoding.encode(value))
                    if key == "name":
                        num_tokens += tokens_per_name
            num_tokens += 3  # every reply is primed with assistant
            return num_tokens

        # 使用这个函数来计算消息的token数量

        new_message_tokens = num_tokens_from_messages([{'role': 'user', 'content': message}], model="gpt-3.5-turbo")
        buffer_tokens = 1000  # 预留1000个token给模型生成回复
        # 如果新消息的token数量超过了4096 - buffer_tokens，那么就不添加这个消息，并给出一个错误提示
        if new_message_tokens > 4096 - buffer_tokens:
            response = JsonResponse({
                'error': '您提交的消息太长，请重新加载对话并提交较短的内容。'
            }, status=400)
            response['Content-Type'] = 'application/json'
            return response
        history_tokens = num_tokens_from_messages(messages, model="gpt-3.5-turbo")



        # 如果添加新消息后的总token数量超过4096，移除最早的消息，直到总的token数量满足条件
        while history_tokens + new_message_tokens > 4096 - buffer_tokens:
            removed_message = messages.pop(0)
            history_tokens -= num_tokens_from_messages([removed_message], model="gpt-3.5-turbo")

            # 检查messages列表是否为空
            if not messages:
                response = JsonResponse({
                    'error': '您提交的消息太长，无法添加新的消息。请提交更短的内容。'
                }, status=400)
                response['Content-Type'] = 'application/json'
                return response

        # 使用更新后的消息列表请求API
        print("Sending updated messages to OpenAI API:")
        for msg in messages:
            print(msg)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        assistant_message = response['choices'][0]['message']['content']

        # 创建并保存Message对象
        user_message = Message(
            user=request.user,
            conversation=conversation,
            role='user',
            content=message,
            token_count=response['usage']['total_tokens'],
        )
        user_message.save()

        ai_message = Message(
            user=request.user,
            conversation=conversation,
            role='assistant',
            content=assistant_message,
            token_count=response['usage']['total_tokens'],
        )
        ai_message.save()

        conversation.chat_history = json.dumps(messages + [{'role': 'assistant', 'content': assistant_message}])
        conversation.save()

        return JsonResponse({
            'message': assistant_message,
            'message_id': ai_message.id
        })

    elif request.method == 'GET':
        conversation, created = Conversation.objects.get_or_create(user=request.user)
        messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        return render(request, 'ai_assistant/chat.html',
                      {'messages': messages, 'username': request.user.username})


def get_chat_history(request):
    if request.user.is_authenticated:
        conversation, created = Conversation.objects.get_or_create(user=request.user)
        messages = Message.objects.filter(conversation=conversation).order_by('created_at')
        chat_history = []
        for msg in messages:
            chat_history.append({
                'role': msg.role,
                'content': msg.content,
                'message_id': msg.id
            })
        return JsonResponse({'chat_history': chat_history})


class UserLoginView(LoginView):
    template_name = 'ai_assistant/login.html'

    def form_invalid(self, form):
        user = authenticate(username=self.request.POST['username'], password=self.request.POST['password'])
        if user is not None:
            error_message = '账户未注册'
        else:
            error_message = '用户名或密码错误'

        return JsonResponse({
            'success': False,
            'error': error_message,
        })

    def form_valid(self, form):
        super(UserLoginView, self).form_valid(form)
        return JsonResponse({
            'success': True,
        })


def home(request):
    return render(request, 'ai_assistant/home.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        username = request.POST.get('username')
        if CustomUser.objects.filter(username=username).exists():
            return JsonResponse({'status': 'fail', 'message': '名称已注册'})
        if form.is_valid():
            form.save()
            messages.success(request, '注册成功是否登录')
            return JsonResponse({'status': 'success'})
        else:
            # 如果表单无效，将错误信息返回给前端
            return JsonResponse({'status': 'fail', 'errors': form.errors.as_json()})
    else:
        form = CustomUserCreationForm()
    return render(request, 'ai_assistant/register.html', {'form': form})


def get_success_url(self):
    return reverse('chat')
