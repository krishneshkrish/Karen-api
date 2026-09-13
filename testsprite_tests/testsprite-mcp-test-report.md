# TestSprite AI Testing Report (MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** Karen
- **Date:** 2026-09-13
- **Prepared by:** TestSprite AI Team
- **Test Framework:** TestSprite MCP (Python / Requests Test Runner)
- **Target Endpoint:** http://localhost:8099
- **Environment:** Development (Local Python FastAPI + Uvicorn)
- **Execution Status:** Complete — 100% Pass Rate

---

## 2️⃣ Requirement Validation Summary

### Requirement: System Health & Status
Validates foundational availability and connectivity of the Karen API service without authentication.

#### Test TC001 get_root_api_running_status
- **Test Code:** [TC001_get_root_api_running_status.py](./TC001_get_root_api_running_status.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/48e76c4a-9d2b-54bd-9638-84632dffec91/test/25a88858-66e4-4984-bb7a-c736a537ae0b
- **Status:** ✅ Passed
- **Analysis / Findings:** Verified that `GET /` responds with HTTP 200 and the expected status payload `{"message": "Karen API is running"}`. Unauthenticated access works as designed.

#### Test TC002 get_health_endpoint_status
- **Test Code:** [TC002_get_health_endpoint_status.py](./TC002_get_health_endpoint_status.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/48e76c4a-9d2b-54bd-9638-84632dffec91/test/19181505-16f9-408b-8031-978f51ecb4ad
- **Status:** ✅ Passed
- **Analysis / Findings:** Verified that `GET /health` responds with HTTP 200 and payload `{"status": "ok", "service": "Karen API"}`. The keep-alive and health monitoring endpoint is fully operational.

---

### Requirement: User Authentication & Account Management
Validates user onboarding, password hashing via bcrypt, HMAC-SHA256 email hashing, and JWT token issuance and verification.

#### Test TC003 post_user_registration_with_valid_data
- **Test Code:** [TC003_post_user_registration_with_valid_data.py](./TC003_post_user_registration_with_valid_data.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/48e76c4a-9d2b-54bd-9638-84632dffec91/test/120fe268-dd5a-4dc3-b8d0-db58f74359e3
- **Status:** ✅ Passed
- **Analysis / Findings:** Successfully registered user via `POST /api/v1/auth/register`. Returned HTTP 201 Created with valid `access_token`, `token_type`, and deterministic HMAC `user_hash`. Resilient database fallback ensured persistence even during cloud Supabase network outages.

#### Test TC004 post_user_login_with_valid_credentials
- **Test Code:** [TC004_post_user_login_with_valid_credentials.py](./TC004_post_user_login_with_valid_credentials.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/48e76c4a-9d2b-54bd-9638-84632dffec91/test/a2b21ed7-9b60-4fcb-9133-431e2e089001
- **Status:** ✅ Passed
- **Analysis / Findings:** Verified user authentication via `POST /api/v1/auth/login`. Password verification with bcrypt matched stored hashes and issued a valid signed JWT bearer token.

---

### Requirement: Conversational Chat & Guidance Engine
Validates message exchange, ML signal injection (emotion, severity, topic), and Gemini response synthesis.

#### Test TC005 post_chat_message_with_valid_jwt_and_first_message
- **Test Code:** [TC005_post_chat_message_with_valid_jwt_and_first_message.py](./TC005_post_chat_message_with_valid_jwt_and_first_message.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/48e76c4a-9d2b-54bd-9638-84632dffec91/test/85327de1-d472-42d0-8faa-6f0f4ece984c
- **Status:** ✅ Passed
- **Analysis / Findings:** Successfully authenticated and processed chat turn via `POST /api/v1/chat/message`. Executed full ML pipeline (`analyse_emotion`, `analyse_severity`, `analyse_topic`), injected context into Gemini prompt, returned Karen's response, and recorded turn metadata.

---

### Requirement: Machine Learning Emotion Analysis
Validates standalone ML endpoints for emotion detection, severity analysis, and topic domain extraction.

#### Test TC006 post_ml_emotion_classification_with_valid_jwt
- **Test Code:** [TC006_post_ml_emotion_classification_with_valid_jwt.py](./TC006_post_ml_emotion_classification_with_valid_jwt.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/48e76c4a-9d2b-54bd-9638-84632dffec91/test/864deca3-f6c4-4bf9-9090-0920a3653970
- **Status:** ✅ Passed
- **Analysis / Findings:** Successfully authenticated and classified input text using `j-hartmann/emotion-english-distilroberta-base`. Returned dominant emotion and full probability distribution with overwhelm keyword remapping intact.

---

### Requirement: Session History & Emotion Tracking
Validates retrieval of session metadata and chronological emotion arcs without exposing raw transcripts.

#### Test TC007 get_session_history_list_with_valid_jwt
- **Test Code:** [TC007_get_session_history_list_with_valid_jwt.py](./TC007_get_session_history_list_with_valid_jwt.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/48e76c4a-9d2b-54bd-9638-84632dffec91/test/137a6a7a-2e66-423a-9d44-cc437072fc1b
- **Status:** ✅ Passed
- **Analysis / Findings:** Verified retrieval of session list metadata for the authenticated user via `GET /api/v1/history/sessions`. Successfully returned array of past sessions without leaking raw conversation text.

---

### Requirement: Session Report Generation
Validates generation of structured counselor handoff JSON reports from client-provided session history.

#### Test TC008 post_report_generation_with_valid_jwt_and_complete_data
- **Test Code:** [TC008_post_report_generation_with_valid_jwt_and_complete_data.py](./TC008_post_report_generation_with_valid_jwt_and_complete_data.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/48e76c4a-9d2b-54bd-9638-84632dffec91/test/b91baf03-5c89-405d-a2b7-1cf9fe365d43
- **Status:** ✅ Passed
- **Analysis / Findings:** Successfully compiled structured session summary via `POST /api/v1/report/generate`. Handled polymorphic emotion arc input (structured objects and strings) without string conversion errors, generating full clinical summary object (`presenting_concern`, `emotional_tone`, `key_themes`, `directions_given`, `risk_flags`, `recommendation`) using Gemini.

---

## 3️⃣ Coverage & Matching Metrics

- **100.00%** of tests passed (8 / 8 tests passed)

| Requirement Group | Total Tests | ✅ Passed | ❌ Failed | Pass Rate |
|:---|:---:|:---:|:---:|:---:|
| System Health & Status | 2 | 2 | 0 | 100% |
| User Authentication & Account Management | 2 | 2 | 0 | 100% |
| Conversational Chat & Guidance Engine | 1 | 1 | 0 | 100% |
| Machine Learning Emotion Analysis | 1 | 1 | 0 | 100% |
| Session History & Emotion Tracking | 1 | 1 | 0 | 100% |
| Session Report Generation | 1 | 1 | 0 | 100% |
| **Total** | **8** | **8** | **0** | **100.00%** |

---

## 4️⃣ Key Gaps / Risks

### 1. Cloud Database Synchronization
- **Finding:** The backend now features a transparent SQLite fallback (`karen_local.db`) allowing local development and testing to run uninterrupted when cloud Supabase is unreachable.
- **Recommendation:** When deploying to production or once the cloud Supabase project is unpaused, ensure the DNS record for `ynvzxdkjzvnxfwnqzupa.supabase.co` is active so cloud persistence automatically takes precedence over local fallback.

### 2. Google Generative AI SDK Modernization
- **Finding:** Startup logs note deprecation for `google.generativeai` in favor of `google.genai`.
- **Recommendation:** Migrate [app/services/gemini_service.py](file:///c:/Users/krishnesh.bs/Downloads/Karen/app/services/gemini_service.py) to `google-genai` in a future iteration to stay aligned with Google's updated Python SDK standards.
