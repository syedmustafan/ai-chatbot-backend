"""
AI Assistant endpoint with Anthropic native tool-use and SSE streaming.
"""
import json
import logging

from django.http import StreamingHttpResponse
from rest_framework.views import APIView

from .anthropic_service import AnthropicAgentService
from .models import Conversation, Message
from .views import get_or_create_conversation, get_conversation_history

logger = logging.getLogger(__name__)


def _format_sse(event: str, data: dict | None = None) -> str:
    """Format a single SSE event string."""
    line = f"event: {event}\n"
    line += f"data: {json.dumps(data or {})}\n\n"
    return line


class AssistantChatView(APIView):
    """
    POST /api/assistant/chat/
    Body: { "message": "user text", "conversation_id": "uuid" (optional) }

    Returns a Server-Sent Events stream with agent loop events.
    """

    def post(self, request):
        message = (request.data.get("message") or "").strip()
        if not message:
            return StreamingHttpResponse(
                _format_sse("error", {"message": "Message cannot be empty."}),
                content_type="text/event-stream",
                status=400,
            )

        conversation_id = request.data.get("conversation_id")
        conversation = get_or_create_conversation(conversation_id)
        history = get_conversation_history(conversation)

        def event_stream():
            final_text = ""
            try:
                service = AnthropicAgentService()
                for event in service.run_agent_loop(message, history):
                    event_type = event.get("event", "unknown")
                    event_data = event.get("data")

                    if event_type == "message" and event_data:
                        final_text = event_data.get("text", "")
                        event_data["conversation_id"] = str(conversation.id)

                    # Skip the generator's done event; we send our own at the end
                    if event_type == "done":
                        continue
                    yield _format_sse(event_type, event_data)

            except Exception as e:
                logger.exception("Assistant chat error")
                yield _format_sse("error", {"message": str(e)})
                final_text = ""

            # Save the exchange to the database
            if final_text:
                Message.objects.create(
                    conversation=conversation,
                    user_message=message,
                    ai_response=final_text,
                )

            # Always end with done
            yield _format_sse("done", {"conversation_id": str(conversation.id)})

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
