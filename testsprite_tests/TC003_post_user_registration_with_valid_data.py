import requests

BASE_URL = "http://localhost:8099"
REGISTER_ENDPOINT = "/api/v1/auth/register"
TIMEOUT = 30

def test_post_user_registration_with_valid_data():
    url = BASE_URL + REGISTER_ENDPOINT
    payload = {
        "email": "testnew@example.com",
        "password": "ValidPass123!"
    }
    headers = {
        "Content-Type": "application/json"
    }

    # Attempt to register user with a unique email to avoid conflict
    response = None
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        # Expected status code 201
        assert response.status_code == 201, f"Expected status code 201, got {response.status_code}"

        json_response = response.json()
        # Validate presence of required fields
        assert "access_token" in json_response and isinstance(json_response["access_token"], str) and json_response["access_token"]
        assert "token_type" in json_response and isinstance(json_response["token_type"], str) and json_response["token_type"]
        assert "user_hash" in json_response and isinstance(json_response["user_hash"], str) and json_response["user_hash"]
    finally:
        # Clean up: Try to delete the user if the API supported it
        # Since no delete endpoint is provided, no cleanup code is possible
        # This is a placeholder for cleanup logic if available in future
        pass

test_post_user_registration_with_valid_data()