import requests

BASE_URL = "http://localhost:8099"
AUTH_CREDENTIALS = {"username": "test", "password": "1234"}
LOGIN_EMAIL = "test@example.com"
LOGIN_PASSWORD = "1234"  # Assuming same password as username password value; adjust if needed
TIMEOUT = 30

def test_post_ml_emotion_classification_with_valid_jwt():
    # Step 1: Authenticate user to get valid JWT
    login_url = f"{BASE_URL}/api/v1/auth/login"
    login_payload = {
        "email": LOGIN_EMAIL,
        "password": LOGIN_PASSWORD
    }
    login_response = requests.post(login_url, json=login_payload, timeout=TIMEOUT)
    assert login_response.status_code == 200, f"Failed to login: {login_response.text}"
    login_data = login_response.json()
    assert "access_token" in login_data, "access_token not found in login response"
    jwt_token = login_data["access_token"]

    # Step 2: Call emotion classification endpoint with valid JWT
    emotion_url = f"{BASE_URL}/api/v1/ml/emotion"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    emotion_payload = {
        "text": "I am feeling very happy and excited today!"
    }
    emotion_response = requests.post(emotion_url, json=emotion_payload, headers=headers, timeout=TIMEOUT)

    # Step 3: Validate the response
    assert emotion_response.status_code == 200, f"Emotion classification failed: {emotion_response.text}"
    emotion_data = emotion_response.json()
    assert "dominant_emotion" in emotion_data, "dominant_emotion not found in response"
    assert isinstance(emotion_data["dominant_emotion"], str) and emotion_data["dominant_emotion"], "Invalid dominant_emotion value"
    assert "scores" in emotion_data, "scores not found in response"
    assert isinstance(emotion_data["scores"], dict) and len(emotion_data["scores"]) > 0, "Invalid scores value"

test_post_ml_emotion_classification_with_valid_jwt()