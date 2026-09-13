from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.core.database import get_supabase
from app.models.session import SessionListItem

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/sessions", response_model=list[SessionListItem])
async def list_sessions(user_hash: str = Depends(get_current_user)):
    """Returns session metadata list for the user. No transcripts."""
    db = get_supabase()
    try:
        result = (
            db.table("sessions")
            .select("session_id, started_at, topic, final_severity, turn_count")
            .eq("user_hash", user_hash)
            .order("started_at", desc=True)
            .limit(50)
            .execute()
        )
        return result.data if result and result.data else []
    except Exception:
        return []


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, user_hash: str = Depends(get_current_user)):
    """Returns session metadata + emotion arc. No transcript."""
    db = get_supabase()

    try:
        session = (
            db.table("sessions")
            .select("*")
            .eq("session_id", session_id)
            .eq("user_hash", user_hash)
            .single()
            .execute()
        )
        session_data = session.data if session and session.data else None
    except Exception:
        session_data = None

    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        turns = (
            db.table("session_turns")
            .select("dominant_emotion, severity, severity_score")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        turns_data = turns.data if turns and turns.data else []
    except Exception:
        turns_data = []

    emotion_arc = [t["dominant_emotion"] for t in turns_data if "dominant_emotion" in t]

    return {**session_data, "emotion_arc": emotion_arc}
