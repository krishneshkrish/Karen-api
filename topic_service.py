from transformers import pipeline
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Reuses the same zero-shot pipeline as severity (loaded once, shared)
_zeroshot_pipeline = None

TOPIC_LABELS = [
    "work stress",
    "relationship issues",
    "grief and loss",
    "anxiety",
    "loneliness",
    "self-worth and confidence",
    "family conflict",
    "existential concerns",
    "burnout",
    "life transition",
]


def _get_pipeline():
    global _zeroshot_pipeline
    if _zeroshot_pipeline is None:
        logger.info(f"Loading zero-shot model for topics: {settings.zeroshot_model_name}")
        _zeroshot_pipeline = pipeline(
            "zero-shot-classification",
            model=settings.zeroshot_model_name,
            device=-1,
        )
        logger.info("Topic zero-shot model loaded")
    return _zeroshot_pipeline


def analyse_topic(text: str) -> dict:
    """
    Identifies the primary concern domain from the first message.

    Output example:
    {
        "topic": "work stress",
        "score": 0.91
    }
    """
    pipe = _get_pipeline()
    result = pipe(text[:512], candidate_labels=TOPIC_LABELS)

    return {
        "topic": result["labels"][0],
        "score": round(result["scores"][0], 4),
    }
