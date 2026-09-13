from pydantic import BaseModel
from typing import List, Optional, Any


class ReportSection(BaseModel):
    presenting_concern: str
    emotional_tone: str
    key_themes: List[str]
    directions_given: List[str]
    risk_flags: List[str]
    recommendation: str


class ReportRequest(BaseModel):
    session_id: str
    messages: List[dict]
    topic: Optional[str] = None
    emotion_arc: List[Any] = []
    final_severity: str = "low"


class ReportResponse(BaseModel):
    session_id: str
    report: ReportSection
