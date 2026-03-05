
import os

# Get the base directory of the backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# On Vercel, use /tmp for everything writable
if os.getenv("VERCEL"):
    UPLOAD_DIR = "/tmp/uploads"
    OUTPUT_DIR = "/tmp/outputs"
else:
    # Load from environment or use defaults relative to BASE_DIR
    UPLOAD_DIR = os.path.join(BASE_DIR, os.getenv("UPLOAD_DIR", "uploads"))
    OUTPUT_DIR = os.path.join(BASE_DIR, os.getenv("OUTPUT_DIR", "outputs"))

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)