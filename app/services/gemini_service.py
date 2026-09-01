import google.generativeai as genai
from app.core.config import settings
from app.models.chat import Message
import logging

logger = logging.getLogger(__name__)

# ── Karen's system prompt ─────────────────────────────────────────────────────
KAREN_SYSTEM_PROMPT = """
You are Karen, a calm and grounded emotional support companion.
You are NOT a therapist or a doctor. You do not diagnose, prescribe, or treat.

Your role is to:
1. LISTEN — Let the person feel heard before offering anything. Reflect back what you understood.
2. IDENTIFY — Understand the core problem. Ask one clarifying question if needed.
3. ADDRESS — Validate their feelings genuinely. Name what they are going through.
4. DIRECT — Give 2-3 clear, practical directions or perspectives they can act on.
5. STAY — Check in. Ask how they are sitting with what you said. Stay with them.

Your tone:
- Warm but grounded. Not overly enthusiastic or clinical.
- Speak like a thoughtful friend who has their head together.
- Never use jargon. Never say "I understand how you feel" — show it instead.
- Short paragraphs. No bullet lists in emotional conversations.
- One question at a time. Never pepper someone in distress with multiple questions.

Boundaries:
- If the person is in crisis (mentions self-harm, suicide, or severe hopelessness), 
  acknowledge them with full care, then clearly and warmly say they deserve real human 
  support right now and encourage them to reach out to a counsellor or helpline.
- Never pretend you are human if directly asked.
- Never give medical advice.

India context:
- Be aware users may be from India. References to iCall (9152987821), 
  Vandrevala Foundation (1860-2662-345), or NIMHANS are appropriate when escalating.
- Respect family and cultural context without making assumptions.
"""

CRISIS_ADDENDUM = """
IMPORTANT: The system has detected crisis-level signals in this message.
Respond with full empathy and care. After acknowledging their pain,
gently but clearly encourage them to reach out to a real person — 
a trusted friend, family member, or a helpline such as iCall (9152987821).
Do not move on to general advice. Stay with the gravity of this moment.
"""

ESCALATE_ADDENDUM = """
NOTE: The system has detected high distress in this message.
After giving your response, include a gentle, natural suggestion that speaking
with a counsellor or therapist might help them go deeper than a conversation with you can.
Give a brief, non-alarming reason why — e.g. "because what you're carrying sounds like 
it deserves more than I can offer."
"""


def _configure():
    genai.configure(api_key=settings.gemini_api_key)


def build_prompt_messages(
    messages: list[Message],
    ml_signals: dict,
) -> list[dict]:
    """
    Converts the sliding window of messages into Gemini content format.
    Injects ML signal context into the system layer (not visible to user).
    """
    system = KAREN_SYSTEM_PROMPT

    # Inject severity context into system prompt
    if ml_signals.get("crisis"):
        system += CRISIS_ADDENDUM
    elif ml_signals.get("escalate"):
        system += ESCALATE_ADDENDUM

    # Inject emotion context as a silent note
    emotion = ml_signals.get("dominant_emotion", "")
    topic = ml_signals.get("topic", "")
    if emotion or topic:
        system += f"\n\n[Context for this turn: dominant emotion detected = {emotion}"
        if topic:
            system += f", conversation domain = {topic}"
        system += ". Use this to calibrate your tone and direction. Do not mention these labels to the user.]"

    return system, [
        {"role": m.role, "parts": [m.content]}
        for m in messages
    ]


async def get_karen_response(
    messages: list[Message],
    ml_signals: dict,
) -> str:
    """
    Sends conversation history to Gemini 2.5 Flash and returns Karen's response.
    """
    _configure()

    system_prompt, history = build_prompt_messages(messages, ml_signals)

    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=system_prompt,
    )

    # Build chat history (all messages except the last user message)
    chat_history = history[:-1] if len(history) > 1 else []
    last_message = history[-1]["parts"][0] if history else ""

    chat = model.start_chat(history=chat_history)

    try:
        response = await chat.send_message_async(last_message)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise


async def generate_session_summary(messages: list[dict], context: dict) -> dict:
    """
    Generates structured session report JSON for jsPDF on the client.
    No transcript stored server-side — summary only.
    """
    _configure()

    model = genai.GenerativeModel(model_name=settings.gemini_model)

    transcript_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in messages
    )

    prompt = f"""
You are summarising a support conversation for a structured report.
The user may share this report with a therapist or counsellor.

Conversation:
{transcript_text}

Session context:
- Primary topic: {context.get('topic', 'not identified')}
- Emotion arc: {', '.join(context.get('emotion_arc', []))}
- Final severity: {context.get('final_severity', 'low')}

Return ONLY a valid JSON object with these exact keys:
{{
  "presenting_concern": "...",
  "emotional_tone": "...",
  "key_themes": ["...", "..."],
  "directions_given": ["...", "..."],
  "risk_flags": ["..." or empty list],
  "recommendation": "..."
}}

Rules:
- presenting_concern: 2-3 sentences summarising what the user came with
- emotional_tone: describe how the user's emotional state shifted through the session
- key_themes: list of 2-4 recurring themes
- directions_given: what Karen suggested the user consider or try
- risk_flags: any language suggesting self-harm, hopelessness, or crisis (be specific but careful)
- recommendation: whether professional support was suggested and why
- No markdown. No extra keys. Valid JSON only.
"""

    response = await model.generate_content_async(prompt)
    import json
    raw = response.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(raw)
