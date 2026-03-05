from dotenv import load_dotenv
import os
import logging

# Load environment variables FIRST before other imports
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("visoid-backend")
logger.info("Visoid Backend starting...")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from core.config import OUTPUT_DIR
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

app.include_router(render_router)

@app.get("/")
def root():
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    
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
                "status": "active" if replicate_token else "missing"
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
