from pydantic import BaseModel
from typing import List, Optional, Dict


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    messages: List[Message]
    is_first_message: bool = False


class MLSignals(BaseModel):
    dominant_emotion: str
    emotion_scores: Dict[str, float]
    severity: str
    severity_score: float
    topic: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    ml_signals: MLSignals
    escalate: bool
    crisis: bool
    session_id: str
