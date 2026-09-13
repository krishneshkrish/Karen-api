import requests

BASE_URL = "http://localhost:8099"

def test_get_root_api_running_status():
    url = f"{BASE_URL}/"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
    json_data = None
    try:
        json_data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert "message" in json_data, "Response JSON does not contain 'message' key"
    assert isinstance(json_data["message"], str), "'message' should be a string"
    assert len(json_data["message"].strip()) > 0, "'message' should not be empty"

test_get_root_api_running_status()