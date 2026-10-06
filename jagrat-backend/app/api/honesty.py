from fastapi import APIRouter, Depends
from app.api.deps import get_profile
from app.models import Profile

router = APIRouter(prefix="/honesty", tags=["honesty"])


@router.get("")
def honesty(profile: Profile = Depends(get_profile)):
    return {
        "product": "Jagrat",
        "identity": "Jagrat is an AI reflection tool, not Swami Vivekananda.",
        "source_authority": {
            "name": "organizer_provided_csv",
            "description": "The organiser-provided CSV is the canonical source of truth for teachings used by Jagrat.",
        },
        "quote_handling": {
            "gemini_returns": "quote_id only",
            "backend_renders_quote": True,
            "exact_text_preserved": True,
            "candidate_id_guard": True,
        },
        "ai_written_sections": [
            "understanding",
            "interpretation",
            "reflection",
            "challenge",
            "action",
        ],
        "journal_memory": "Relevant journal context may be used internally to personalize a reflection; unrelated diary content is not included in mentor context and relevant diary excerpts are not displayed as a separate section in the answer.",
        "growth": "Theme frequencies are observations from product activity. Five-factor values are explicit self-reported weekly check-ins, not clinical measurements.",
        "safety": "High-risk content bypasses the normal mentor/challenge flow and receives a supportive safety response with India-based resources.",
        "gemini": {
            "role": "reasoning and structured generation",
            "source_of_truth": False,
            "backend_owns_history": True,
        },
    }
