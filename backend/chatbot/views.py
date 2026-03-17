"""
Chat API view.
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import ChatRequestSerializer
from .services import OpenAIService, OpenAIServiceError
from .models import Conversation, Message


def get_or_create_conversation(conversation_id=None):
    """Get existing conversation by id or create a new one."""
    if conversation_id:
        try:
            return Conversation.objects.get(pk=conversation_id)
        except Conversation.DoesNotExist:
            pass
    return Conversation.objects.create()


def get_conversation_history(conversation, max_messages=20):
    """Build list of message dicts for OpenAI from stored messages."""
    messages = conversation.messages.order_by('timestamp')[:max_messages]
    history = []
    for m in messages:
        history.append({"role": "user", "content": m.user_message})
        if m.ai_response:
            history.append({"role": "assistant", "content": m.ai_response})
    return history


class ChatbotView(APIView):
    """
    POST /api/chat/
    Body: { "message": "user text", "conversation_id": "uuid" (optional) }
    """

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "error": "Invalid request.", "details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        message = serializer.validated_data["message"].strip()
        if not message:
            return Response(
                {"success": False, "error": "Message cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        conversation_id = serializer.validated_data.get("conversation_id")

        try:
            openai_service = OpenAIService()
        except OpenAIServiceError as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        conversation = get_or_create_conversation(conversation_id)
        history = get_conversation_history(conversation)

        try:
            ai_response = openai_service.send_message(message, conversation_history=history)
        except OpenAIServiceError as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        Message.objects.create(
            conversation=conversation,
            user_message=message,
            ai_response=ai_response,
        )
        ts = timezone.now()
        if timezone.is_naive(ts):
            ts = timezone.make_aware(ts, timezone.UTC)
        ts = ts.astimezone(timezone.UTC)
        timestamp_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return Response(
            {
                "success": True,
                "response": ai_response,
                "conversation_id": str(conversation.id),
                "timestamp": timestamp_str,
            },
            status=status.HTTP_200_OK,
        )
