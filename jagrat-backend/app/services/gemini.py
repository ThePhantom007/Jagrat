import json
from typing import TypeVar

from pydantic import BaseModel

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)


class GeminiUnavailableError(RuntimeError):
    """Provider/configuration/quota failure that should be surfaced as HTTP 503."""


class GeminiOutputError(RuntimeError):
    """Provider returned malformed structured output."""


class GeminiService:
    """Thin wrapper around the official Gemini Interactions API.

    The service intentionally exposes only structured generation; every caller supplies
    its own narrow Pydantic schema so model output cannot silently change the API contract.
    """

    def __init__(self) -> None:
        try:
            from google import genai
        except Exception as exc:
            raise GeminiUnavailableError("Gemini client is not installed") from exc

        settings = get_settings()
        if not settings.gemini_api_key:
            raise GeminiUnavailableError("GEMINI_API_KEY is not configured")
        try:
            self.client = genai.Client(api_key=settings.gemini_api_key)
        except Exception as exc:
            raise GeminiUnavailableError("Gemini client could not be initialized") from exc
        self.model = settings.gemini_model
        self.fast_model = settings.gemini_fast_model

    def generate(self, *, system_instruction: str, prompt: str, schema: type[T], fast: bool = False) -> T:
        model = self.fast_model if fast else self.model
        try:
            interaction = self.client.interactions.create(
                model=model,
                input=prompt,
                system_instruction=system_instruction,
                response_format=[
                    {
                        "type": "text",
                        "mime_type": "application/json",
                        "schema": schema.model_json_schema(),
                    }
                ],
                # We do not use Gemini-side conversation storage; our backend owns persistence.
                store=False,
            )
        except Exception as exc:
            # Do not leak provider internals/API details to the client.
            raise GeminiUnavailableError("Gemini request failed; check GEMINI_API_KEY and free-tier quota.") from exc

        raw = interaction.output_text or ""
        if not raw:
            raise GeminiOutputError("Gemini returned an empty response")
        try:
            return schema.model_validate_json(raw)
        except Exception as exc:
            raise GeminiOutputError("Gemini returned output that did not match the expected schema.") from exc


def compact_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
