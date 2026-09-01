from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.ml import (
    EmotionRequest, EmotionResponse,
    SeverityRequest, SeverityResponse,
    TopicRequest, TopicResponse,
)
from app.services.emotion_service import analyse_emotion
from app.services.severity_service import analyse_severity
from app.services.topic_service import analyse_topic

router = APIRouter(prefix="/ml", tags=["ML"])


@router.post("/emotion", response_model=EmotionResponse)
async def emotion(payload: EmotionRequest, _: str = Depends(get_current_user)):
    result = analyse_emotion(payload.text)
    return EmotionResponse(dominant_emotion=result["dominant_emotion"], scores=result["scores"])


@router.post("/severity", response_model=SeverityResponse)
async def severity(payload: SeverityRequest, _: str = Depends(get_current_user)):
    result = analyse_severity(payload.text)
    return SeverityResponse(**result)


@router.post("/topic", response_model=TopicResponse)
async def topic(payload: TopicRequest, _: str = Depends(get_current_user)):
    result = analyse_topic(payload.text)
    return TopicResponse(**result)
