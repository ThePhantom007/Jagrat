from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_profile
from app.db.session import get_db
from app.models import (
    Account,
    ActionFollowUp,
    ActionItem,
    AuthSession,
    ChallengeRound,
    Conversation,
    InteractionRecord,
    JournalEntry,
    JournalInsight,
    Profile,
    ReflectionFeedback,
    ReflectionGoal,
    SavedTeaching,
    VivekanandaComparison,
    WeeklyCheckIn,
    WeeklyReport,
    Message,
    AIRequestTrace,
)
from app.schemas import (
    AuthMeResponse,
    AuthResponse,
    ChangePasswordRequest,
    ClaimProfileRequest,
    LoginRequest,
    LogoutResponse,
    ProfileSnapshot,
    SignupRequest,
)
from app.services.auth import (
    find_account_by_email,
    find_active_session,
    hash_password,
    hash_session_token,
    issue_session,
    validate_email,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _profile_snapshot(profile: Profile, account: Account) -> ProfileSnapshot:
    return ProfileSnapshot(
        id=profile.id,
        display_name=profile.display_name,
        email=account.email,
        answers=profile.answers or {},
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _build_me(db: Session, profile: Profile, account: Account) -> AuthMeResponse:
    pid = profile.id
    counts = {
        "journal_entries": db.scalar(select(func.count()).select_from(JournalEntry).where(JournalEntry.profile_id == pid)) or 0,
        "journal_insights": db.scalar(select(func.count()).select_from(JournalInsight).where(JournalInsight.profile_id == pid)) or 0,
        "mentor_reflections": db.scalar(select(func.count()).select_from(Conversation).where(Conversation.profile_id == pid)) or 0,
        "mentor_messages": db.scalar(select(func.count()).select_from(Message).join(Conversation, Message.conversation_id == Conversation.id).where(Conversation.profile_id == pid)) or 0,
        "challenge_rounds": db.scalar(select(func.count()).select_from(ChallengeRound).join(Conversation, ChallengeRound.conversation_id == Conversation.id).where(Conversation.profile_id == pid)) or 0,
        "vivekananda_vs_me": db.scalar(select(func.count()).select_from(VivekanandaComparison).where(VivekanandaComparison.profile_id == pid)) or 0,
        "actions": db.scalar(select(func.count()).select_from(ActionItem).where(ActionItem.profile_id == pid)) or 0,
        "action_follow_ups": db.scalar(select(func.count()).select_from(ActionFollowUp).where(ActionFollowUp.profile_id == pid)) or 0,
        "weekly_checkins": db.scalar(select(func.count()).select_from(WeeklyCheckIn).where(WeeklyCheckIn.profile_id == pid)) or 0,
        "weekly_reports": db.scalar(select(func.count()).select_from(WeeklyReport).where(WeeklyReport.profile_id == pid)) or 0,
        "saved_teachings": db.scalar(select(func.count()).select_from(SavedTeaching).where(SavedTeaching.profile_id == pid)) or 0,
        "feedback": db.scalar(select(func.count()).select_from(ReflectionFeedback).where(ReflectionFeedback.profile_id == pid)) or 0,
        "interaction_records": db.scalar(select(func.count()).select_from(InteractionRecord).where(InteractionRecord.profile_id == pid)) or 0,
        "ai_request_traces": db.scalar(select(func.count()).select_from(AIRequestTrace).where(AIRequestTrace.profile_id == pid)) or 0,
        "has_reflection_goal": db.scalar(select(func.count()).select_from(ReflectionGoal).where(ReflectionGoal.profile_id == pid)) or 0,
    }
    return AuthMeResponse(
        account_id=account.id,
        profile=_profile_snapshot(profile, account),
        storage=counts,
    )


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    try:
        email = validate_email(payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if find_account_by_email(db, email):
        raise HTTPException(status_code=409, detail="An account with this email already exists. Please sign in instead.")

    profile = Profile(id=uuid.uuid4().hex, display_name=payload.display_name.strip(), answers={})
    account = Account(
        id=uuid.uuid4().hex,
        profile_id=profile.id,
        email=email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add_all([profile, account])
    token = issue_session(db, account, profile)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from exc
    db.refresh(profile)
    db.refresh(account)
    return AuthResponse(access_token=token, account_id=account.id, profile=_profile_snapshot(profile, account))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        email = validate_email(payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    account = find_account_by_email(db, email)
    if not account or not account.is_active or not verify_password(payload.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    profile = db.get(Profile, account.profile_id)
    if profile is None:
        raise HTTPException(status_code=500, detail="Account profile is missing.")
    token = issue_session(db, account, profile)
    account.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return AuthResponse(access_token=token, account_id=account.id, profile=_profile_snapshot(profile, account))


@router.post("/claim", response_model=AuthResponse, status_code=201)
def claim_anonymous_profile(payload: ClaimProfileRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    """Upgrade an existing anonymous profile token into an account without losing stored data."""
    if profile.access_token_hash is None:
        raise HTTPException(status_code=409, detail="This profile cannot be claimed with the current credential.")
    if db.scalar(select(Account.id).where(Account.profile_id == profile.id)):
        raise HTTPException(status_code=409, detail="This profile already has an account.")
    try:
        email = validate_email(payload.email)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if find_account_by_email(db, email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    account = Account(
        id=uuid.uuid4().hex,
        profile_id=profile.id,
        email=email,
        password_hash=hash_password(payload.password),
        is_active=True,
    )
    db.add(account)
    token = issue_session(db, account, profile)
    # The anonymous credential is no longer valid once the profile is upgraded.
    profile.access_token_hash = None
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from exc
    db.refresh(account)
    return AuthResponse(access_token=token, account_id=account.id, profile=_profile_snapshot(profile, account))


@router.get("/me", response_model=AuthMeResponse)
def me(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_profile_token: str | None = Header(default=None, alias="X-Profile-Token"),
    db: Session = Depends(get_db),
):
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif x_profile_token:
        token = x_profile_token.strip()
    if not token:
        raise HTTPException(status_code=401, detail="Bearer access token is required.")
    session = find_active_session(db, token)
    if not session:
        raise HTTPException(status_code=401, detail="Session is invalid or expired.")
    account = db.get(Account, session.account_id)
    profile = db.get(Profile, session.profile_id)
    if not account or not profile or not account.is_active:
        raise HTTPException(status_code=401, detail="Session is invalid.")
    db.commit()
    return _build_me(db, profile, account)


@router.post("/change-password", response_model=LogoutResponse)
def change_password(
    payload: ChangePasswordRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_profile_token: str | None = Header(default=None, alias="X-Profile-Token"),
    db: Session = Depends(get_db),
):
    token = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else (x_profile_token or "").strip()
    session = find_active_session(db, token) if token else None
    if not session:
        raise HTTPException(status_code=401, detail="Session is invalid or expired.")
    account = db.get(Account, session.account_id)
    if not account or not verify_password(payload.current_password, account.password_hash):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")
    account.password_hash = hash_password(payload.new_password)
    # Revoke every existing session so an old credential cannot remain active after a password change.
    now = datetime.now(timezone.utc)
    for row in db.scalars(select(AuthSession).where(AuthSession.account_id == account.id, AuthSession.revoked_at.is_(None))).all():
        row.revoked_at = now
    db.commit()
    return LogoutResponse(logged_out=True)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_profile_token: str | None = Header(default=None, alias="X-Profile-Token"),
    db: Session = Depends(get_db),
):
    token = authorization[7:].strip() if authorization and authorization.lower().startswith("bearer ") else (x_profile_token or "").strip()
    if token:
        session = db.scalar(select(AuthSession).where(AuthSession.token_hash == hash_session_token(token), AuthSession.revoked_at.is_(None)))
        if session:
            session.revoked_at = datetime.now(timezone.utc)
            db.commit()
    return LogoutResponse(logged_out=True)
