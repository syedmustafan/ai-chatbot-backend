"""
Shared intake logic: natural reply + structured field extraction (web + phone).
"""
import json
import re
from typing import Any

from decouple import config
from openai import OpenAI
from openai import APITimeoutError, APIError, APIConnectionError

from .models import Lead
from .services import OpenAIServiceError, OPENAI_TIMEOUT

INTAKE_SYSTEM = """You are a warm, professional intake assistant for a moving company.
You collect: first name, last name, email, phone, and type of job.

Job types (use these exact codes in JSON only): full_move, partial_move, few_boxes, moving_lift, other.
Map user phrases naturally: "whole apartment" -> full_move, "just a few things" -> few_boxes, "elevator/lift service" -> moving_lift, etc.

Rules:
- Sound human: short sentences, one follow-up at a time when helpful.
- If the user gives multiple pieces of info at once, acknowledge and extract all you can.
- If something is unclear or incomplete, ask a friendly clarifying question in assistant_message.
- If the user corrects themselves, use the corrected value.
- For phone channel, keep replies concise for text-to-speech (under ~40 words when possible).

You MUST respond with a single JSON object only, no markdown:
{
  "assistant_message": "what you say to the user next",
  "first_name": string or null,
  "last_name": string or null,
  "email": string or null,
  "phone": string or null (E.164 or digits ok),
  "job_type": one of full_move|partial_move|few_boxes|moving_lift|other or null,
  "intake_complete": boolean (true only if all five fields are confidently known from the conversation so far)
}

Only include non-null keys for fields the user clearly provided in this turn OR you are correcting from context.
If nothing new extracted this turn, use null for all field keys except assistant_message.
When intake_complete is true, assistant_message should thank them and say someone will be in touch — still use JSON."""

JOB_CODES = frozenset({
    'full_move', 'partial_move', 'few_boxes', 'moving_lift', 'other',
})


def _normalize_phone(value: str | None) -> str:
    if not value or not isinstance(value, str):
        return ''
    digits = re.sub(r'\D', '', value)
    if len(digits) >= 10:
        return value.strip()[:32]
    return value.strip()[:32]


def _merge_lead(lead: Lead, data: dict[str, Any]) -> None:
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email

    for key in ('first_name', 'last_name'):
        v = data.get(key)
        if v is not None and isinstance(v, str) and v.strip():
            setattr(lead, key, v.strip()[:120])
    v = data.get('email')
    if v is not None and isinstance(v, str) and v.strip():
        try:
            validate_email(v.strip())
            lead.email = v.strip()[:254]
        except ValidationError:
            pass
    v = data.get('phone')
    if v is not None and isinstance(v, str) and v.strip():
        lead.phone = _normalize_phone(v)
    v = data.get('job_type')
    if v is not None and isinstance(v, str) and v in JOB_CODES:
        lead.job_type = v
    if not lead.missing_fields():
        lead.status = Lead.Status.COMPLETE
    else:
        lead.status = Lead.Status.IN_PROGRESS
    lead.save()


def run_intake_turn(
    *,
    user_message: str,
    history: list[dict],
    lead: Lead,
    channel: str,
) -> tuple[str, list[str]]:
    """
    Returns (assistant_message, missing_fields_after).
    Updates lead in DB.
    """
    api_key = config('OPENAI_API_KEY', default=None)
    if not api_key:
        raise OpenAIServiceError("OPENAI_API_KEY is not set in environment.")
    client = OpenAI(api_key=api_key.strip())
    model = config('OPENAI_MODEL', default='gpt-4o-mini')

    snapshot = {
        'first_name': lead.first_name or None,
        'last_name': lead.last_name or None,
        'email': lead.email or None,
        'phone': lead.phone or None,
        'job_type': lead.job_type or None,
        'channel': channel,
    }
    user_block = (
        f"Known lead data so far: {json.dumps(snapshot)}\n\n"
        f"User said: {user_message or '(call just connected — give a short greeting and start naturally)'}"
    )
    messages = [
        {"role": "system", "content": INTAKE_SYSTEM},
        *history[-16:],
        {"role": "user", "content": user_block},
    ]
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            timeout=OPENAI_TIMEOUT,
        )
    except APITimeoutError:
        raise OpenAIServiceError("The request to OpenAI timed out.")
    except APIConnectionError:
        raise OpenAIServiceError("Could not connect to OpenAI.")
    except APIError as e:
        raise OpenAIServiceError(str(e) or "OpenAI API error.")

    raw = (response.choices[0].message.content or "").strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise OpenAIServiceError("Invalid JSON from model.")

    assistant = (data.get("assistant_message") or "Thanks — could you repeat that?").strip()
    _merge_lead(lead, data)
    lead.refresh_from_db()
    return assistant, lead.missing_fields()
