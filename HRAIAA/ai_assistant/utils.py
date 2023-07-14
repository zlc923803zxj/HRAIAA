# utils.py
from ai_assistant.models import Conversation,Message


def get_conversation_history_for_model(user):
    # 获取用户的所有对话
    conversations = Conversation.objects.filter(user=user)

    # 获取这些对话中的所有消息
    messages = Message.objects.filter(conversation__in=conversations)

    # 将每个消息转换为一个字典，并添加到列表中
    conversation_history = []
    for message in messages:
        conversation_history.append({
            'role': message.role,
            'content': message.content
        })

    return conversation_history