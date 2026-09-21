import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

HF_ROUTER_URL = f"https://router.huggingface.co/hf-inference/models/{settings.zeroshot_model_name}"
HF_LEGACY_URL = f"https://api-inference.huggingface.co/models/{settings.zeroshot_model_name}"

TOPIC_CANDIDATES = [
    "work stress",
    "relationship issues",
    "grief and loss",
    "anxiety",
    "loneliness",
    "self-worth and confidence",
    "family conflict",
    "existential concerns",
    "burnout",
    "life transition"
]

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


def _query_hf_topic(text: str) -> dict | None:
    token = settings.huggingface_api_token
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "inputs": text,
        "parameters": {
            "candidate_labels": TOPIC_CANDIDATES
        }
    }

    for url in [HF_ROUTER_URL, HF_LEGACY_URL]:
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    if "labels" in data and "scores" in data and len(data["labels"]) > 0:
                        top_topic = data["labels"][0]
                        top_score = round(data["scores"][0], 4)
                        logger.info(f"Hugging Face BART detected topic: {top_topic} ({top_score})")
                        return {
                            "topic": top_topic,
                            "score": top_score,
                        }
                elif res.status_code == 503:
                    logger.warning(f"HF model {settings.zeroshot_model_name} is loading: {res.text[:100]}")
                else:
                    logger.debug(f"HF topic status {res.status_code}: {res.text[:100]}")
        except Exception as e:
            logger.debug(f"HF topic call error to {url}: {e}")

    return None


def analyse_topic(text: str) -> dict:
    """
    Identifies the primary concern domain from the first message.
    Uses Hugging Face Serverless Inference (BART Zero-Shot) when configured,
    with local keyword fallback for reliability.
    """
    # 1. Attempt Hugging Face Serverless Inference
    hf_result = _query_hf_topic(text)
    if hf_result:
        return hf_result

    # 2. Local keyword fallback
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
