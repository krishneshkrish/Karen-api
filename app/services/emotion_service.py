import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

EMOTION_KEYWORDS = {
    "sadness": [
        "sad", "depressed", "cry", "crying", "unhappy", "sorrow", "heartbroken",
        "hopeless", "grief", "miserable", "down", "hurt", "pain", "lonely", "alone", "empty"
    ],
    "fear": [
        "afraid", "scared", "fear", "terrified", "anxious", "anxiety", "panic",
        "nervous", "worry", "worried", "stress", "stressed", "disturbed", "dread",
        "frightened", "paralyzed"
    ],
    "anger": [
        "angry", "mad", "furious", "rage", "hate", "annoyed", "irritated",
        "frustrated", "resentful", "bitter", "pissed", "infuriated"
    ],
    "joy": [
        "happy", "glad", "joy", "excited", "great", "relieved", "peaceful",
        "hopeful", "content", "grateful", "calm", "optimistic"
    ],
    "disgust": [
        "disgusted", "revolted", "sick", "nauseated", "gross", "repulsed", "loathe"
    ],
    "surprise": [
        "shocked", "surprised", "astonished", "stunned", "unexpected", "speechless"
    ],
}


def analyse_emotion(text: str) -> dict:
    """
    Classifies dominant emotion and provides score distribution.
    Lightweight, deterministic, and safe for low-memory environments (Render 512 MB).

    Output example:
    {
        "dominant_emotion": "sadness",
        "scores": {
            "sadness": 0.72, "fear": 0.14,
            "anger": 0.08, "joy": 0.02,
            "surprise": 0.02, "disgust": 0.02,
            "neutral": 0.05
        }
    }
    """
    lower = text.lower()

    scores = {
        "sadness": 0.05,
        "fear": 0.05,
        "anger": 0.05,
        "joy": 0.05,
        "disgust": 0.05,
        "surprise": 0.05,
        "neutral": 0.10,
    }

    matched = False
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[emotion] += 0.35
                matched = True

    if not matched:
        scores["neutral"] += 0.40

    total = sum(scores.values())
    normalized_scores = {k: round(v / total, 4) for k, v in scores.items()}
    dominant = max(normalized_scores, key=normalized_scores.get)

    return {
        "dominant_emotion": dominant,
        "scores": normalized_scores,
    }
