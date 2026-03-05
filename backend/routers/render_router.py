from fastapi import APIRouter, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, JSONResponse
import shutil, os, logging
from services.ai_service import generate_render
from core.config import UPLOAD_DIR, OUTPUT_DIR

router = APIRouter()
logger = logging.getLogger("visoid-backend")

RENDER_PRESETS = [
    {"name": "Modern Villa", "prompt": "modern luxury villa, ultra realistic architectural render, 8k ultra detailed, professional architectural visualization"},
    {"name": "Classic Mansion", "prompt": "classic mansion, ornate, photorealistic, golden hour lighting, 4k"},
    {"name": "Futuristic", "prompt": "futuristic building, sci-fi, glass and steel, neon lights, 4k"},
    {"name": "Minimalist", "prompt": "minimalist house, clean lines, white, natural light, 4k"}
]

@router.post("/render")
async def render(
    front: UploadFile = File(...),
    back: UploadFile = File(...),
    left: UploadFile = File(...),
    right: UploadFile = File(...),
    reference: UploadFile = File(None),
    background: UploadFile = File(None),
    style: str = Form("Modern Villa"),
    strength: float = Form(0.65),
    resolution: str = Form("4k")
):
    logger.info(f"Received render request: style={style}, strength={strength}, resolution={resolution}")
    # Save all uploaded files
    file_paths = {}
    for file_key, upload_file in [
        ("front", front), ("back", back), ("left", left),
        ("right", right), ("reference", reference), ("background", background)
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
        # Run the synchronous generate_render in a threadpool to avoid blocking the event loop
        from fastapi.concurrency import run_in_threadpool
        output_paths = await run_in_threadpool(
            generate_render, 
            file_paths, 
            output_path, 
            style=style, 
            strength=strength, 
            resolution=resolution, 
            prompt=prompt
        )
        
        # Check if output_paths are already full URLs (from Replicate) or local filenames
        output_results = []
        for p in output_paths:
            if p.startswith("http"):
                output_results.append(p)
            else:
                output_results.append(os.path.basename(p))

    except Exception as e:
        logger.error(f"Render failed: {e}")
        # Ensure we return a 400 or 500 with the error message so the frontend can show it
        return JSONResponse(status_code=400, content={"error": str(e)})

    logger.info(f"Render complete: {output_results}")
    return JSONResponse(content={"results": output_results})


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