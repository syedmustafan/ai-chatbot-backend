"""
Chatbot URL configuration.
"""
from django.urls import path
from .views import ChatbotView, LeadsListView
from .twilio_views import TwilioVoiceIncomingView, TwilioVoiceGatherView

urlpatterns = [
    path('chat/', ChatbotView.as_view()),
    path('leads/', LeadsListView.as_view()),
    path('twilio/voice/incoming/', TwilioVoiceIncomingView.as_view()),
    path('twilio/voice/gather/', TwilioVoiceGatherView.as_view()),
]
