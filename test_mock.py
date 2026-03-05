import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.ai_service import generate_render

try:
    print("Testing mock render...")
    results = generate_render({}, "test.png")
    print(f"Success! Mock results: {results}")
except Exception as e:
    print(f"Failed! Error: {e}")
    import traceback
    traceback.print_exc()
