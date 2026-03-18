"""
Chat API view (web intake).
"""
import datetime

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import ChatRequestSerializer, LeadSerializer
from .services import OpenAIServiceError
from .intake_service import run_intake_turn
from .models import Conversation, Message, Lead


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
        if m.user_message and m.user_message not in ('__CALL_START__',):
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
        try:
            return self._handle_post(request)
        except Exception as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _handle_post(self, request):
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

        conversation = get_or_create_conversation(conversation_id)
        lead, _ = Lead.objects.get_or_create(
            conversation=conversation,
            defaults={"source": Lead.Source.WEB},
        )
        if lead.source != Lead.Source.WEB:
            return Response(
                {"success": False, "error": "This conversation is not a web session."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        history = get_conversation_history(conversation)

        try:
            ai_response, missing = run_intake_turn(
                user_message=message,
                history=history,
                lead=lead,
                channel="web",
            )
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
        lead.refresh_from_db()
        ts = timezone.now()
        if timezone.is_naive(ts):
            ts = timezone.make_aware(ts, datetime.timezone.utc)
        ts = ts.astimezone(datetime.timezone.utc)
        timestamp_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return Response(
            {
                "success": True,
                "response": ai_response,
                "conversation_id": str(conversation.id),
                "timestamp": timestamp_str,
                "lead_status": lead.status,
                "missing_fields": missing,
            },
            status=status.HTTP_200_OK,
        )


class LeadsPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


def _leads_api_authorized(request) -> bool:
    key = getattr(settings, 'LEADS_API_KEY', '') or ''
    if not key:
        return bool(settings.DEBUG)
    auth = (request.headers.get('Authorization') or '').strip()
    if auth.lower().startswith('bearer '):
        token = auth[7:].strip()
        if token == key:
            return True
    return (request.headers.get('X-API-Key') or '').strip() == key


class LeadsListView(APIView):
    """
    GET /api/leads/
    Paginated list of intake leads (newest first).

    When DEBUG is False, set LEADS_API_KEY and send it as:
    Header: X-API-Key: <key> or Authorization: Bearer <key>
    """

    def get(self, request):
        if not _leads_api_authorized(request):
            if not getattr(settings, 'LEADS_API_KEY', ''):
                return Response(
                    {
                        'detail': 'Leads API requires LEADS_API_KEY in production (DEBUG=False). '
                        'Set LEADS_API_KEY and pass X-API-Key or Authorization: Bearer <key>.',
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            return Response({'detail': 'Invalid or missing API key.'}, status=status.HTTP_401_UNAUTHORIZED)

        queryset = Lead.objects.select_related('conversation').all().order_by('-updated_at')
        paginator = LeadsPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = LeadSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
