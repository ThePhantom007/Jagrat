from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import AIRequestTrace

with SessionLocal() as db:
    rows = list(db.scalars(select(AIRequestTrace).order_by(AIRequestTrace.created_at.desc()).limit(100)).all())
    for row in rows:
        print({
            "request_id": row.request_id,
            "operation": row.operation,
            "model": row.model,
            "candidate_ids": row.candidate_ids,
            "selected_quote_id": row.selected_quote_id,
            "safety_status": row.safety_status,
            "created_at": row.created_at.isoformat(),
        })
