"""
Chatbot models: conversations, messages, and intake leads.
"""
import uuid
from django.db import models


class Conversation(models.Model):
    """Tracks a chat or phone session."""
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


class Lead(models.Model):
    """Structured intake data from web chat or phone; updated incrementally."""

    class Source(models.TextChoices):
        WEB = 'web', 'Web chat'
        PHONE = 'phone', 'Phone'

    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In progress'
        COMPLETE = 'complete', 'Complete'

    class JobType(models.TextChoices):
        FULL_MOVE = 'full_move', 'Full move'
        PARTIAL_MOVE = 'partial_move', 'Partial move'
        FEW_BOXES = 'few_boxes', 'Few boxes only'
        MOVING_LIFT = 'moving_lift', 'Moving lift'
        OTHER = 'other', 'Other'

    conversation = models.OneToOneField(
        Conversation,
        on_delete=models.CASCADE,
        related_name='lead',
    )
    twilio_call_sid = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )
    source = models.CharField(
        max_length=16,
        choices=Source.choices,
        default=Source.WEB,
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )

    first_name = models.CharField(max_length=120, blank=True)
    last_name = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    job_type = models.CharField(
        max_length=32,
        choices=JobType.choices,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        name = (self.first_name or '') + ' ' + (self.last_name or '')
        return f"Lead {self.pk} ({self.source}) {name.strip() or '—'}"

    def missing_fields(self) -> list[str]:
        """Field names still empty."""
        need = []
        if not (self.first_name or '').strip():
            need.append('first_name')
        if not (self.last_name or '').strip():
            need.append('last_name')
        if not (self.email or '').strip():
            need.append('email')
        if not (self.phone or '').strip():
            need.append('phone')
        if not (self.job_type or '').strip():
            need.append('job_type')
        return need

    def refresh_complete(self) -> bool:
        """Set status complete if all fields filled; returns True if complete."""
        if not self.missing_fields():
            self.status = self.Status.COMPLETE
            return True
        return False
