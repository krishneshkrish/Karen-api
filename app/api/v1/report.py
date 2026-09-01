from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.report import ReportRequest, ReportResponse, ReportSection
from app.services.gemini_service import generate_session_summary

router = APIRouter(prefix="/report", tags=["Report"])


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    payload: ReportRequest,
    user_hash: str = Depends(get_current_user),
):
    """
    Receives full transcript from client IndexedDB,
    generates structured summary via Gemini,
    returns JSON for client-side jsPDF rendering.
    Transcript is NOT stored server-side.
    """
    context = {
        "topic": payload.topic,
        "emotion_arc": payload.emotion_arc,
        "final_severity": payload.final_severity,
    }

    summary = await generate_session_summary(payload.messages, context)

    return ReportResponse(
        session_id=payload.session_id,
        report=ReportSection(**summary),
    )
