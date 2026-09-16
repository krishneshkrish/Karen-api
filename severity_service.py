from transformers import pipeline
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_zeroshot_pipeline = None

SEVERITY_LABELS = ["low distress", "moderate distress", "high distress", "crisis"]

# Map label → normalized key
LABEL_MAP = {
    "low distress": "low",
    "moderate distress": "moderate",
    "high distress": "high",
    "crisis": "crisis",
}


CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "end it all", "want to die",
    "hang myself", "cut myself", "self harm", "self-harm", "harm myself",
]


def _get_pipeline():
    global _zeroshot_pipeline
    if _zeroshot_pipeline is None:
        try:
            logger.info(f"Loading zero-shot model: {settings.zeroshot_model_name}")
            _zeroshot_pipeline = pipeline(
                "zero-shot-classification",
                model=settings.zeroshot_model_name,
                device=-1,
            )
            logger.info("Zero-shot model loaded")
        except Exception as e:
            logger.warning(f"Could not load zero-shot model ({e}). Using heuristic fallback.")
            return None
    return _zeroshot_pipeline


def analyse_severity(text: str) -> dict:
    """
    Classifies emotional severity using zero-shot NLI with heuristic fallback.

    Output example:
    {
        "severity": "high",
        "score": 0.74,
        "escalate": True,
        "crisis": False
    }
    """
    lower = text.lower()
    if any(kw in lower for kw in CRISIS_KEYWORDS):
        return {
            "severity": "crisis",
            "score": 0.95,
            "escalate": True,
            "crisis": True,
        }

    try:
        pipe = _get_pipeline()
        if pipe is not None:
            result = pipe(text[:512], candidate_labels=SEVERITY_LABELS)
            top_label = result["labels"][0]
            top_score = round(result["scores"][0], 4)
            severity = LABEL_MAP[top_label]

            return {
                "severity": severity,
                "score": top_score,
                "escalate": top_score >= settings.severity_escalate_threshold and severity in ("high", "crisis"),
                "crisis": severity == "crisis" and top_score >= settings.severity_crisis_threshold,
            }
    except Exception as e:
        logger.warning(f"Zero-shot severity classification failed: {e}")

    # Safe heuristic fallback
    return {
        "severity": "low",
        "score": 0.2,
        "escalate": False,
        "crisis": False,
    }
