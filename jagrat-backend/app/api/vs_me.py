from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_profile
from app.db.session import get_db
from app.models import Profile
from app.schemas import SafetyResponse, VivekanandaVsMeRequest, VivekanandaVsMeResponse
from app.services.gemini import GeminiService
from app.services.mentor import SourceGuardError
from app.services.safety import local_risk_check, safety_message
from app.services.vs_me import VivekanandaVsMeService


def is_blocking(level: str) -> bool:
    return level in {"high", "immediate"}

router = APIRouter(prefix="/vivekananda-vs-me", tags=["vivekananda-vs-me"])


def service() -> VivekanandaVsMeService:
    return VivekanandaVsMeService(GeminiService())


@router.post("", response_model=VivekanandaVsMeResponse | SafetyResponse)
def create_comparison(
    payload: VivekanandaVsMeRequest,
    db: Session = Depends(get_db),
    profile: Profile = Depends(get_profile),
):
    view = payload.view.strip()
    local = local_risk_check(view)
    if local and is_blocking(local.risk_level):
        return safety_message()
    try:
        return service().create(db, profile.id, view)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SourceGuardError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        if str(exc) == "SAFETY_TRIGGERED":
            return safety_message()
        raise HTTPException(status_code=503, detail="Jagrat could not complete the comparison because Gemini is temporarily unavailable.") from exc


@router.get("/{comparison_id}", response_model=VivekanandaVsMeResponse)
def get_comparison(
    comparison_id: str,
    db: Session = Depends(get_db),
    profile: Profile = Depends(get_profile),
):
    try:
        return service().get(db, profile.id, comparison_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
