import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

TOPIC_KEYWORDS = {
    "work stress": [
        "work", "job", "boss", "coworker", "colleague", "office", "career",
        "promotion", "deadline", "fired", "interview", "project", "workplace",
    ],
    "relationship issues": [
        "partner", "husband", "wife", "boyfriend", "girlfriend", "dating",
        "breakup", "broke up", "divorce", "ex", "marriage", "cheated", "cheating",
        "relationship", "significant other",
    ],
    "grief and loss": [
        "grief", "died", "death", "passed away", "lost my", "funeral", "mourning",
        "bereavement", "miss him", "miss her",
    ],
    "anxiety": [
        "anxious", "anxiety", "panic", "nervous", "scared", "worry", "worried",
        "disturbed", "fear", "overthinking", "restless", "on edge",
    ],
    "loneliness": [
        "lonely", "alone", "isolated", "nobody", "no friends", "abandoned",
        "no one to talk to", "empty",
    ],
    "self-worth and confidence": [
        "worthless", "failure", "hate myself", "ugly", "not good enough",
        "confidence", "insecure", "imposter", "ashamed", "shame", "useless",
    ],
    "family conflict": [
        "family", "mom", "dad", "parent", "parents", "mother", "father",
        "brother", "sister", "in-laws", "relatives", "household",
    ],
    "existential concerns": [
        "purpose", "meaning of life", "pointless", "why exist", "future",
        "what am i doing", "no direction",
    ],
    "burnout": [
        "burnout", "burnt out", "exhausted", "drained", "no energy",
        "cant go on", "tired all the time", "chronic fatigue",
    ],
    "life transition": [
        "moving", "new city", "college", "university", "graduating",
        "graduation", "retired", "new phase", "starting over",
    ],
}


def analyse_topic(text: str) -> dict:
    """
    Identifies the primary concern domain from the first message.
    Output example:
    {
        "topic": "work stress",
        "score": 0.80
    }
    """
    lower = text.lower()
    scores = {}

    for topic, keywords in TOPIC_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in lower)
        if count > 0:
            scores[topic] = count

    if scores:
        top_topic = max(scores, key=scores.get)
        confidence = round(min(0.55 + scores[top_topic] * 0.15, 0.95), 4)
        return {
            "topic": top_topic,
            "score": confidence,
        }

    return {
        "topic": "general support",
        "score": 0.5,
    }
