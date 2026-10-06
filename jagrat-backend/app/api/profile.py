from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
import uuid
import hashlib
import secrets

from app.api.deps import get_profile
from app.db.session import get_db
from app.models import Profile
from app.schemas import OnboardingRequest, ProfileCreateRequest, ProfileCreateResponse, ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", response_model=ProfileCreateResponse, status_code=201)
def create_profile(payload: ProfileCreateRequest, db: Session = Depends(get_db)):
    """Create an anonymous profile secured by an opaque access token (no password/account flow)."""
    access_token = secrets.token_urlsafe(32)
    profile = Profile(
        id=str(uuid.uuid4()),
        display_name=payload.display_name.strip(),
        answers={},
        access_token_hash=hashlib.sha256(access_token.encode("utf-8")).hexdigest(),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return ProfileCreateResponse(
        id=profile.id, display_name=profile.display_name, answers=profile.answers,
        created_at=profile.created_at, updated_at=profile.updated_at, access_token=access_token
    )


@router.get("", response_model=ProfileResponse)
def get_current_profile(profile: Profile = Depends(get_profile)):
    return profile


@router.put("", response_model=ProfileResponse)
def update_profile(payload: ProfileUpdateRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    """Update display name only; onboarding is changed only through /onboarding."""
    profile.display_name = payload.display_name.strip()
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/onboarding", response_model=ProfileResponse)
def save_onboarding(payload: OnboardingRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    profile.answers = payload.model_dump()
    db.commit()
    db.refresh(profile)
    return profile
