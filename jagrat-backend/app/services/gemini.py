import json
from typing import TypeVar

from pydantic import BaseModel

from app.config import get_settings

T = TypeVar("T", bound=BaseModel)


class GeminiService:
    """Thin wrapper around the official Gemini Interactions API.

    The service intentionally exposes only structured generation; every caller supplies
    its own narrow Pydantic schema so model output cannot silently change the API contract.
    """

    def __init__(self) -> None:
        from google import genai

        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        self.client = genai.Client(api_key=settings.gemini_api_key)
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
            raise RuntimeError("Gemini request failed; check GEMINI_API_KEY and free-tier quota.") from exc

        raw = interaction.output_text or ""
        if not raw:
            raise RuntimeError("Gemini returned an empty response")
        try:
            return schema.model_validate_json(raw)
        except Exception as exc:
            raise RuntimeError("Gemini returned output that did not match the expected schema.") from exc


def compact_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
