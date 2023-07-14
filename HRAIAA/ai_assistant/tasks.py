from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Conversation
import openai
#from .models import Message  # 你需要引入 Message 模型
import logging
from .utils import get_conversation_history_for_model
from django.contrib.auth import get_user_model
from HRAIAA.celery import app
# 创建一个日志记录器
logger = logging.getLogger(__name__)

openai.api_key = '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'  # 用你的 OpenAI API key 替换这个


def some_view(request):
    # ...

    # 异步执行任务
    analyze_user_interaction.delay(user)
from .models import UserNeed

def show_user_needs(request):
    # 引入User模型
    from ai_assistant.models import CustomUser  # 引入 CustomUser

    # 检查是否登录
    if not request.user.is_authenticated:
        return redirect('houtaidenglu')  # 如果用户未登录，则重定向到登录页面
    # 检查是否为超级用户
    if not request.user.is_superuser:
        raise PermissionDenied  # 如果用户不是超级用户，则抛出权限拒绝的异常

    # 获取所有的用户
    all_users = CustomUser.objects.all()

    # 对于每一个用户，调用 analyze_user_interaction.delay(user) 函数
    # 使用 Celery 的 delay() 函数将任务发送到后台
    for user in all_users:
        analyze_user_interaction.delay(user)

    # 获取所有的 UserNeed 对象
    all_user_needs = UserNeed.objects.all()

    # 将 UserNeed 对象传递给模板
    return render(request, 'user_needs.html', {'user_needs': all_user_needs})



# 用于获取用户对话历史的函数
@app.task
def analyze_user_interaction(user):
    from .models import Conversation, Message, UserNeed
    import openai

    conversations_before_last_activity = Conversation.objects.filter(user=user, created_at__lt=user.last_activity)
    if not conversations_before_last_activity.exists():
        return None

    print(
        f'Found {conversations_before_last_activity.count()} conversations for user {user.username} before their last activity.')

    for conversation in conversations_before_last_activity:
        print(f'Analyzing conversation {conversation.id} for user {user.username}...')
        messages = Message.objects.filter(conversation=conversation).order_by('created_at')

        new_question = "请根据以下的对话内容，分析和理解用户的需求："
        for message in messages:
            new_question += "\n\n" + message.role + ": " + message.content

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": new_question}]
        )

        # Check that 'choices' key exists in the response and it contains at least one element
        if 'choices' in response and len(response['choices']) > 0:
            # Check that 'message' key exists in the first choice
            if 'message' in response['choices'][0]:
                # Check that 'content' key exists in the message
                if 'content' in response['choices'][0]['message']:
                    # Now you can safely use the 'content' value
                    summarized_need = response['choices'][0]['message']['content']

                    user_need, created = UserNeed.objects.get_or_create(user=user, conversation=conversation, defaults={'need': summarized_need})
                    if not created:
                        user_need.need = summarized_need
                        user_need.save()

                    return summarized_need

    return None  # Return None if 'choices' key does not exist in the response or it does not contain at least one element, or 'message' key does not exist in the first choice, or 'content' key does not exist in the message





@shared_task
def check_conversations():
    # 获取所有还未结束的对话
    conversations = Conversation.objects.all()  # 你可能需要修改这个查询以适应你的实际需求

    for conversation in conversations:
        # 如果对话的最新消息的时间与当前时间的差值超过 30 分钟
        if timezone.now() - conversation.last_message_at > timedelta(minutes=5):
            # 对所有用户的对话进行分析
            analyze_all_user_interactions()

def analyze_conversation(conversation):
    # 将对话历史作为模型的输入
    messages = Message.objects.filter(conversation=conversation).order_by('created_at')
    prompt = "\n".join(f"{message.role}: {message.content}" for message in messages)

    # 给出明确的指示让模型概括用户的需求
    prompt += "\nGiven the above conversation, what does the user need?"

    response = openai.Completion.create(
      engine="gpt-3.5-turbo",  # 使用 GPT-3.5-turbo 模型
      prompt=prompt,
      max_tokens=1024  # 你可能需要调整这个值以适应你的需求
    )

    # 保存或使用模型的输出
    #conversation.need_summary = response.choices[0].text.strip()
    #conversation.save()
    summary = response.choices[0].text.strip()

    # 记录模型的输出
    logger.info(f"Conversation ID: {conversation.id}, Summary: {summary}")


def analyze_all_user_interactions():
    User = get_user_model()
    all_users = User.objects.all()  # 获取所有用户

    for user in all_users:
        analyze_user_interaction(user)  # 对每个用户调用 analyze_user_interaction(user) 函数