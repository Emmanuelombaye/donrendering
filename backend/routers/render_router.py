from fastapi import APIRouter, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, JSONResponse
import shutil, os, logging
from services.ai_service import generate_render
from core.config import UPLOAD_DIR, OUTPUT_DIR, COST_PER_RENDER_KES

router = APIRouter()
logger = logging.getLogger("visoid-backend")

RENDER_PRESETS = [
    {"name": "Modern Villa", "prompt": "modern luxury villa, ultra realistic architectural render, 8k ultra detailed, professional architectural visualization"},
    {"name": "Classic Mansion", "prompt": "classic mansion, ornate, photorealistic, golden hour lighting, 4k"},
    {"name": "Futuristic", "prompt": "futuristic building, sci-fi, glass and steel, neon lights, 4k"},
    {"name": "Minimalist", "prompt": "minimalist house, clean lines, white, natural light, 4k"}
]

import json

STATE_FILE = os.path.join(os.path.dirname(UPLOAD_DIR), "usage_state.json")

def get_usage_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"budget_kes": 5000} # Default starting budget or loaded from elsewhere

def update_usage_state(amount):
    state = get_usage_state()
    state["budget_kes"] -= amount
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    return state

@router.post("/render")
async def render(
    elevation: UploadFile = File(...),
    reference: UploadFile = File(None),
    background: UploadFile = File(None),
    style: str = Form("Modern Villa"),
    strength: float = Form(0.65),
    resolution: str = Form("2k")
):
    # Force 2K ONLY as requested
    effective_resolution = "2k"
    
    logger.info(f"Received 3-input render request: style={style}")
    
    usage = get_usage_state()
    if usage["budget_kes"] < COST_PER_RENDER_KES:
        return JSONResponse(status_code=402, content={"error": f"Insufficient KES budget for render (Needs {COST_PER_RENDER_KES} KES)"})

    # Save exactly 3 uploaded files
    file_paths = {}
    for file_key, upload_file in [
        ("front", elevation), ("reference", reference), ("background", background)
    ]:
        if upload_file and upload_file.filename:
            file_path = os.path.join(UPLOAD_DIR, f"{file_key}_{upload_file.filename}")
            with open(file_path, "wb") as f:
                shutil.copyfileobj(upload_file.file, f)
            file_paths[file_key] = file_path

    output_name = f"rendered_{os.urandom(4).hex()}.png"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    # Find prompt from presets
    prompt = next((p["prompt"] for p in RENDER_PRESETS if p["name"] == style), None)

    try:
        from fastapi.concurrency import run_in_threadpool
        # Pass effective_resolution ("2k") to ensure strict compliance
        output_paths = await run_in_threadpool(
            generate_render, 
            file_paths, 
            output_path, 
            style=style, 
            strength=strength, 
            resolution=effective_resolution, 
            prompt=prompt
        )
        
        # Deduct per render
        new_usage = update_usage_state(COST_PER_RENDER_KES)
        
        output_results = []
        for p in output_paths:
            p_str = str(p)  # Handle Replicate FileOutput objects
            if p_str.startswith("http"):
                output_results.append(p_str)
            else:
                output_results.append(os.path.basename(p_str))

    except Exception as e:
        logger.error(f"Render failed: {e}")
        return JSONResponse(status_code=400, content={"error": str(e)})

    logger.info(f"Render complete: {output_results}. Remaining budget: {new_usage['budget_kes']} KES")
    return JSONResponse(content={
        "results": output_results,
        "budget_kes": new_usage["budget_kes"]
    })


@router.get("/presets")
async def get_presets():
    return RENDER_PRESETS

from fastapi import Path

@router.get("/download/{image_name}")
async def download_image(image_name: str = Path(..., description="Name of the image file to download")):
    file_path = os.path.join(OUTPUT_DIR, image_name)
    if not os.path.exists(file_path):
        logger.warning(f"Download failed: {image_name} not found")
        return JSONResponse(status_code=404, content={"error": "Image not found"})
    logger.info(f"Image downloaded: {image_name}")
    return FileResponse(file_path, filename=image_name)