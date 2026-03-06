import replicate
import requests
import os
import logging
from PIL import Image
from io import BytesIO

logger = logging.getLogger("visoid-backend")

def generate_render(file_paths, base_output_path, style="Modern Villa", strength=0.65, resolution="2k", prompt=None):
    """
    Generate architectural renders the 'Visoid Way'.
    Utilizes all 6 provided images (4 elevations, 1 reference, 1 background)
    to produce 4 consistent variations using Replicate.
    """
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        error_msg = "Make payment: your Replicate API token is invalid or expired. Please check your account."
        logger.error(error_msg)
        raise ValueError(error_msg)

    # 1. Prepare inputs from all 6 files
    front_img = file_paths.get("front")
    back_img = file_paths.get("back")
    left_img = file_paths.get("left")
    right_img = file_paths.get("right")
    ref_img = file_paths.get("reference")
    bg_img = file_paths.get("background")

    # We use 'front' as the structural anchor
    anchor_img = front_img or back_img or left_img or right_img
    if not anchor_img:
        raise ValueError("No elevation images (front/back/left/right) provided. At least one is required.")

    # 2. Build a STRICT 'Visoid' prompt referring to image indices
    # Image 1 = Structure anchor
    # Image 2 = Reference (if provided)
    # Image 3 = Background (if provided)
    
    # Start with structure anchor
    visoid_prompt = "STRICT INSTRUCTION: Generate a photorealistic architectural render. "
    visoid_prompt += "STRUCTURE: Follow the exact architecture and lines shown in Image 1. "
    
    base_images = [anchor_img]
    
    if ref_img:
        base_images.append(ref_img)
        # Force strict material and style adherence
        visoid_prompt += "STYLE & MATERIALS: You MUST copy the exact materials, textures, color palette, lighting, and architectural aesthetic from Image 2. No variations allowed. "
    else:
        visoid_prompt += f"STYLE: Follow a {style} architectural style. "

    if bg_img:
        base_images.append(bg_img)
        bg_idx = len(base_images)
        # Force strict environment adherence
        visoid_prompt += f"ENVIRONMENT: Place the building exactly into the environment and lighting context shown in Image {bg_idx}. Use it as a literal background. "

    visoid_prompt += "QUALITY: 8k resolution, cinematic masterpiece, sharp architectural focus, highly detailed textures."

    # Overwrite with user prompt if provided but keep the strict prefixes
    if prompt:
        visoid_prompt = f"{visoid_prompt} User specific details: {prompt}"

    try:
        # Using bytedance/seedream-4 as requested by the user
        model_id = "bytedance/seedream-4"
        logger.info(f"VISOID RENDER: Using {len(base_images)} images for style: {style} (Seedream-4)")

        opened_files = []
        try:
            # Open all required image files
            file_handles = [open(path, "rb") for path in base_images]
            opened_files = file_handles

            # Map resolution to Seedream-4 size schema
            size_map = {"1k": "1K", "2k": "2K", "4k": "4K"}
            target_size = size_map.get(resolution.lower(), "2K")

            # Replicate request for Seedream-4 based on official multi-image schema
            render_input = {
                "prompt": visoid_prompt,
                "image_input": file_handles,    # 3 core inputs: Structure, Style, Background
                "size": target_size,
                "image_strength": strength,    # Fidelity to elevation (Image 1)
                "sequential_image_generation": "disabled",
                "max_images": 1,
                "enhance_prompt": True,
                "aspect_ratio": "match_input_image"
            }
            
            output = replicate.run(model_id, input=render_input)
        finally:
            for f in opened_files:
                f.close()
        
        if not output:
            raise ValueError("Replicate API returned no results.")

        if isinstance(output, str):
            output = [output]

        # For Vercel deployment, we return the Replicate URLs directly
        # because Vercel filesystem is read-only/ephemeral.
        # This ensures the images are accessible to the frontend.
        return output

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Visoid Service error: {error_msg}")
        if "401" in error_msg or "unauthorized" in error_msg.lower() or "token" in error_msg.lower():
            raise ValueError("Make payment: your Replicate API token is invalid or expired. Please check your account.")
        raise ValueError(f"AI System Error: {error_msg}")
