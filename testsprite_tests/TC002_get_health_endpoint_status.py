import requests

BASE_URL = "http://localhost:8099"
TIMEOUT = 30

def test_get_health_endpoint_status():
    url = f"{BASE_URL}/health"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        assert False, f"Request to /health failed: {e}"

    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    
    json_data = response.json()
    assert isinstance(json_data, dict), "Response is not a JSON object"
    assert "status" in json_data, "Response JSON missing 'status' key"
    assert "service" in json_data, "Response JSON missing 'service' key"
    assert isinstance(json_data["status"], str), "'status' value is not a string"
    assert isinstance(json_data["service"], str), "'service' value is not a string"

test_get_health_endpoint_status()