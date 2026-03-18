from django.contrib import admin
from .models import Conversation, Message, Lead


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'user_message', 'timestamp')
    list_filter = ('conversation',)
    readonly_fields = ('timestamp',)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'source', 'status', 'first_name', 'last_name', 'email', 'phone',
        'job_type', 'twilio_call_sid', 'created_at',
    )
    list_filter = ('source', 'status', 'job_type')
    search_fields = ('first_name', 'last_name', 'email', 'phone', 'twilio_call_sid')
    readonly_fields = ('created_at', 'updated_at')
