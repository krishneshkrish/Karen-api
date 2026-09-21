from pydantic import BaseModel
from typing import List, Optional, Any


class ReportSection(BaseModel):
    presenting_concern: str
    client_story: Optional[str] = None
    emotional_tone: str
    mental_status_observations: Optional[str] = None
    longitudinal_trajectory: Optional[List[str]] = []
    key_themes: List[str]
    directions_given: List[str]
    risk_flags: List[str] = []
    risk_assessment_tier: Optional[str] = "Low"
    clinician_notes: Optional[str] = None
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
