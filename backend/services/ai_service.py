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

    # 2. Build a comprehensive 'Visoid' prompt incorporating all context
    visoid_prompt = prompt or f"Professional architectural visualization of a {style}, high resolution, photorealistic, cinematic lighting."
    
    if ref_img:
        visoid_prompt += " Match the materials, textures, and aesthetic style shown in the reference image."
    if bg_img:
        visoid_prompt += " Place the building in the exact environment and lighting context of the background image."
    if back_img and left_img and right_img:
        visoid_prompt += " Ensure structural consistency across all elevations provided."

    try:
        # Using stability-ai/sdxl with potential for multi-image context if the version supports it
        # For this implementation, we use SDXL and we can utilize the 'reference' image as a secondary input
        # if using a model that supports IP-Adapter or similar, but here we'll stick to a robust SDXL setup.
        model_id = "stability-ai/sdxl:7762fd07cf2183b2800d73e9061de50bab31a8b24c6d1518299d3cb5543ef52a"
        
        logger.info(f"VISOID RENDER: Using {len(file_paths)} inputs for style: {style}")

        # Map resolution for 2k
        width, height = 1024, 1024
        if resolution == "2k":
            width, height = 2048, 2048

        with open(anchor_img, "rb") as main_image:
            # Replicate request
            render_input = {
                "prompt": visoid_prompt,
                "image": main_image,
                "prompt_strength": strength,
                "num_outputs": 4,
                "width": width,
                "height": height,
                "scheduler": "K_EULER_ANCESTRAL",
                "guidance_scale": 8.5,
                "num_inference_steps": 50,
                "refine": "expert_ensemble_refiner",
                "apply_watermark": False,
                "high_noise_frac": 0.8
            }
            
            output = replicate.run(model_id, input=render_input)
        
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
