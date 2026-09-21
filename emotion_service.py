import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

HF_ROUTER_URL = f"https://router.huggingface.co/hf-inference/models/{settings.emotion_model_name}"
HF_LEGACY_URL = f"https://api-inference.huggingface.co/models/{settings.emotion_model_name}"

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


def _query_hf_emotion(text: str) -> dict | None:
    token = settings.huggingface_api_token
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": text}

    for url in [HF_ROUTER_URL, HF_LEGACY_URL]:
        try:
            with httpx.Client(timeout=3.5) as client:
                res = client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list) and len(data) > 0:
                        items = data[0] if isinstance(data[0], list) else data
                        scores = {item["label"].lower(): round(item["score"], 4) for item in items if "label" in item and "score" in item}
                        if scores:
                            dominant = max(scores, key=scores.get)
                            logger.info(f"Hugging Face DistilRoBERTa detected: {dominant} ({scores[dominant]})")
                            return {
                                "dominant_emotion": dominant,
                                "scores": scores,
                            }
                elif res.status_code == 503:
                    logger.warning(f"HF model {settings.emotion_model_name} is loading: {res.text[:100]}")
                else:
                    logger.debug(f"HF emotion status {res.status_code}: {res.text[:100]}")
        except Exception as e:
            logger.debug(f"HF emotion call error to {url}: {e}")

    return None


def analyse_emotion(text: str) -> dict:
    """
    Classifies dominant emotion and provides score distribution.
    Uses Hugging Face Serverless Inference (DistilRoBERTa) when configured,
    with an ultra-fast local lexicon fallback for resilience.
    """
    # 1. Attempt Hugging Face Serverless Inference
    hf_result = _query_hf_emotion(text)
    if hf_result:
        return hf_result

    # 2. Resilient local lexicon fallback
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