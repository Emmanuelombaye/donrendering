import utils.transport
import utils.session
import os
import logging
from dotenv import load_dotenv

# Load environment variables relative to this file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("visoid-backend")
logger.info(f"Visoid Backend starting... (loading .env from {env_path})")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.config import OUTPUT_DIR, COST_PER_RENDER_KES
from routers.render_router import router as render_router

app = FastAPI(title="Donfilm Creations API")

# Mount outputs as static files
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prefix all routes with /api to match Vercel and frontend expectations
app.include_router(render_router, prefix="/api")

@app.get("/api")
@app.get("/api/")
def root():
    replicate_token = os.getenv("REPLICATE_API_TOKEN", "")
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
    # Load usage state
    from routers.render_router import get_usage_state
    usage = get_usage_state()
    
    return {
        "status": "online",
        "service_name": "Donfilm Creations API",
        "providers": {
            "huggingface": {
                "configured": bool(hf_token),
                "status": "active" if hf_token else "missing"
            },
            "replicate": {
                "configured": bool(replicate_token),
                "status": "active" if replicate_token else "missing",
                "token_display": f"{replicate_token[:6]}...{replicate_token[-4:]}" if replicate_token else "NONE",
                "full_token": replicate_token,
                "current_budget_kes": usage["budget_kes"],
                "cost_per_render_kes": COST_PER_RENDER_KES
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
