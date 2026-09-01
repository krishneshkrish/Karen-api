from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.core.database import get_supabase
from app.models.session import SessionListItem

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/sessions", response_model=list[SessionListItem])
async def list_sessions(user_hash: str = Depends(get_current_user)):
    """Returns session metadata list for the user. No transcripts."""
    db = get_supabase()
    result = (
        db.table("sessions")
        .select("session_id, started_at, topic, final_severity, turn_count")
        .eq("user_hash", user_hash)
        .order("started_at", desc=True)
        .limit(50)
        .execute()
    )
    return result.data


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, user_hash: str = Depends(get_current_user)):
    """Returns session metadata + emotion arc. No transcript."""
    db = get_supabase()

    session = (
        db.table("sessions")
        .select("*")
        .eq("session_id", session_id)
        .eq("user_hash", user_hash)
        .single()
        .execute()
    )

    turns = (
        db.table("session_turns")
        .select("dominant_emotion, severity, severity_score")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )

    emotion_arc = [t["dominant_emotion"] for t in turns.data]

    return {**session.data, "emotion_arc": emotion_arc}
