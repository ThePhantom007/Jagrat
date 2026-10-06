from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.config import get_settings
from app.db.session import get_db
from app.models import Profile


def get_profile_id(x_profile_id: str | None = Header(default=None)) -> str:
    # Hackathon mode: no auth. Frontend can use X-Profile-Id; otherwise use the single seeded demo user.
    return x_profile_id or get_settings().demo_user_id


def get_profile(profile_id: str = Depends(get_profile_id), db: Session = Depends(get_db)) -> Profile:
    profile = db.get(Profile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Create /api/profile first.")
    return profile
