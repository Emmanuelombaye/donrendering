import replicate
import os
import json

def inspect_model():
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("REPLICATE_API_TOKEN not set")
        return

    try:
        model = replicate.models.get("bytedance/seedream-4")
        latest_version = model.latest_version
        print(f"Model: {model.owner}/{model.name}")
        print(f"Latest Version: {latest_version.id}")
        print("Schema:")
        print(json.dumps(latest_version.openapi_schema, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_model()
