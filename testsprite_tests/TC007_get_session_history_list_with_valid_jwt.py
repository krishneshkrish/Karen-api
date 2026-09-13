import requests

BASE_URL = "http://localhost:8099"
AUTH_CREDENTIALS = {"email": "test@example.com", "password": "1234"}
TIMEOUT = 30


def get_jwt_token():
    login_url = f"{BASE_URL}/api/v1/auth/login"
    payload = {"email": AUTH_CREDENTIALS["email"], "password": AUTH_CREDENTIALS["password"]}
    resp = requests.post(login_url, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    assert "access_token" in data and "token_type" in data
    return f'{data["token_type"].capitalize()} {data["access_token"]}'


def test_get_session_history_list_with_valid_jwt():
    token = get_jwt_token()
    headers = {"Authorization": token}

    url = f"{BASE_URL}/api/v1/history/sessions"
    response = requests.get(url, headers=headers, timeout=TIMEOUT)

    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be an array of session metadata."


test_get_session_history_list_with_valid_jwt()