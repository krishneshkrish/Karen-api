import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://localhost:8099"
AUTH_CREDENTIALS = {"username": "test", "password": "1234"}

def test_post_report_generation_with_valid_jwt_and_complete_data():
    timeout = 30

    login_url = f"{BASE_URL}/api/v1/auth/login"
    report_url = f"{BASE_URL}/api/v1/report/generate"
    chat_message_url = f"{BASE_URL}/api/v1/chat/message"
    end_session_url = f"{BASE_URL}/api/v1/chat/end-session"

    # Step 1: Login and get JWT token
    try:
        login_resp = requests.post(
            login_url,
            json={"email": "test@example.com", "password": "1234"},
            auth=HTTPBasicAuth(AUTH_CREDENTIALS["username"], AUTH_CREDENTIALS["password"]),
            timeout=timeout,
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        login_data = login_resp.json()
        token = login_data.get("access_token")
        assert token is not None, "No access_token in login response"
        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: Create a new chat session by sending first message to get session_id
        first_message_payload = {
            "session_id": "",
            "messages": [
                {"role": "user", "content": "I am feeling very anxious today."}
            ],
            "is_first_message": True
        }
        chat_resp = requests.post(
            chat_message_url,
            json=first_message_payload,
            headers=headers,
            timeout=timeout,
        )
        assert chat_resp.status_code == 200, f"Chat message failed: {chat_resp.text}"
        chat_data = chat_resp.json()
        session_id = chat_data.get("session_id")
        assert session_id is not None and session_id != "", "No session_id returned from chat message"

        # Step 3: Prepare report generation payload with complete session data
        report_payload = {
            "session_id": session_id,
            "messages": [
                {"role": "user", "content": "I am feeling very anxious today."},
                {"role": "karen", "content": "I hear that you feel anxious. Can you tell me more?"},
                {"role": "user", "content": "I have a big presentation tomorrow and I'm really nervous."},
            ],
            "topic": "Anxiety about presentation",
            "emotion_arc": [
                {"timestamp": 1690000000, "emotion": "anxiety"},
                {"timestamp": 1690000600, "emotion": "concern"},
                {"timestamp": 1690001200, "emotion": "nervousness"},
            ],
            "final_severity": "moderate"
        }

        # Step 4: POST to report generate endpoint
        report_resp = requests.post(
            report_url,
            json=report_payload,
            headers=headers,
            timeout=timeout,
        )
        assert report_resp.status_code == 200, f"Report generation failed: {report_resp.text}"
        report_data = report_resp.json()

        # Validate the response contains session_id and report object
        assert "session_id" in report_data, "Response missing session_id"
        assert report_data["session_id"] == session_id, "Mismatched session_id in report"
        assert "report" in report_data, "Response missing report object"
        assert isinstance(report_data["report"], dict), "Report object is not a dictionary"

    finally:
        # Cleanup: End the chat session to avoid resource leak
        if 'session_id' in locals() and session_id:
            try:
                end_resp = requests.post(
                    end_session_url,
                    params={
                        "session_id": session_id,
                        "topic": "Anxiety about presentation",
                        "final_severity": "moderate"
                    },
                    headers=headers,
                    timeout=timeout,
                )
                # Accept 200 or ignore errors in cleanup phase
                if end_resp.status_code != 200:
                    print(f"Warning: Failed to end session {session_id}: {end_resp.text}")
            except Exception as e:
                print(f"Warning: Exception during session cleanup: {e}")

test_post_report_generation_with_valid_jwt_and_complete_data()
