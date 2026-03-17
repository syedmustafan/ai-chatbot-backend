"""
Chatbot models for storing conversations and messages.
"""
import uuid
from django.db import models


class Conversation(models.Model):
    """Tracks a chat session."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']


class Message(models.Model):
    """Stores user messages and AI responses within a conversation."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    user_message = models.TextField()
    ai_response = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
