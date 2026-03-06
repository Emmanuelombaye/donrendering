import requests
import os
import json

def get_model_schema():
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("REPLICATE_API_TOKEN not set")
        return

    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/json"
    }
    
    # Get model info
    url = "https://api.replicate.com/v1/models/bytedance/seedream-4"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error getting model: {resp.text}")
        return
    
    model_data = resp.json()
    latest_version_id = model_data.get("latest_version", {}).get("id")
    if not latest_version_id:
        print("No latest version found")
        return
    
    # Get version info
    url = f"https://api.replicate.com/v1/models/bytedance/seedream-4/versions/{latest_version_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Error getting version: {resp.text}")
        return
    
    version_data = resp.json()
    print(json.dumps(version_data.get("openapi_schema", {}).get("components", {}).get("schemas", {}).get("Input", {}).get("properties", {}), indent=2))

if __name__ == "__main__":
    get_model_schema()
