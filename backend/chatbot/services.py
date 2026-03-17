"""
OpenAI integration for the chatbot.
"""
from decouple import config
from openai import OpenAI
from openai import APITimeoutError, APIError, APIConnectionError

# Timeout in seconds for OpenAI API calls
OPENAI_TIMEOUT = 30

# Default system prompt for the assistant
DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, friendly assistant. "
    "Answer concisely and clearly. If you don't know something, say so."
)


class OpenAIServiceError(Exception):
    """Raised when OpenAI service fails."""
    pass


class OpenAIService:
    """Service for sending messages to OpenAI Chat API."""

    def __init__(self):
        api_key = config('OPENAI_API_KEY', default=None)
        if not api_key:
            raise OpenAIServiceError("OPENAI_API_KEY is not set in environment.")
        self.client = OpenAI(api_key=api_key)
        self.model = config('OPENAI_MODEL', default='gpt-3.5-turbo')
        self.system_prompt = config('OPENAI_SYSTEM_PROMPT', default=DEFAULT_SYSTEM_PROMPT)

    def _build_messages(self, user_message: str, conversation_history: list[dict] | None = None):
        """Build messages list for the API: system + history + new user message."""
        messages = [{"role": "system", "content": self.system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_message})
        return messages

    def send_message(
        self,
        user_message: str,
        conversation_history: list[dict] | None = None
    ) -> str:
        """
        Send user message to OpenAI and return the assistant's reply.

        Args:
            user_message: The user's message text.
            conversation_history: Optional list of {"role": "user"|"assistant", "content": "..."}.

        Returns:
            The assistant's reply text.

        Raises:
            OpenAIServiceError: On API failure, timeout, or invalid response.
        """
        messages = self._build_messages(user_message, conversation_history)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                timeout=OPENAI_TIMEOUT,
            )
        except APITimeoutError:
            raise OpenAIServiceError("The request to OpenAI timed out. Please try again.")
        except APIConnectionError:
            raise OpenAIServiceError("Could not connect to OpenAI. Check your network.")
        except APIError as e:
            raise OpenAIServiceError(str(e) or "OpenAI API error occurred.")

        choices = response.choices
        if not choices:
            raise OpenAIServiceError("OpenAI returned no response.")
        content = choices[0].message.content
        if content is None:
            raise OpenAIServiceError("OpenAI returned empty content.")
        return content.strip()
