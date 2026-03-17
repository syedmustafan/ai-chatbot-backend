"""
Serializers for chat API.
"""
from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    """Validate incoming chat request payload."""
    message = serializers.CharField(required=True, allow_blank=False, max_length=4000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
