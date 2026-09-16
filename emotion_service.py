from transformers import pipeline
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Lazy-loaded — model downloads on first request, cached after
_emotion_pipeline = None


def _get_pipeline():
    global _emotion_pipeline
    if _emotion_pipeline is None:
        try:
            logger.info(f"Loading emotion model: {settings.emotion_model_name}")
            _emotion_pipeline = pipeline(
                "text-classification",
                model=settings.emotion_model_name,
                top_k=None,                    # Return all emotion scores
                device=-1,                     # CPU (Render free tier has no GPU)
            )
            logger.info("Emotion model loaded")
        except Exception as e:
            logger.warning(f"Could not load emotion model ({e}). Using heuristic fallback.")
            return None
    return _emotion_pipeline


# Words that pattern-match to "surprise" in distilroberta but are
# semantically closer to fear or sadness in a support context.
_OVERWHELM_KEYWORDS = {
    "overwhelmed", "overwhelm", "don't know what to do",
    "dont know what to do", "lost", "helpless", "hopeless",
    "no idea", "confused", "can't cope", "cant cope",
    "falling apart", "breaking down",
}


def _remap_surprise(text: str, scores: dict) -> str:
    """
    distilroberta frequently maps 'overwhelmed / helpless' to 'surprise'
    because those words co-occur with unexpected events in training data.
    In a support context, if surprise dominates AND the text contains
    overwhelm/helplessness keywords, we defer to the second-highest emotion.
    """
    dominant = max(scores, key=scores.get)
    if dominant != "surprise":
        return dominant

    text_lower = text.lower()
    if any(kw in text_lower for kw in _OVERWHELM_KEYWORDS):
        # Pick best non-surprise emotion
        without_surprise = {k: v for k, v in scores.items() if k != "surprise"}
        return max(without_surprise, key=without_surprise.get)

    return dominant


def analyse_emotion(text: str) -> dict:
    """
    Returns dominant emotion and all scores with heuristic fallback.

    Output example:
    {
        "dominant_emotion": "sadness",
        "scores": {
            "sadness": 0.72, "fear": 0.14,
            "anger": 0.08, "joy": 0.02,
            "surprise": 0.02, "disgust": 0.02
        }
    }
    """
    try:
        pipe = _get_pipeline()
        if pipe is not None:
            results = pipe(text[:512])[0]          # Truncate to 512 tokens
            scores = {r["label"].lower(): round(r["score"], 4) for r in results}
            dominant = _remap_surprise(text, scores)
            return {"dominant_emotion": dominant, "scores": scores}
    except Exception as e:
        logger.warning(f"Emotion classification failed: {e}")

    # Heuristic fallback based on common distress words
    lower = text.lower()
    fallback_emotion = "neutral"
    if any(w in lower for w in ["sad", "crying", "depressed", "hurt", "grief", "loss", "pain"]):
        fallback_emotion = "sadness"
    elif any(w in lower for w in ["anxious", "scared", "fear", "worried", "panic", "stress"]):
        fallback_emotion = "fear"
    elif any(w in lower for w in ["angry", "furious", "mad", "hate", "irritated"]):
        fallback_emotion = "anger"
    elif any(w in lower for w in ["happy", "glad", "relief", "better", "joy"]):
        fallback_emotion = "joy"

    return {
        "dominant_emotion": fallback_emotion,
        "scores": {fallback_emotion: 0.8, "neutral": 0.2}
    }