import os
import sys
from dotenv import load_dotenv

# Check current directory
print(f"Current Directory: {os.getcwd()}")

# Load env from backend folder
env_path = os.path.join(os.getcwd(), 'backend', '.env')
print(f"Checking for .env at: {env_path}")
if os.path.exists(env_path):
    print(".env file FOUND")
    load_dotenv(env_path)
else:
    print(".env file NOT FOUND in backend/")

# Check for .env in root
root_env = os.path.join(os.getcwd(), '.env')
if os.path.exists(root_env):
    print(".env file FOUND in root")
    load_dotenv(root_env)

token = os.getenv("REPLICATE_API_TOKEN")
if token:
    print(f"REPLICATE_API_TOKEN is SET (starts with: {token[:5]}...)")
else:
    print("REPLICATE_API_TOKEN is NOT SET")

try:
    import replicate
    print("replicate library is installed")
except ImportError:
    print("replicate library NOT installed")

try:
    from PIL import Image
    print("Pillow (PIL) is installed")
except ImportError:
    print("Pillow NOT installed")
