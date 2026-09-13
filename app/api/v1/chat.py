from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.models.chat import ChatRequest, ChatResponse, MLSignals
from app.services.emotion_service import analyse_emotion
from app.services.severity_service import analyse_severity
from app.services.topic_service import analyse_topic
from app.services.gemini_service import get_karen_response
from app.core.database import get_supabase
import uuid
import logging

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("/message", response_model=ChatResponse)
async def send_message(
    payload: ChatRequest,
    user_hash: str = Depends(get_current_user),
):
    """
    Main chat endpoint.
    - Client sends last N messages from IndexedDB (stateless backend)
    - ML pipeline runs on the latest user message
    - Gemini generates Karen's response with ML context injected
    - Returns response + ML signals (client stores transcript locally)
    """
    if not payload.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    # Latest user message for ML analysis
    last_user_msg = next(
        (m.content for m in reversed(payload.messages) if m.role == "user"),
        None
    )
    if not last_user_msg:
        raise HTTPException(status_code=400, detail="No user message found")

    # ── ML Pipeline ───────────────────────────────────────────────────────────
    emotion_result = analyse_emotion(last_user_msg)
    severity_result = analyse_severity(last_user_msg)

    topic_result = None
    if payload.is_first_message:
        topic_result = analyse_topic(last_user_msg)

    ml_signals = {
        "dominant_emotion": emotion_result["dominant_emotion"],
        "emotion_scores": emotion_result["scores"],
        "severity": severity_result["severity"],
        "severity_score": severity_result["score"],
        "escalate": severity_result["escalate"],
        "crisis": severity_result["crisis"],
        "topic": topic_result["topic"] if topic_result else None,
    }

    # ── Gemini ────────────────────────────────────────────────────────────────
    karen_response = await get_karen_response(payload.messages, ml_signals)

    session_id = payload.session_id or str(uuid.uuid4())

    # ── Persist session metadata to Supabase (no transcript) ─────────────────
    db = get_supabase()
    try:
        db.table("session_turns").insert({
            "session_id": session_id,
            "user_hash": user_hash,
            "dominant_emotion": emotion_result["dominant_emotion"],
            "severity": severity_result["severity"],
            "severity_score": severity_result["score"],
            "topic": topic_result["topic"] if topic_result else None,
        }).execute()
    except Exception as e:
        logger.warning(f"Failed to persist turn metadata: {e}")
        # Non-fatal — chat continues even if metadata persistence fails

    return ChatResponse(
        response=karen_response,
        ml_signals=MLSignals(
            dominant_emotion=ml_signals["dominant_emotion"],
            emotion_scores=ml_signals["emotion_scores"],
            severity=ml_signals["severity"],
            severity_score=ml_signals["severity_score"],
            topic=ml_signals["topic"],
        ),
        escalate=ml_signals["escalate"],
        crisis=ml_signals["crisis"],
        session_id=session_id,
    )


@router.post("/end-session")
async def end_session(
    session_id: str,
    topic: str | None = None,
    final_severity: str = "low",
    user_hash: str = Depends(get_current_user),
):
    """Marks a session as ended in Supabase. Transcript stays client-side."""
    db = get_supabase()
    from datetime import datetime, timezone
    db.table("sessions").upsert({
        "session_id": session_id,
        "user_hash": user_hash,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "topic": topic,
        "final_severity": final_severity,
    }).execute()
    return {"status": "session ended", "session_id": session_id}
