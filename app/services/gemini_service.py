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

    raw_arc = context.get('emotion_arc', [])
    formatted_arc = []
    for item in raw_arc:
        if isinstance(item, dict):
            formatted_arc.append(str(item.get("emotion", item)))
        else:
            formatted_arc.append(str(item))

    prompt = f"""
You are an expert Clinical Psychologist and Psychiatric Assessor preparing a comprehensive Clinical Intake & Psychological Trajectory Report based on a mental health conversation.
This clinical document will be reviewed by an attending psychologist, psychiatrist, or clinical counsellor to evaluate the client's psychological history, diagnostic impressions, and treatment trajectory.

Conversation Transcript:
{transcript_text}

Session Context & Biomarkers:
- Primary Topic Identified: {context.get('topic', 'Not specified')}
- Emotion Trajectory Arc: {', '.join(formatted_arc) if formatted_arc else 'Not recorded'}
- Session Final Severity Tier: {context.get('final_severity', 'low')}

Return ONLY a valid JSON object with these exact keys:
{{
  "presenting_concern": "...",
  "client_story": "...",
  "emotional_tone": "...",
  "mental_status_observations": "...",
  "longitudinal_trajectory": [
    "Stage 1 (Initial Presentation): ...",
    "Stage 2 (Distress & Exploration): ...",
    "Stage 3 (Grounding & De-escalation): ..."
  ],
  "key_themes": ["...", "..."],
  "directions_given": ["...", "..."],
  "risk_flags": ["..."],
  "risk_assessment_tier": "Low | Moderate | High | Crisis",
  "clinician_notes": "...",
  "recommendation": "..."
}}

Clinical Guidelines for each field:
- presenting_concern: A concise clinical chief complaint (2-3 sentences) detailing the presenting issue and acute psychosocial stressors.
- client_story: The comprehensive chronological narrative ("the user's whole story"). Detail the background circumstances, interpersonal conflicts, work or family dynamics, what burden the client carried, and how the crisis or distress evolved. Write with clinical depth and empathy.
- emotional_tone: Affective assessment detailing the client's emotional range, baseline distress, emotional reactivity, and shifts observed across the session.
- mental_status_observations: Clinical observations on thought process (e.g. linear, circumstantial, ruminative), cognitive distortions noted (e.g. catastrophizing, all-or-nothing thinking, imposter feelings), and coping mechanisms.
- longitudinal_trajectory: A list of 3-5 chronological stages tracing the turn-by-turn progression of emotions and severity from beginning to end.
- key_themes: List of 3-5 core psychological themes (e.g. "Workplace Burnout & Chronic Overwhelm", "Attachment Insecurity", "Somatic Exhaustion").
- directions_given: Specific psychoeducational strategies, somatic grounding, or cognitive reframing techniques explored during the session.
- risk_flags: Explicit clinical flags concerning self-harm, passive/active suicidal ideation, severe hopelessness, or medical instability (or an empty list [] if none noted).
- risk_assessment_tier: One of "Low", "Moderate", "High", or "Crisis".
- clinician_notes: Specific clinical impressions for the treating psychologist or psychiatrist: suggested therapeutic modalities (e.g. CBT, ACT, Psychodynamic), key diagnostic differentials to explore during intake, and recommended inquiry avenues.
- recommendation: Formal triage and referral recommendation for human clinical care.

Strict Instructions: Return ONLY valid JSON. No markdown code blocks, no backticks, no text outside the JSON.
"""

    response = await model.generate_content_async(prompt)
    import json
    raw = response.text.strip().replace("```json", "").replace("```", "").strip()
    summary = json.loads(raw)

    # Ensure all clinical fields exist with sensible fallbacks
    defaults = {
        "presenting_concern": "Client presented for emotional processing and reflection.",
        "client_story": "The client engaged in an unhurried dialogue regarding personal stressors and emotional burden.",
        "emotional_tone": "Self-reflective and seeking emotional regulation.",
        "mental_status_observations": "Linear thought process with moments of heightened emotional vulnerability.",
        "longitudinal_trajectory": ["Stage 1: Presenting distress explored", "Stage 2: Coping and grounding evaluated"],
        "key_themes": ["Emotional Awareness", "Stress Regulation"],
        "directions_given": ["Diaphragmatic breathing", "Somatic grounding"],
        "risk_flags": [],
        "risk_assessment_tier": context.get("final_severity", "Low").capitalize(),
        "clinician_notes": "Recommend exploring primary stressors during initial clinical intake. Consider CBT or ACT modalities.",
        "recommendation": "Outpatient therapeutic support recommended for ongoing emotional grounding.",
    }
    for k, v in defaults.items():
        if k not in summary or not summary[k]:
            summary[k] = v

    return summary
