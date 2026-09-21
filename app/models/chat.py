from pydantic import BaseModel
from typing import List, Optional, Dict


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    messages: List[Message]
    is_first_message: bool = False


class EndSessionRequest(BaseModel):
    session_id: str
    topic: Optional[str] = None
    final_severity: Optional[str] = "low"


class MLSignals(BaseModel):
    dominant_emotion: str
    emotion_scores: Dict[str, float]
    severity: str
    severity_score: float
    topic: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    reply: Optional[str] = None
    ml_signals: MLSignals
    detected_emotion: Optional[str] = None
    escalate: bool
    crisis: bool
    crisis_flag: Optional[bool] = None
    session_id: str
