import app.models  # noqa: F401
from app.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import Profile


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    with SessionLocal() as db:
        if db.get(Profile, settings.demo_user_id) is None:
            db.add(Profile(id=settings.demo_user_id, display_name="Friend", answers={}))
            db.commit()
