from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_profile
from app.config import get_settings
from app.db.session import get_db
from app.models import Profile
from app.schemas import OnboardingRequest, ProfileResponse, ProfileUpsertRequest

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_current_profile(profile: Profile = Depends(get_profile)):
    return profile


@router.put("", response_model=ProfileResponse)
def upsert_profile(payload: ProfileUpsertRequest, db: Session = Depends(get_db)):
    profile_id = get_settings().demo_user_id
    profile = db.get(Profile, profile_id)
    if profile is None:
        profile = Profile(id=profile_id)
        db.add(profile)
    profile.display_name = payload.display_name.strip()
    profile.answers = payload.answers
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/onboarding", response_model=ProfileResponse)
def save_onboarding(payload: OnboardingRequest, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    answers = dict(profile.answers or {})
    answers.update(payload.model_dump())
    profile.answers = answers
    db.commit()
    db.refresh(profile)
    return profile
