from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_profile
from app.db.session import get_db
from app.models import ChallengeRound, Conversation, Message, Profile
from app.schemas import ChallengeRequest, ChallengeResponse, MentorRequest, MentorResponse, SafetyResponse
from app.services.gemini import GeminiService
from app.services.mentor import MentorService, SourceGuardError
from app.services.context import onboarding_complete
from app.services.safety import local_risk_check, safety_message

router = APIRouter(prefix="/mentor", tags=["mentor"])


def service() -> MentorService:
    return MentorService(GeminiService())


def is_blocking(level: str) -> bool:
    return level in {"high", "immediate"}


@router.post("", response_model=MentorResponse | SafetyResponse)
def mentor(payload: MentorRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    message = payload.message.strip()
    local = local_risk_check(message)
    if local and is_blocking(local.risk_level):
        return safety_message()

    if not onboarding_complete(profile):
        raise HTTPException(status_code=409, detail="Complete all six onboarding questions before starting a mentor reflection")

    svc = service()
    assessment = svc.assess_text(message)  # combines safety + problem classification in one Gemini call
    if is_blocking(assessment.risk.risk_level):
        return safety_message()

    # The MVP creates a new reflection conversation for each mentor request.
    # conversation_id is retained in the schema for frontend compatibility/future continuation.
    try:
        return svc.create_turn(db, profile.id, message, assessment=assessment)
    except LookupError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SourceGuardError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{conversation_id}/challenge", response_model=ChallengeResponse | SafetyResponse)
def challenge(conversation_id: str, payload: ChallengeRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    response = payload.user_response.strip()
    local = local_risk_check(response)
    if local and is_blocking(local.risk_level):
        conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile.id))
        if conversation:
            conversation.risk_flag = True
            db.commit()
        return safety_message()

    svc = service()
    assessment = svc.assess_text(response)  # one call: safety + lightweight classification
    if is_blocking(assessment.risk.risk_level):
        conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile.id))
        if conversation:
            conversation.risk_flag = True
            db.commit()
        return safety_message()

    try:
        return svc.continue_challenge(db, profile.id, conversation_id, response, assessment=assessment)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        if str(exc) == "SAFETY_TRIGGERED":
            return safety_message()
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile.id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = list(db.scalars(select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)).all())
    rounds = list(db.scalars(select(ChallengeRound).where(ChallengeRound.conversation_id == conversation.id).order_by(ChallengeRound.round_number)).all())
    return {
        "id": conversation.id,
        "current_problem": conversation.current_problem,
        "problem_analysis": conversation.problem_analysis,
        "selected_teaching_id": conversation.selected_teaching_id,
        "rounds_used": conversation.rounds_used,
        "completed_at": conversation.completed_at,
        "risk_flag": conversation.risk_flag,
        "created_at": conversation.created_at,
        "messages": [{"role": m.role, "content": m.content, "created_at": m.created_at, "metadata": m.metadata_json} for m in messages],
        "challenge_rounds": [{"round": r.round_number, "belief": r.belief, "assumption": r.assumption, "question": r.challenge_question, "user_response": r.user_response, "reflection": r.reflection, "next_step": r.next_step} for r in rounds],
    }
