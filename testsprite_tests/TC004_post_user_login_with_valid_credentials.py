import requests

BASE_URL = "http://localhost:8099"
LOGIN_ENDPOINT = "/api/v1/auth/login"
TIMEOUT = 30

def test_post_user_login_with_valid_credentials():
    url = BASE_URL + LOGIN_ENDPOINT
    payload = {
        "email": "test@example.com",
        "password": "1234"
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"HTTP request failed: {e}"
    
    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
    
    json_response = None
    try:
        json_response = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"
    
    assert "access_token" in json_response, "Response missing 'access_token'"
    assert isinstance(json_response["access_token"], str) and json_response["access_token"], "'access_token' should be a non-empty string"

    assert "token_type" in json_response, "Response missing 'token_type'"
    assert isinstance(json_response["token_type"], str) and json_response["token_type"], "'token_type' should be a non-empty string"
    
    assert "user_hash" in json_response, "Response missing 'user_hash'"
    assert isinstance(json_response["user_hash"], str) and json_response["user_hash"], "'user_hash' should be a non-empty string"

test_post_user_login_with_valid_credentials()