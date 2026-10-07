from app.bootstrap import seed_demo
from app.db.init_db import init_db
from app.db.session import SessionLocal


if __name__ == "__main__":
    init_db()
    with SessionLocal() as db:
        seed_demo(db)
        db.commit()
    print("Demo profile/data ready.")
