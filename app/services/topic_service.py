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
        try:
            from transformers import pipeline
            logger.info(f"Loading zero-shot model for topics: {settings.zeroshot_model_name}")
            _zeroshot_pipeline = pipeline(
                "zero-shot-classification",
                model=settings.zeroshot_model_name,
                device=-1,
            )
            logger.info("Topic zero-shot model loaded")
        except Exception as e:
            logger.warning(f"Could not load zero-shot topic model ({e}). Using heuristic fallback.")
            return None
    return _zeroshot_pipeline


def analyse_topic(text: str) -> dict:
    """
    Identifies the primary concern domain from the first message with heuristic fallback.

    Output example:
    {
        "topic": "work stress",
        "score": 0.91
    }
    """
    try:
        pipe = _get_pipeline()
        if pipe is not None:
            result = pipe(text[:512], candidate_labels=TOPIC_LABELS)
            return {
                "topic": result["labels"][0],
                "score": round(result["scores"][0], 4),
            }
    except Exception as e:
        logger.warning(f"Topic classification failed: {e}")

    return {
        "topic": "general support",
        "score": 0.5,
    }
