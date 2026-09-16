import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "end it all", "want to die",
    "hang myself", "cut myself", "self harm", "self-harm", "harm myself",
    "take all my pills", "better off dead", "don't want to live", "dont want to live",
]

HIGH_DISTRESS_KEYWORDS = [
    "break down", "breaking down", "falling apart", "cannot take this", "cant take this",
    "can't take this anymore", "cant do this anymore", "unbearable", "hopeless",
    "panic attack", "disturbed", "severe", "trauma", "agony", "suffering",
    "terrified", "paralyzed", "freaking out", "drowning",
]

MODERATE_DISTRESS_KEYWORDS = [
    "stressed", "stress", "anxious", "anxiety", "worried", "worry", "overwhelmed",
    "depressed", "sad", "crying", "lonely", "exhausted", "tired", "not ok", "not okay",
    "struggling", "hard time", "hurting", "lost", "confused", "in pain",
]


def analyse_severity(text: str) -> dict:
    """
    Classifies emotional severity.
    Output example:
    {
        "severity": "high",
        "score": 0.75,
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

    if any(kw in lower for kw in HIGH_DISTRESS_KEYWORDS):
        return {
            "severity": "high",
            "score": 0.75,
            "escalate": True,
            "crisis": False,
        }

    if any(kw in lower for kw in MODERATE_DISTRESS_KEYWORDS):
        return {
            "severity": "moderate",
            "score": 0.50,
            "escalate": False,
            "crisis": False,
        }

    return {
        "severity": "low",
        "score": 0.15,
        "escalate": False,
        "crisis": False,
    }
