from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_profile
from app.db.session import get_db
from app.models import Profile
from app.services.growth import build_growth_journey

router = APIRouter(prefix="/growth-journey", tags=["growth-journey"])


@router.get("")
def growth_journey(db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    return build_growth_journey(db, profile.id)
