"""Shared OpenAI client and JSON parsing for all agents."""
import json
from openai import AsyncOpenAI
from app.core.config import get_settings

settings = get_settings()
openai_client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)


async def chat_completion(messages: list, model: str, temperature: float = 0.2) -> tuple[str, int, int]:
    """Returns (content, input_tokens, output_tokens)."""
    response = await openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=3500,
        response_format={"type": "json_object"},
    )
    choice = response.choices[0].message.content
    return choice, response.usage.prompt_tokens, response.usage.completion_tokens


async def chat_text(messages: list, model: str, temperature: float = 0.3) -> tuple[str, int, int]:
    """Free-text response (not JSON)."""
    response = await openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=3500,
    )
    choice = response.choices[0].message.content
    return choice, response.usage.prompt_tokens, response.usage.completion_tokens


def parse_json(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Extract JSON block if wrapped in markdown
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}
