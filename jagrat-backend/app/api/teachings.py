from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_profile
from app.db.session import get_db
from app.models import Profile, Teaching

router = APIRouter(prefix="/teachings", tags=["teachings"])


@router.get("")
def list_teachings(query: str | None = None, db: Session = Depends(get_db), profile: Profile = Depends(get_profile)):
    rows = list(db.scalars(select(Teaching).where(Teaching.is_active.is_(True))).all())
    if query:
        q = query.lower()
        rows = [
            t for t in rows
            if q in f"{t.quote} {' '.join(t.themes or [])} {' '.join(t.keywords or [])} {t.context or ''}".lower()
        ]
    return [
        {
            "id": t.id,
            "quote": t.quote,
            "themes": t.themes,
            "source": {
                "type": t.source_type,
                "title": t.source_title,
                "volume": t.source_volume,
                "chapter": t.source_chapter,
                "page": t.source_page,
                "section": t.source_section,
                "url": t.source_url,
                "authority": "organizer_provided_json",
            },
        }
        for t in rows[:50]
    ]
