"""Thin LLM client used by the AI coordinator.

Rules for this file:
- The API key is read from the environment only (see `app/config.py`).
  It is never written to a file, a log or a response body.
- Every failure mode (no key, timeout, HTTP error, empty answer, invalid
  JSON) is turned into a normal return value so the caller can decide
  what to do. Nothing here raises past the module.
"""

import json
import logging
import re

import httpx

from app import config

logger = logging.getLogger("triplan.llm")


class LLMError(Exception):
    """Raised when the provider cannot give us a usable answer."""


def _extract_json_text(raw: str) -> str:
    """Pull the JSON object out of a model answer.

    Models often wrap JSON in a markdown fence or add a sentence before
    it. This finds the first balanced `{...}` block.
    """
    if not raw:
        raise LLMError("The model returned an empty answer.")

    text = raw.strip()

    # Remove a markdown code fence if there is one.
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    start = text.find("{")
    if start == -1:
        raise LLMError("The model answer did not contain JSON.")

    # Walk forward to find the matching closing brace.
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]

    raise LLMError("The model answer contained incomplete JSON.")


def parse_json_answer(raw: str) -> dict:
    """Parse a model answer into a dict.

    Raises:
        LLMError: when the answer is not valid JSON.
    """
    candidate = _extract_json_text(raw)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise LLMError(f"The model answer was not valid JSON: {exc.msg}") from exc

    if not isinstance(parsed, dict):
        raise LLMError("The model answer was JSON, but not a JSON object.")

    return parsed


def chat_completion(
    messages: list[dict],
    response_format: dict | None = None,
    temperature: float | None = None,
) -> str:
    """Send a chat request to the provider and return the raw answer text.

    Raises:
        LLMError: for every failure, so the caller can fall back cleanly.
    """
    if not config.is_ai_configured():
        raise LLMError("No AI provider is configured.")

    url = f"{config.LLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": config.LLM_MODEL,
        "messages": messages,
        "temperature": config.LLM_TEMPERATURE if temperature is None else temperature,
        "max_tokens": config.LLM_MAX_TOKENS,
    }
    if response_format:
        body["response_format"] = response_format

    try:
        with httpx.Client(timeout=config.LLM_TIMEOUT_SECONDS) as client:
            response = client.post(url, headers=headers, json=body)
    except httpx.TimeoutException as exc:
        raise LLMError(f"The AI provider did not answer in time: {exc}") from exc
    except httpx.HTTPError as exc:
        raise LLMError(f"Could not reach the AI provider: {exc}") from exc

    if response.status_code >= 400:
        # Log the status only. The body may echo the key, so keep it out of the log.
        logger.warning("AI provider returned HTTP %s", response.status_code)
        raise LLMError(f"The AI provider returned an error (HTTP {response.status_code}).")

    try:
        payload = response.json()
    except ValueError as exc:
        raise LLMError("The AI provider returned a response we could not read.") from exc

    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("The AI provider returned an unexpected response shape.") from exc

    if not content or not content.strip():
        raise LLMError("The AI provider returned an empty answer.")

    return content


def ask_for_json(
    prompt: str,
    response_format: dict | None = None,
    temperature: float | None = None,
) -> dict:
    """Ask the model for JSON and return the parsed dict.

    Raises:
        LLMError: when the provider fails or the answer is not valid JSON.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are a trip-planning assistant for TriPlan. "
                "You always answer with a single JSON object and nothing else."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    raw = chat_completion(
        messages,
        response_format=response_format,
        temperature=temperature,
    )
    return parse_json_answer(raw)
