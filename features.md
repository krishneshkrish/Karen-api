# Karen — Features & Functionality Specification

Karen is an empathetic, privacy-first emotional support and direction-giving companion powered by a FastAPI backend, modern Hugging Face NLP classification pipelines, and Google Gemini 2.0.

---

## Table of Contents

1. [Core Philosophy & Companion Persona](#1-core-philosophy--companion-persona)
2. [Natural Language & Machine Learning Pipeline](#2-natural-language--machine-learning-pipeline)
3. [Privacy-First "Zero-Knowledge" Cloud Architecture](#3-privacy-first-zero-knowledge-cloud-architecture)
4. [Safety, Distress Detection & Crisis Escalation](#4-safety-distress-detection--crisis-escalation)
5. [Structured Session Reports & Therapist Handoff](#5-structured-session-reports--therapist-handoff)
6. [Session Lifecycle & Emotion Tracking](#6-session-lifecycle--emotion-tracking)
7. [Authentication & Security](#7-authentication--security)
8. [API Architecture & Endpoint Overview](#8-api-architecture--endpoint-overview)
9. [Operational & Infrastructure Features](#9-operational--infrastructure-features)

---

## 1. Core Philosophy & Companion Persona

Karen is designed to act as a grounded, thoughtful, and validating presence rather than an automated medical or diagnostic tool.

### 5-Stage Conversational Methodology
Each conversational exchange follows a structured guidance model:
1. **LISTEN**: Acknowledges and mirrors user input to establish trust and ensure the user feels understood prior to offering solutions.
2. **IDENTIFY**: Pinpoints the core emotional struggle or root problem, asking at most one focused clarifying question when necessary.
3. **ADDRESS**: Validates difficult feelings and names the emotional reality without cliché statements (e.g., explicitly avoids empty phrases like *"I understand how you feel"*).
4. **DIRECT**: Offers 2–3 clear, practical perspectives, cognitive reframings, or concrete next steps the user can act on.
5. **STAY**: Checks in on how the advice sits with the user, remaining attentive and present throughout the interaction.

### Conversational Tone & Boundaries
- **Tone**: Warm, grounded, calm, and friend-like. Free of academic jargon, clinical sterility, or artificial cheerfulness.
- **Form Factor**: Concise paragraphs; avoids bulleted lists during emotional dialogue to preserve natural speech rhythm.
- **Non-Therapy Disclaimer**: Explicitly not a licensed therapist or doctor. Does not diagnose, prescribe, or treat mental health conditions.
- **Transparency**: Never misleads the user regarding AI identity when asked directly.
- **Regional & Cultural Sensitivity**: Built-in awareness of cultural, familial, and regional contexts (including Indian helpline referrals: iCall `9152987821`, Vandrevala Foundation `1860-2662-345`, and NIMHANS).

---

## 2. Natural Language & Machine Learning Pipeline

Karen combines real-time local classification models with conversational large language models (LLMs) to understand emotional subtleties.

```
                    User Message (via Client)
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌───────────────────────────────┐     ┌───────────────────────────────┐
│     Emotion Classification    │     │      Distress & Severity      │
│  (distilroberta-base pipeline)│     │     (BART-large-MNLI NLI)     │
└───────────────┬───────────────┘     └───────────────┬───────────────┘
                │                                     │
                │     ┌───────────────────────────────┤
                │     │   Topic Domain Classification │ (First turn only)
                │     │     (BART-large-MNLI NLI)     │
                │     └───────────────┬───────────────┘
                ▼                     ▼
        ┌─────────────────────────────────────────┐
        │  Dynamic Prompt & ML Signal Injection   │
        └────────────────────┬────────────────────┘
                             ▼
        ┌─────────────────────────────────────────┐
        │        Google Gemini 2.0 Flash          │
        │   Contextual, Empathetic Response Gen   │
        └─────────────────────────────────────────┘
```

### 1. Emotion Classification (`j-hartmann/emotion-english-distilroberta-base`)
- Runs via Hugging Face Transformers pipeline (CPU-optimized for serverless/containerized deployment).
- Computes granular probability scores across 6 core affective states:
  - Joy
  - Sadness
  - Anger
  - Fear
  - Disgust
  - Surprise
- **Domain-Specific Surprise Heuristic**:
  - DistilRoBERTa often misattributes distress phrases to `"surprise"`.
  - An intelligent override re-maps expressions like *"overwhelmed"*, *"lost"*, *"can't cope"*, *"falling apart"*, and *"hopeless"* to the second highest emotion (typically sadness or fear) to preserve conversational accuracy.

### 2. Zero-Shot Distress & Severity Analysis (`facebook/bart-large-mnli`)
- Natural Language Inference (NLI) zero-shot classifier categorizes user input into four distinct tiers:
  - `low distress`
  - `moderate distress`
  - `high distress`
  - `crisis`
- Flags actionable thresholds:
  - **Escalate Threshold (`>= 0.65`)**: Detects severe distress requiring professional human consultation suggestions.
  - **Crisis Threshold (`>= 0.80`)**: Triggers urgent crisis intervention workflows.

### 3. Concern Domain & Topic Identification
- Reuses the loaded `facebook/bart-large-mnli` pipeline without additional model memory overhead.
- Triggered on session initiation to detect the primary conversational anchor from 10 distinct domains:
  - Work stress
  - Relationship issues
  - Grief and loss
  - Anxiety
  - Loneliness
  - Self-worth and confidence
  - Family conflict
  - Existential concerns
  - Burnout
  - Life transition

### 4. Conversational Generation (Google Gemini 2.0 Flash)
- Ingests a sliding message context window (up to 10 recent messages).
- **Silent System Context Injection**: Injects dominant emotion, topic domain, and distress level into the system instructions. The LLM calibrates warmth, empathy, and directionality without repeating analytical labels to the user.

---

## 3. Privacy-First "Zero-Knowledge" Cloud Architecture

Karen is architected so that personal conversations remain strictly confidential and out of server databases.

```
┌────────────────────────────────────────────────────────┐
│                     Client Device                      │
│                                                        │
│  [IndexedDB / Local Storage]                           │
│  ├── Full Chat History & Raw Transcripts               │
│  └── Saved Session Reports                             │
└──────────────┬───────────────────────────▲─────────────┘
               │ (Sliding context only)    │ (Response + ML signals)
               ▼                           │
┌────────────────────────────────────────────────────────┐
│                   Karen FastAPI Backend                │
│                                                        │
│  ├── Stateless processing (transcripts NOT saved)      │
│  └── Email Hashed via HMAC-SHA256 (user_hash)          │
└──────────────┬─────────────────────────────────────────┘
               │ (Only turn metadata & emotion arc)
               ▼
┌────────────────────────────────────────────────────────┐
│                    Supabase Database                   │
│                                                        │
│  ├── users (user_hash, password_hash)                  │
│  ├── sessions (session_id, timestamps, topic, severity)│
│  └── session_turns (dominant_emotion, severity_score)  │
└────────────────────────────────────────────────────────┘
```

- **Stateless Server Processing**: Raw conversation text is never written to cloud disks or relational databases. Transcripts live in the client's local IndexedDB.
- **HMAC Email Obfuscation**: The user's actual email address is never stored in Supabase. It is deterministically hashed using HMAC-SHA256 with a server secret key to generate an irreversible `user_hash`.
- **Anonymized Emotion Arcs**: The database only tracks high-level session trajectories (e.g., `sadness` $\rightarrow$ `fear` $\rightarrow$ `joy`, severity scores, and turn counts).
- **Supabase Row Level Security (RLS)**: Strict `service_only` policies block direct client key reads/writes; all persistence is mediated through the authenticated backend.
- **Opt-In Anonymized ML Signals**: Decoupled, fully anonymized `ml_signals` table stores emotion/severity/topic labels for offline model tuning without any user identifiers.

---

## 4. Safety, Distress Detection & Crisis Escalation

When user input indicates extreme emotional weight, Karen seamlessly activates elevated care protocols:

### High Distress Escalation Protocol
- **Condition**: Severity score $\ge 0.65$ with severity rated as `high` or `crisis`.
- **Action**: Dynamically appends an `ESCALATE_ADDENDUM` to Gemini's system prompt.
- **Outcome**: Karen delivers validating support, followed by a gentle, non-alarmist recommendation that the user's situation warrants human-led therapy or counseling (e.g., *"what you're carrying sounds like it deserves more than I can offer"*).

### Crisis Intervention Protocol
- **Condition**: Explicit mentions of self-harm, suicidal ideation, or severity score $\ge 0.80$ marked as `crisis`.
- **Action**: Injects `CRISIS_ADDENDUM` directly overriding standard conversational direction.
- **Outcome**:
  - Halts general advice or problem-solving.
  - Expresses immediate care and empathy.
  - Directly provides actionable emergency hotlines (e.g., iCall: `9152987821`, Vandrevala Foundation: `1860-2662-345`, NIMHANS).
  - Emphasizes human support and safety first.

---

## 5. Structured Session Reports & Therapist Handoff

Users have the option to generate structured session summaries for personal reflection or to share with a mental health professional.

### Report Generation Process (`/api/v1/report/generate`)
1. Client securely transmits the session transcript and metadata (topic, emotion arc, final severity) from IndexedDB.
2. Karen uses Gemini to parse and synthesize the interaction into a strictly formatted JSON report schema:
   - **`presenting_concern`**: 2–3 sentence synopsis of why the user initiated the session.
   - **`emotional_tone`**: Description of how the user's affective state evolved throughout the discussion.
   - **`key_themes`**: 2–4 core recurring behavioral or emotional patterns.
   - **`directions_given`**: Summary of concrete perspectives and action items proposed by Karen.
   - **`risk_flags`**: Explicit indicators of self-harm, severe distress, or crisis (if observed).
   - **`recommendation`**: Contextual suggestion regarding professional care.
3. The server immediately releases the transcript from memory; the client renders the structured JSON into a downloadable PDF (e.g., using `jsPDF`).

---

## 6. Session Lifecycle & Emotion Tracking

### Session Flow
- **Initialization**: First message triggers topic categorization (`is_first_message=True`).
- **Turn Progression**: Each message evaluates emotional shift and severity, recording turn-level metadata in `session_turns`.
- **Session Termination (`/api/v1/chat/end-session`)**:
  - Records session completion timestamp, identified topic, and resolved distress level in the `sessions` table.
- **History Exploration (`/api/v1/history/sessions`)**:
  - Users can view a dashboard of past sessions with timestamps, topics, and duration.
  - Detail view reconstructs the user's **Emotion Arc** across turns without ever retaining or exposing raw chat logs.

---

## 7. Authentication & Security

- **Bcrypt Password Encryption**: Passwords salted and hashed with bcrypt (including 72-byte truncation protections).
- **JWT Authorization**: JSON Web Tokens (HS256) signed with server secret key, configured with 7-day expiration.
- **Stateless Verification**: Bearer tokens are decoded on protected routes via FastAPI dependency injection (`get_current_user`).
- **CORS Protection**: Whitelisted origins supporting local frontend development (`localhost:5173`, `localhost:5180`) and production deployment (`karen-app.vercel.app`).
- **Rate Limiting**: Integrated `slowapi` rate-limiter:
  - 10 requests per minute (matches Gemini free tier RPM limits).
  - 200 requests per day per user cap to prevent abuse and manage API costs.

---

## 8. API Architecture & Endpoint Overview

| Router | Method | Path | Description | Auth Required |
| :--- | :---: | :--- | :--- | :---: |
| **Root** | `GET` | `/` | API status message | No |
| **Health** | `GET` | `/health` | Service health status for keep-alive pings | No |
| **Auth** | `POST` | `/api/v1/auth/register` | Registers new user with HMAC-hashed identifier | No |
| **Auth** | `POST` | `/api/v1/auth/login` | Authenticates credentials, returns JWT & user_hash | No |
| **Chat** | `POST` | `/api/v1/chat/message` | Evaluates user turn via ML, returns Karen's reply & signals | Yes |
| **Chat** | `POST` | `/api/v1/chat/end-session` | Finalizes session state, end time, and severity | Yes |
| **ML** | `POST` | `/api/v1/ml/emotion` | Standalone emotion classification test endpoint | Yes |
| **ML** | `POST` | `/api/v1/ml/severity` | Standalone distress/severity test endpoint | Yes |
| **ML** | `POST` | `/api/v1/ml/topic` | Standalone topic domain classification endpoint | Yes |
| **History** | `GET` | `/api/v1/history/sessions` | Lists user's session history (up to 50 records) | Yes |
| **History** | `GET` | `/api/v1/history/sessions/{session_id}` | Retrieves session metadata and chronological emotion arc | Yes |
| **Report** | `POST` | `/api/v1/report/generate` | Compiles structured handoff JSON from local transcript | Yes |

---

## 9. Operational & Infrastructure Features

- **Containerization**: Includes production `Dockerfile` utilizing lightweight `python:3.11-slim` with optimized layer caching.
- **Free-Tier Render Cold-Start Mitigation**: Background asynchronous task (`ping_self`) automatically pings `/health` every 14 minutes to prevent Render free-tier containers from spinning down due to inactivity.
- **Lazy Model Loading**: Transformers pipelines (`distilroberta-base`, `bart-large-mnli`) load on first request and remain memory-cached for subsequent turns.
- **Environment-Driven Configuration**: Centralized configuration management with `pydantic-settings` reading from `.env`.
- **Conditional API Documentation**: Swagger UI docs enabled in debug mode and automatically hidden in production for security.
