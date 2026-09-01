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


def _get_pipeline():
    global _zeroshot_pipeline
    if _zeroshot_pipeline is None:
        logger.info(f"Loading zero-shot model: {settings.zeroshot_model_name}")
        _zeroshot_pipeline = pipeline(
            "zero-shot-classification",
            model=settings.zeroshot_model_name,
            device=-1,
        )
        logger.info("Zero-shot model loaded")
    return _zeroshot_pipeline


def analyse_severity(text: str) -> dict:
    """
    Classifies emotional severity using zero-shot NLI.

    Output example:
    {
        "severity": "high",
        "score": 0.74,
        "escalate": True,
        "crisis": False
    }
    """
    pipe = _get_pipeline()
    result = pipe(text[:512], candidate_labels=SEVERITY_LABELS)

    # result["labels"] is sorted by score descending
    top_label = result["labels"][0]
    top_score = round(result["scores"][0], 4)
    severity = LABEL_MAP[top_label]

    return {
        "severity": severity,
        "score": top_score,
        "escalate": top_score >= settings.severity_escalate_threshold and severity in ("high", "crisis"),
        "crisis": severity == "crisis" and top_score >= settings.severity_crisis_threshold,
    }
