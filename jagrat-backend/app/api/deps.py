import hashlib

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import get_db
from app.models import Profile


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def get_profile_id(
    x_profile_token: str | None = Header(default=None, alias="X-Profile-Token"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_profile_id: str | None = Header(default=None, alias="X-Profile-Id"),
) -> str:
    settings = get_settings()
    bearer = None
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()
    token = (x_profile_token or bearer or "").strip()
    if token:
        return "token:" + _hash_token(token)
    if settings.demo_mode:
        return "id:" + settings.demo_user_id
    if settings.allow_legacy_profile_id and x_profile_id and x_profile_id.strip():
        return "id:" + x_profile_id.strip()
    raise HTTPException(status_code=401, detail="X-Profile-Token is required. Create a profile first.")


def get_profile(
    profile_key: str = Depends(get_profile_id),
    db: Session = Depends(get_db),
) -> Profile:
    if profile_key.startswith("token:"):
        profile = db.query(Profile).filter(Profile.access_token_hash == profile_key.removeprefix("token:")).first()
    elif profile_key.startswith("id:"):
        profile = db.get(Profile, profile_key.removeprefix("id:"))
    else:
        profile = None
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found or profile token is invalid.")
    return profile
