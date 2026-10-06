from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_profile
from app.db.session import get_db
from app.models import ChallengeRound, Conversation, Message, Profile
from app.schemas import ChallengeRequest, ChallengeResponse, MentorRequest, MentorResponse, SafetyResponse, MentorContinueRequest, MentorSessionSummary
from app.services.gemini import GeminiService
from app.services.mentor import ChallengeLimitError, MentorService, SourceGuardError
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

    try:
        return service().create_turn(db, profile.id, message)
    except SourceGuardError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Jagrat could not complete the reflection because Gemini is temporarily unavailable. Your request was saved; retry the reflection.") from exc


@router.post("/{conversation_id}/continue", response_model=MentorResponse | SafetyResponse)
def continue_reflection(conversation_id: str, payload: MentorContinueRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    response = payload.message.strip()
    local = local_risk_check(response)
    if local and is_blocking(local.risk_level):
        conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile.id))
        if conversation:
            conversation.risk_flag = True
            db.commit()
        return safety_message()
    conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile.id))
    if conversation and conversation.completed_at is not None:
        raise HTTPException(status_code=409, detail="This reflection is already completed and cannot be continued")
    if conversation and conversation.risk_flag:
        raise HTTPException(status_code=409, detail="This reflection is unavailable because it was safety-flagged")
    try:
        return service().continue_turn(db, profile.id, conversation_id, response)
    except LookupError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SourceGuardError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        if str(exc) == "SAFETY_TRIGGERED":
            return safety_message()
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/{conversation_id}/retry", response_model=MentorResponse | SafetyResponse)
def retry_reflection(conversation_id: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    try:
        return service().retry_turn(db, profile.id, conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except SourceGuardError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        if str(exc) == "SAFETY_TRIGGERED":
            return safety_message()
        raise HTTPException(status_code=503, detail="Gemini is temporarily unavailable; retry the reflection later.") from exc


@router.get("/sessions", response_model=list[MentorSessionSummary])
def sessions(status: str = "active", db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    """Return persisted reflection sessions so the frontend can offer Resume Reflection."""
    rows = list(
        db.scalars(
            select(Conversation)
            .where(Conversation.profile_id == profile.id)
            .order_by(Conversation.updated_at.desc())
            .limit(100)
        ).all()
    )
    if status not in {"active", "completed", "all"}:
        raise HTTPException(status_code=422, detail="status must be active, completed, or all")

    if status == "active":
        rows = [r for r in rows if r.completed_at is None and not r.risk_flag]
    elif status == "completed":
        rows = [r for r in rows if r.completed_at is not None]

    result: list[MentorSessionSummary] = []
    for r in rows:
        last_message = r.messages[-1] if r.messages else None
        last_activity = last_message.created_at if last_message else r.updated_at
        if r.risk_flag:
            session_status = "safety"
        elif r.completed_at is not None:
            session_status = "completed"
        else:
            session_status = "active"
        result.append(
            MentorSessionSummary(
                id=r.id,
                current_problem=r.current_problem,
                preview=(r.current_problem[:160] + ("…" if len(r.current_problem) > 160 else "")),
                status=session_status,
                created_at=r.created_at,
                updated_at=r.updated_at,
                last_activity_at=last_activity,
                completed=r.completed_at is not None,
                challenge_rounds=r.rounds_used,
                resumable=session_status == "active",
            )
        )
    return result


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

    try:
        return service().continue_challenge(db, profile.id, conversation_id, response)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ChallengeLimitError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except SourceGuardError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except RuntimeError as exc:
        if str(exc) == "SAFETY_TRIGGERED":
            return safety_message()
        raise HTTPException(status_code=503, detail="Gemini is temporarily unavailable; the challenge response was not generated.") from exc


@router.get("/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.profile_id == profile.id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = list(db.scalars(select(Message).where(Message.conversation_id == conversation.id).order_by(Message.created_at)).all())
    rounds = list(db.scalars(select(ChallengeRound).where(ChallengeRound.conversation_id == conversation.id).order_by(ChallengeRound.round_number)).all())
    status = "safety" if conversation.risk_flag else ("completed" if conversation.completed_at is not None else "active")
    return {
        "id": conversation.id,
        "status": status,
        "resumable": status == "active",
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
