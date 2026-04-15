"""
Anthropic native tool-use agent with web search.

Uses the Anthropic Python SDK directly (no LangChain/LangGraph).
Implements the standard tool-use loop: send → tool_use → execute → tool_result → repeat.
"""
import json
import logging
import os

import anthropic
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

TOOL_DEFINITIONS = [
    {
        "name": "web_search",
        "description": (
            "Search the web for current information. Use this when the user asks "
            "about recent events, real-time data, facts you're unsure about, or "
            "anything that benefits from up-to-date web results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up on the web",
                }
            },
            "required": ["query"],
        },
    }
]

SYSTEM_PROMPT = (
    "You are a helpful AI assistant powered by Claude. You have access to a web "
    "search tool that lets you find current information from the internet. Use it "
    "when the user asks about recent events, specific facts, or anything that "
    "would benefit from up-to-date information. Be concise and cite your sources "
    "when using search results."
)

MAX_TOOL_ITERATIONS = 5


def _execute_web_search(query: str) -> str:
    """Run a DuckDuckGo search and return formatted results."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        if not results:
            return "No results found."
        formatted = []
        for r in results:
            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")
            formatted.append(f"**{title}**\n{body}\nSource: {href}")
        return "\n\n".join(formatted)
    except Exception as e:
        logger.warning("Web search failed: %s", e)
        return f"Search failed: {str(e)}"


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch tool calls to their implementations."""
    if tool_name == "web_search":
        return _execute_web_search(tool_input.get("query", ""))
    return f"Unknown tool: {tool_name}"


class AnthropicAgentService:
    """Runs an Anthropic tool-use agent loop, yielding SSE events."""

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    def run_agent_loop(self, user_message: str, history: list[dict]):
        """
        Generator that yields SSE event dicts as the agent loop progresses.

        Events:
          {"event": "thinking"}              — Claude is processing
          {"event": "tool_call", "data": {"tool": str, "input": dict}}
          {"event": "tool_result", "data": {"tool": str, "result": str}}
          {"event": "message", "data": {"text": str}}
          {"event": "done"}
          {"event": "error", "data": {"message": str}}
        """
        # Build messages from history + new user message
        messages = []
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })
        messages.append({"role": "user", "content": user_message})

        yield {"event": "thinking"}

        for iteration in range(MAX_TOOL_ITERATIONS):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=SYSTEM_PROMPT,
                    tools=TOOL_DEFINITIONS,
                    messages=messages,
                )
            except anthropic.APIError as e:
                logger.error("Anthropic API error: %s", e)
                yield {"event": "error", "data": {"message": str(e)}}
                return

            # Process response content blocks
            if response.stop_reason == "tool_use":
                # Append the full assistant message (text + tool_use blocks)
                messages.append({"role": "assistant", "content": response.content})

                # Execute each tool call
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input

                        yield {
                            "event": "tool_call",
                            "data": {"tool": tool_name, "input": tool_input},
                        }

                        result = _execute_tool(tool_name, tool_input)

                        yield {
                            "event": "tool_result",
                            "data": {
                                "tool": tool_name,
                                "result": result[:500],  # truncate for SSE
                            },
                        }

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                # Append tool results and continue loop
                messages.append({"role": "user", "content": tool_results})
                yield {"event": "thinking"}

            elif response.stop_reason == "end_turn":
                # Extract final text
                text_parts = [
                    block.text
                    for block in response.content
                    if hasattr(block, "text")
                ]
                final_text = "\n".join(text_parts)

                yield {"event": "message", "data": {"text": final_text}}
                yield {"event": "done"}
                return

            else:
                # Unexpected stop reason
                text_parts = [
                    block.text
                    for block in response.content
                    if hasattr(block, "text")
                ]
                final_text = "\n".join(text_parts) if text_parts else "No response generated."
                yield {"event": "message", "data": {"text": final_text}}
                yield {"event": "done"}
                return

        # Safety: max iterations reached
        yield {
            "event": "error",
            "data": {"message": "Agent loop exceeded maximum iterations."},
        }
