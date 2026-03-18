"""
Serializers for chat API.
"""
from rest_framework import serializers

from .models import Lead


class LeadSerializer(serializers.ModelSerializer):
    """Expose lead intake fields for the leads dashboard API."""

    conversation_id = serializers.UUIDField(source='conversation_id', read_only=True)

    class Meta:
        model = Lead
        fields = (
            'id',
            'conversation_id',
            'source',
            'status',
            'first_name',
            'last_name',
            'email',
            'phone',
            'job_type',
            'twilio_call_sid',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class ChatRequestSerializer(serializers.Serializer):
    """Validate incoming chat request payload."""
    message = serializers.CharField(required=True, allow_blank=False, max_length=4000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
