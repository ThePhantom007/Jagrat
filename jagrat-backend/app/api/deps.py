import hashlib
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.models import Account, AuthSession, Profile


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _extract_token(x_profile_token: str | None, authorization: str | None) -> str:
    bearer = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()
    return (x_profile_token or bearer or "").strip()


def get_profile_id(
    x_profile_token: str | None = Header(default=None, alias="X-Profile-Token"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_profile_id: str | None = Header(default=None, alias="X-Profile-Id"),
) -> str:
    settings = get_settings()
    token = _extract_token(x_profile_token, authorization)
    if token:
        return "token:" + _hash_token(token)
    if settings.demo_mode:
        return "id:" + settings.demo_user_id
    if settings.allow_legacy_profile_id and x_profile_id and x_profile_id.strip():
        return "id:" + x_profile_id.strip()
    raise HTTPException(status_code=401, detail="Authentication is required. Sign up or sign in first.")


def get_profile(
    profile_key: str = Depends(get_profile_id),
    db: Session = Depends(get_db),
) -> Profile:
    if profile_key.startswith("token:"):
        token_hash = profile_key.removeprefix("token:")
        profile = db.query(Profile).filter(Profile.access_token_hash == token_hash).first()
        if profile:
            return profile
        now = datetime.now(timezone.utc)
        session = db.scalar(
            select(AuthSession).where(
                AuthSession.token_hash == token_hash,
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > now,
            )
        )
        if session:
            session.last_seen_at = now
            profile = db.get(Profile, session.profile_id)
            if profile:
                db.commit()
                return profile
    elif profile_key.startswith("id:"):
        profile = db.get(Profile, profile_key.removeprefix("id:"))
        if profile:
            return profile
    raise HTTPException(status_code=404, detail="Profile not found or authentication token is invalid.")


def get_auth_session(
    x_profile_token: str | None = Header(default=None, alias="X-Profile-Token"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> tuple[AuthSession, Account, Profile]:
    token = _extract_token(x_profile_token, authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Bearer access token is required.")
    now = datetime.now(timezone.utc)
    session = db.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == _hash_token(token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
        )
    )
    if not session:
        raise HTTPException(status_code=401, detail="Session is invalid or expired.")
    account = db.get(Account, session.account_id)
    profile = db.get(Profile, session.profile_id)
    if not account or not profile or not account.is_active:
        raise HTTPException(status_code=401, detail="Session is invalid.")
    session.last_seen_at = now
    db.commit()
    return session, account, profile
