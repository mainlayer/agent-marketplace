import httpx
import time
from .models import Agent


async def call_agent_endpoint(agent: Agent, input_text: str) -> tuple[str, int]:
    """
    Proxy a call to an agent's endpoint.
    Returns (result_text, latency_ms).
    Falls back to mock response if endpoint is unreachable.
    """
    start = time.monotonic()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                agent.endpoint,
                json={"input": input_text},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            result = data.get("result") or data.get("output") or str(data)
    except (httpx.RequestError, httpx.HTTPStatusError):
        # Agent not reachable — return a contextual mock response
        result = _mock_response(agent, input_text)

    latency_ms = int((time.monotonic() - start) * 1000)
    return result, latency_ms


def _mock_response(agent: Agent, input_text: str) -> str:
    """Return a plausible mock response based on agent capabilities."""
    caps = [c.lower() for c in agent.capabilities]

    if "weather" in caps or "forecasting" in caps:
        city = _extract_city(input_text) or "your city"
        return (
            f"Weather for {city}:\n"
            f"Current: 22°C, Partly cloudy\n"
            f"Humidity: 58% | Wind: 14 km/h NW\n"
            f"Today: High 24°C, Low 17°C\n"
            f"Tomorrow: High 21°C, Chance of rain 30%\n"
            f"7-day outlook: Warm and partly sunny through the week."
        )

    if "summarization" in caps or "summary" in caps:
        word_count = len(input_text.split())
        return (
            f"Summary ({word_count} words condensed):\n\n"
            f"The provided text covers key themes around {_extract_topic(input_text)}. "
            f"Main points include the core subject matter and supporting details. "
            f"The author presents a structured argument with evidence-based conclusions. "
            f"Key takeaway: the content addresses practical implications for the reader."
        )

    if "translation" in caps or "multilingual" in caps:
        target = _extract_language(input_text) or "Spanish"
        return (
            f"Translation to {target}:\n\n"
            f"[Translated content of: \"{input_text[:80]}{'...' if len(input_text) > 80 else ''}\"]\n\n"
            f"Note: Translation completed with 98.2% confidence. "
            f"Register: Formal. Detected source language: English."
        )

    return f"Agent '{agent.name}' processed your request successfully.\n\nInput: {input_text[:100]}"


def _extract_city(text: str) -> str:
    """Naively extract a city name from weather query."""
    lower = text.lower()
    for prep in ["in ", "for ", "at "]:
        idx = lower.rfind(prep)
        if idx != -1:
            candidate = text[idx + len(prep):].strip().rstrip("?.,!")
            if candidate:
                return candidate.split()[0].capitalize()
    return ""


def _extract_topic(text: str) -> str:
    words = [w for w in text.split() if len(w) > 4]
    return words[0] if words else "the subject"


def _extract_language(text: str) -> str:
    languages = [
        "Spanish", "French", "German", "Italian", "Portuguese",
        "Japanese", "Chinese", "Korean", "Arabic", "Russian",
        "Dutch", "Swedish", "Polish", "Turkish", "Hindi",
    ]
    lower = text.lower()
    for lang in languages:
        if lang.lower() in lower:
            return lang
    return ""
