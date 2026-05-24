"""
Shared LLM Client
===================
Centralised OpenAI wrapper used by all agents.
Handles JSON parsing, retries, and token usage logging.
"""

import json
import logging
import time
from typing import Any

logger = logging.getLogger("video_pipeline.agents.llm")

# Module-level client singleton
_client = None


def _get_client(api_key: str):
    """Lazy-init a shared OpenAI client."""
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=api_key)
    return _client


def call_llm(
    *,
    system_prompt: str,
    user_prompt: str,
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    json_mode: bool = True,
    max_retries: int = 2,
    agent_name: str = "agent",
) -> dict | list | str:
    """
    Call OpenAI with structured retry and JSON parsing.

    Args:
        system_prompt:  System message content.
        user_prompt:    User message content.
        api_key:        OpenAI API key.
        model:          Model identifier.
        temperature:    Sampling temperature.
        max_tokens:     Max response tokens.
        json_mode:      If True, request JSON response format.
        max_retries:    Number of retries on failure.
        agent_name:     Name for logging.

    Returns:
        Parsed JSON (dict or list) if json_mode=True, else raw string.
    """
    client = _get_client(api_key)

    response_format = {"type": "json_object"} if json_mode else None

    for attempt in range(1, max_retries + 1):
        try:
            t0 = time.time()
            logger.info(f"  [{agent_name}] Calling {model} (attempt {attempt})…")

            response = client.chat.completions.create(
                model=model,
                response_format=response_format,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            elapsed = time.time() - t0
            raw = response.choices[0].message.content

            # Log token usage
            usage = response.usage
            if usage:
                logger.info(
                    f"  [{agent_name}] Done in {elapsed:.1f}s — "
                    f"tokens: {usage.prompt_tokens} in / "
                    f"{usage.completion_tokens} out"
                )
            else:
                logger.info(f"  [{agent_name}] Done in {elapsed:.1f}s")

            if json_mode:
                parsed = json.loads(raw)
                return parsed
            return raw

        except json.JSONDecodeError as e:
            logger.warning(
                f"  [{agent_name}] JSON parse error (attempt {attempt}): {e}"
            )
            if attempt == max_retries:
                logger.error(
                    f"  [{agent_name}] Failed to parse JSON after "
                    f"{max_retries} attempts. Raw response:\n{raw[:500]}"
                )
                raise

        except Exception as e:
            logger.warning(
                f"  [{agent_name}] API error (attempt {attempt}): {e}"
            )
            if attempt == max_retries:
                raise
            time.sleep(1.0 * attempt)  # Backoff


def call_llm_with_history(
    *,
    messages: list[dict],
    api_key: str,
    model: str = "gpt-4o",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    json_mode: bool = True,
    agent_name: str = "agent",
) -> dict | list | str:
    """
    Call OpenAI with full message history (for critic retry loops).
    """
    client = _get_client(api_key)
    response_format = {"type": "json_object"} if json_mode else None

    t0 = time.time()
    logger.info(f"  [{agent_name}] Calling {model} (with history)…")

    response = client.chat.completions.create(
        model=model,
        response_format=response_format,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    elapsed = time.time() - t0
    raw = response.choices[0].message.content

    usage = response.usage
    if usage:
        logger.info(
            f"  [{agent_name}] Done in {elapsed:.1f}s — "
            f"tokens: {usage.prompt_tokens} in / "
            f"{usage.completion_tokens} out"
        )

    if json_mode:
        return json.loads(raw)
    return raw
