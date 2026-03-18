"""
Twilio Voice webhooks: inbound call + speech Gather loop.
"""
from xml.sax.saxutils import escape

from decouple import config
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from twilio.request_validator import RequestValidator

from .intake_service import run_intake_turn
from .services import OpenAIServiceError
from .models import Conversation, Lead, Message

CALL_START = '__CALL_START__'


def _public_url(request) -> str:
    base = (config('PUBLIC_BASE_URL', default='') or '').strip().rstrip('/')
    if base:
        return base + request.path
    return request.build_absolute_uri()


def _twilio_ok(request) -> bool:
    token = (config('TWILIO_AUTH_TOKEN', default='') or '').strip()
    if not token:
        return config('DEBUG', default=False, cast=bool)
    validator = RequestValidator(token)
    sig = request.META.get('HTTP_X_TWILIO_SIGNATURE', '')
    return validator.validate(_public_url(request), request.POST.dict(), sig)


def _phone_history(conversation) -> list[dict]:
    out = []
    for m in conversation.messages.order_by('timestamp'):
        if m.user_message and m.user_message != CALL_START:
            out.append({'role': 'user', 'content': m.user_message})
        elif m.user_message == CALL_START:
            pass
        if m.ai_response:
            out.append({'role': 'assistant', 'content': m.ai_response})
    return out


def _twiml_say_gather(say_text: str, gather_url: str) -> str:
    safe = escape(say_text)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">{safe}</Say>
  <Gather input="speech" action="{escape(gather_url)}" method="POST" speechTimeout="auto" language="en-US"></Gather>
  <Say voice="Polly.Joanna">I did not hear anything. Goodbye.</Say>
</Response>"""


def _twiml_say_hangup(say_text: str) -> str:
    safe = escape(say_text)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">{safe}</Say>
  <Hangup/>
</Response>"""


@method_decorator(csrf_exempt, name='dispatch')
class TwilioVoiceIncomingView(View):
    """First hit when call connects. Twilio Console: Voice webhook POST here."""

    def post(self, request):
        if not _twilio_ok(request):
            return HttpResponse('Forbidden', status=403)
        call_sid = request.POST.get('CallSid', '')
        if not call_sid:
            return HttpResponse(_twiml_say_hangup('Sorry, this line is not available.'), content_type='text/xml')

        if Lead.objects.filter(twilio_call_sid=call_sid).exists():
            lead = Lead.objects.get(twilio_call_sid=call_sid)
            conv = lead.conversation
            last = conv.messages.order_by('-timestamp').first()
            reply = (last.ai_response if last else '') or 'Hello, thanks for calling.'
            base = (config('PUBLIC_BASE_URL', default='') or '').strip().rstrip('/')
            gather_url = f'{base}/api/twilio/voice/gather/'
            return HttpResponse(_twiml_say_gather(reply, gather_url), content_type='text/xml')
        else:
            conv = Conversation.objects.create()
            caller = request.POST.get('From', '') or ''
            lead = Lead.objects.create(
                conversation=conv,
                source=Lead.Source.PHONE,
                twilio_call_sid=call_sid,
                phone=caller.replace(' ', '')[:32] if caller else '',
            )

        try:
            reply, _ = run_intake_turn(
                user_message='',
                history=[],
                lead=lead,
                channel='phone',
            )
        except OpenAIServiceError:
            reply = 'Thanks for calling. Please try again in a moment.'

        Message.objects.create(conversation=conv, user_message=CALL_START, ai_response=reply)

        base = (config('PUBLIC_BASE_URL', default='') or '').strip().rstrip('/')
        gather_url = f'{base}/api/twilio/voice/gather/'

        xml = _twiml_say_gather(reply, gather_url)
        return HttpResponse(xml, content_type='text/xml')


@method_decorator(csrf_exempt, name='dispatch')
class TwilioVoiceGatherView(View):
    """After caller speaks."""

    def post(self, request):
        if not _twilio_ok(request):
            return HttpResponse('Forbidden', status=403)
        call_sid = request.POST.get('CallSid', '')
        speech = (request.POST.get('SpeechResult') or '').strip()

        try:
            lead = Lead.objects.select_related('conversation').get(twilio_call_sid=call_sid)
        except Lead.DoesNotExist:
            return HttpResponse(_twiml_say_hangup('Goodbye.'), content_type='text/xml')

        conv = lead.conversation
        history = _phone_history(conv)

        if not speech:
            reply = "Sorry, I didn't catch that. Could you repeat that?"
            Message.objects.create(conversation=conv, user_message='(no speech)', ai_response=reply)
        else:
            try:
                reply, _ = run_intake_turn(
                    user_message=speech,
                    history=history,
                    lead=lead,
                    channel='phone',
                )
            except OpenAIServiceError:
                reply = 'Sorry, something went wrong. Please call back later.'
            Message.objects.create(conversation=conv, user_message=speech, ai_response=reply)

        lead.refresh_from_db()
        base = (config('PUBLIC_BASE_URL', default='') or '').strip().rstrip('/')
        gather_url = f'{base}/api/twilio/voice/gather/'

        if lead.status == Lead.Status.COMPLETE:
            return HttpResponse(_twiml_say_hangup(reply), content_type='text/xml')
        return HttpResponse(_twiml_say_gather(reply, gather_url), content_type='text/xml')
