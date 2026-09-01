from pydantic import BaseModel
from typing import Dict


class EmotionRequest(BaseModel):
    text: str


class EmotionResponse(BaseModel):
    dominant_emotion: str
    scores: Dict[str, float]


class SeverityRequest(BaseModel):
    text: str


class SeverityResponse(BaseModel):
    severity: str
    score: float
    escalate: bool
    crisis: bool


class TopicRequest(BaseModel):
    text: str


class TopicResponse(BaseModel):
    topic: str
    score: float
