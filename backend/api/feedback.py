"""Feedback API — saves to PostgreSQL."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import structlog
from db.database import save_feedback, get_pool

log = structlog.get_logger()
router = APIRouter()

# In-memory fallback if DB is down
_fallback_feedbacks = []


class FeedbackRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    rating: int
    helpful: Optional[str] = None
    what_liked: Optional[str] = None
    improve: Optional[str] = None
    use_case: Optional[str] = None
    language: str = 'en'
    submitted_at: Optional[str] = None


@router.post("/feedback", tags=["Feedback"])
async def submit_feedback(body: FeedbackRequest):
    data = body.model_dump()
    saved = await save_feedback(data)
    if not saved:
        # Fallback to memory
        _fallback_feedbacks.append({**data, "server_time": datetime.utcnow().isoformat()})
        log.warning("feedback_saved_to_memory_fallback")
    return {"status": "ok", "message": "Thank you for your feedback!", "saved_to_db": saved}


@router.get("/feedback", tags=["Feedback"])
async def get_feedbacks(limit: int = 100):
    """Admin — view all feedback from DB."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, email, rating, helpful, what_liked,
                       improve, use_case, language, submitted_at
                FROM feedback
                ORDER BY submitted_at DESC
                LIMIT $1
            """, limit)
        total = await conn.fetchval("SELECT COUNT(*) FROM feedback") if rows else 0
        avg   = await conn.fetchval("SELECT AVG(rating) FROM feedback") if rows else None
        return {
            "total": total,
            "avg_rating": round(float(avg), 1) if avg else None,
            "feedbacks": [dict(r) for r in rows]
        }
    except Exception as e:
        # Return in-memory fallback
        return {
            "total": len(_fallback_feedbacks),
            "avg_rating": None,
            "feedbacks": _fallback_feedbacks[-limit:],
            "note": f"DB unavailable: {e}"
        }
