"""
Unified LLM Provider Layer with Interface, Retry Logic, and Structured Output Validation.

Provides:
  - LLMProvider (Base Interface)
  - GroqProvider (Primary: openai/gpt-oss-120b with fallback models)
  - GeminiProvider (Swappable fallback)
  - get_llm_provider() factory
"""

from __future__ import annotations

import abc
import asyncio
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)


def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Robustly extract the outermost JSON object from an LLM response,
    stripping markdown code fences, comments, and trailing commas.
    """
    if not text:
        raise ValueError("Empty response received from LLM")

    # Strip markdown code blocks
    cleaned = re.sub(r"```(?:json)?\s*", "", text)
    cleaned = re.sub(r"```", "", cleaned).strip()

    # Remove trailing commas before } or ]
    cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

    # Find first {
    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in LLM response: {text[:200]}")

    depth = 0
    end = start
    for i in range(start, len(cleaned)):
        if cleaned[i] == "{":
            depth += 1
        elif cleaned[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break

    if depth != 0:
        # Fallback: scan for last }
        end = cleaned.rfind("}") + 1
        if end <= start:
            raise ValueError(f"Mismatched braces in JSON response: {text[:200]}")

    return json.loads(cleaned[start:end])


class LLMProvider(abc.ABC):
    """Abstract Base Class for LLM Providers."""

    @abc.abstractmethod
    async def complete_json(
        self,
        system: str,
        user: str,
        json_schema: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Produce a validated JSON response.
        
        Args:
            system: System instructions.
            user: User input/prompt.
            json_schema: Optional JSON schema dictionary or Pydantic model class.
            temperature: Sampling temperature (capped at <= 0.3 for deterministic extraction).
        
        Returns:
            Parsed and validated Python dictionary.
        """
        pass


class GroqProvider(LLMProvider):
    """
    Groq LLM Provider using AsyncGroq.
    Supports primary model 'openai/gpt-oss-120b' with resilient multi-model fallback,
    exponential backoff for rate limits (429/413/5xx), and validation retries.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        # Models ordered by capability
        self.candidate_models = list(
            dict.fromkeys([self.model, "openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"])
        )

    async def _execute_with_backoff(
        self,
        client: Any,
        messages: List[Dict[str, str]],
        temperature: float,
    ) -> tuple[str, str, Dict[str, Any]]:
        """
        Executes chat completion with model fallback and exponential backoff.
        Returns: (raw_text, used_model, usage_stats)
        """
        max_retries = settings.LLM_MAX_RETRIES
        last_exception = None

        for model_name in self.candidate_models:
            for attempt in range(max_retries):
                try:
                    start_time = time.perf_counter()
                    logger.debug("Groq call model=%s attempt=%d", model_name, attempt + 1)
                    
                    response = await asyncio.wait_for(
                        client.chat.completions.create(
                            model=model_name,
                            messages=messages,
                            temperature=temperature,
                            response_format={"type": "json_object"},
                        ),
                        timeout=settings.LLM_TIMEOUT,
                    )
                    latency_ms = (time.perf_counter() - start_time) * 1000

                    usage = {}
                    if hasattr(response, "usage") and response.usage:
                        usage = {
                            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                            "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                            "total_tokens": getattr(response.usage, "total_tokens", 0),
                        }

                    logger.info(
                        "Groq completion: model=%s latency=%.1fms tokens=%s",
                        model_name,
                        latency_ms,
                        usage.get("total_tokens", "n/a"),
                    )

                    content = response.choices[0].message.content or "{}"
                    return content, model_name, usage

                except asyncio.TimeoutError as err:
                    logger.warning("Groq timeout (model=%s attempt=%d)", model_name, attempt + 1)
                    last_exception = err
                    await asyncio.sleep(1.0 * (2 ** attempt))

                except Exception as err:
                    err_str = str(err).lower()
                    last_exception = err

                    # Rate limits or message size limits -> try next model or back off
                    is_rate_limit = "429" in err_str or "rate_limit" in err_str or "tokens" in err_str or "413" in err_str
                    is_server_error = "500" in err_str or "502" in err_str or "503" in err_str or "504" in err_str
                    is_not_found = "404" in err_str or "model_not_found" in err_str

                    if is_not_found:
                        logger.warning("Groq model %s not found. Skipping to next model.", model_name)
                        break  # Break inner retry loop, try next model

                    if is_rate_limit or is_server_error:
                        delay = min(1.5 * (2 ** attempt), 10.0)
                        logger.warning(
                            "Groq retryable error (%s) on model=%s attempt=%d. Backing off %.1fs...",
                            type(err).__name__,
                            model_name,
                            attempt + 1,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        # If on the last attempt of this model, fall through to try next candidate model
                    else:
                        logger.error("Groq unrecoverable error on model %s: %s", model_name, err)
                        break

        raise RuntimeError(f"All Groq models and retry attempts failed. Last error: {last_exception}")

    async def complete_json(
        self,
        system: str,
        user: str,
        json_schema: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key.startswith("your_"):
            raise ValueError("GROQ_API_KEY is not configured in settings or environment.")

        from groq import AsyncGroq

        client = AsyncGroq(api_key=self.api_key)
        # Cap temperature for deterministic extraction / rewriting
        clamped_temp = min(max(temperature, 0.0), 0.3)

        schema_instruction = ""
        if json_schema is not None:
            if isinstance(json_schema, type) and issubclass(json_schema, BaseModel):
                schema_json = json.dumps(json_schema.model_json_schema(), indent=2)
                schema_instruction = f"\n\nSTRICT JSON SCHEMA:\n{schema_json}\nYour JSON output MUST match this schema."
            elif isinstance(json_schema, dict):
                schema_instruction = f"\n\nSTRICT JSON SCHEMA:\n{json.dumps(json_schema, indent=2)}\nYour JSON output MUST match this schema."

        system_prompt = (
            system
            + "\nYou are a strict JSON generator. Output ONLY a valid JSON object matching the requested schema. No conversational preamble, no markdown fences."
            + schema_instruction
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user},
        ]

        # Validation retry loop (max 2 attempts on parsing/schema failure)
        max_validation_retries = 2
        for val_attempt in range(max_validation_retries + 1):
            raw_text, used_model, _ = await self._execute_with_backoff(client, messages, clamped_temp)

            try:
                parsed_data = extract_json_object(raw_text)

                # Validate against Pydantic schema if provided
                if json_schema is not None and isinstance(json_schema, type) and issubclass(json_schema, BaseModel):
                    validated_obj = json_schema.model_validate(parsed_data)
                    return validated_obj.model_dump()

                return parsed_data

            except (ValueError, json.JSONDecodeError, ValidationError) as val_err:
                if val_attempt == max_validation_retries:
                    logger.error("Failed validation after %d retries: %s", max_validation_retries, val_err)
                    raise ValueError(f"LLM JSON output failed schema validation: {val_err}") from val_err

                logger.warning(
                    "LLM output failed validation (attempt %d/%d): %s. Feeding back to model...",
                    val_attempt + 1,
                    max_validation_retries,
                    val_err,
                )
                # Feed the error back to the model for correction
                messages.append({"role": "assistant", "content": raw_text})
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Your previous JSON output failed validation with error:\n{val_err}\n\n"
                            "Please fix all schema and formatting errors and output ONLY the corrected valid JSON object."
                        ),
                    }
                )

        raise RuntimeError("Failed to obtain valid JSON from LLM")


class GeminiProvider(LLMProvider):
    """
    Google Gemini Provider (Swappable implementation).
    Uses google-genai SDK with async generation and validation.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    async def complete_json(
        self,
        system: str,
        user: str,
        json_schema: Optional[Union[Dict[str, Any], Type[BaseModel]]] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        if not self.api_key or self.api_key.startswith("your_"):
            raise ValueError("GEMINI_API_KEY is not configured in settings.")

        from google import genai
        from google.genai.types import GenerateContentConfig

        client = genai.Client(api_key=self.api_key)
        clamped_temp = min(max(temperature, 0.0), 0.3)

        schema_instruction = ""
        if json_schema is not None:
            if isinstance(json_schema, type) and issubclass(json_schema, BaseModel):
                schema_json = json.dumps(json_schema.model_json_schema(), indent=2)
                schema_instruction = f"\n\nSTRICT JSON SCHEMA:\n{schema_json}"
            elif isinstance(json_schema, dict):
                schema_instruction = f"\n\nSTRICT JSON SCHEMA:\n{json.dumps(json_schema, indent=2)}"

        full_prompt = (
            f"{system}\n"
            f"You are a strict JSON generator. Output ONLY a valid JSON object.{schema_instruction}\n\n"
            f"USER REQUEST:\n{user}"
        )

        start_time = time.perf_counter()
        response = await client.aio.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=GenerateContentConfig(
                temperature=clamped_temp,
                top_p=0.95,
                max_output_tokens=8192,
            ),
        )
        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info("Gemini completion: model=%s latency=%.1fms", self.model, latency_ms)

        raw_text = response.text or "{}"
        parsed = extract_json_object(raw_text)

        if json_schema is not None and isinstance(json_schema, type) and issubclass(json_schema, BaseModel):
            return json_schema.model_validate(parsed).model_dump()

        return parsed


def get_llm_provider() -> LLMProvider:
    """Factory returning the active configured LLM provider."""
    provider_name = settings.LLM_PROVIDER.lower().strip()
    if provider_name == "groq" or (settings.GROQ_API_KEY and not settings.GEMINI_API_KEY):
        return GroqProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    # Default to Groq if key exists, otherwise Gemini
    if settings.GROQ_API_KEY:
        return GroqProvider()
    return GeminiProvider()
