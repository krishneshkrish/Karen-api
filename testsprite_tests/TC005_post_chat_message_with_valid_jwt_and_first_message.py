import requests

BASE_URL = "http://localhost:8099"
AUTH_CREDENTIALS = {"email": "test@example.com", "password": "1234"}
TIMEOUT = 30


def post_chat_message_with_valid_jwt_and_first_message():
    # Step 1: Authenticate to get JWT token
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_payload = {
        "email": AUTH_CREDENTIALS["email"],
        "password": AUTH_CREDENTIALS["password"],
    }

    login_resp = requests.post(login_url, json=login_payload, timeout=TIMEOUT)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    login_data = login_resp.json()
    access_token = login_data.get("access_token")
    assert access_token, "No access_token received after login"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    chat_url = f"{BASE_URL}/api/v1/chat/message"

    payload = {
        "session_id": "",
        "messages": [
            {
                "role": "user",
                "content": "Hello, I need some support.",
            }
        ],
        "is_first_message": True,
    }

    session_id = None
    try:
        resp = requests.post(chat_url, headers=headers, json=payload, timeout=TIMEOUT)
        assert resp.status_code == 200, f"Chat message failed: {resp.text}"
        resp_data = resp.json()

        assert isinstance(resp_data, dict), "Response is not a JSON object"
        assert "response" in resp_data and isinstance(resp_data["response"], str) and resp_data["response"], "Missing or invalid 'response' text"
        assert "ml_signals" in resp_data and isinstance(resp_data["ml_signals"], dict), "Missing or invalid 'ml_signals' object"
        assert "escalate" in resp_data and isinstance(resp_data["escalate"], bool), "Missing or invalid 'escalate' flag"
        assert "crisis" in resp_data and isinstance(resp_data["crisis"], bool), "Missing or invalid 'crisis' flag"
        assert "session_id" in resp_data and isinstance(resp_data["session_id"], str) and resp_data["session_id"], "Missing or invalid 'session_id'"

        session_id = resp_data["session_id"]

    finally:
        if session_id:
            end_session_url = f"{BASE_URL}/api/v1/chat/end-session"
            params = {
                "session_id": session_id,
                "topic": "test_cleanup",
                "final_severity": "low",
            }
            try:
                end_resp = requests.post(end_session_url, headers=headers, params=params, timeout=TIMEOUT)
                if end_resp.status_code != 200:
                    print(f"Warning: Failed to end session {session_id}: {end_resp.status_code} {end_resp.text}")
            except Exception as e:
                print(f"Warning: Exception when ending session {session_id}: {e}")


post_chat_message_with_valid_jwt_and_first_message()
