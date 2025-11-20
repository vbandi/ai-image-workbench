"""Image Generation API module for handling various AI image generation models."""

import base64
import io
import logging
from typing import Dict, Any

import requests
from PIL import Image

import fal_client


LOGGER = logging.getLogger("image_generator.api")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)

# Available models
MODELS = [
    "fal-ai/flux/schnell",
    "fal-ai/flux-1/srpo",
    "fal-ai/flux-pro/v1.1",
    "fal-ai/flux-pro/v1.1-ultra",
    "fal-ai/imagen4/preview",
    "fal-ai/imagen4/preview/fast",
    "fal-ai/imagen4/preview/ultra",
    "fal-ai/hidream-i1-fast",
    "fal-ai/hidream-i1-dev",
    "fal-ai/hidream-i1-full",
    "fal-ai/stable-diffusion-v35-large",
    "fal-ai/stable-diffusion-v35-medium",
    "fal-ai/luma-photon",
    "fal-ai/ideogram/v2",
    "fal-ai/recraft-20b",
    "fal-ai/sana",
    "fal-ai/bytedance/seedream/v3/text-to-image",
    "fal-ai/bytedance/seedream/v4/text-to-image",
    "fal-ai/wan/v2.2-5b/text-to-image",
    "fal-ai/gemini-25-flash-image",
    "fal-ai/gemini-3-pro-image-preview",
    "fal-ai/nano-banana",
    "fal-ai/qwen-image",
    "bria/fibo/generate",
]


def _parse_ideogram_response(result: Dict[str, Any]) -> bytes:
    """Parse Ideogram v2 response format."""
    decoded_image = None
    # Format 1: Direct array of image URLs or data URIs
    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        encoded_image = result["images"][0]
        if isinstance(encoded_image, str):
            if encoded_image.startswith("data:"):
                # Handle data URI
                decoded_image = base64.b64decode(encoded_image.split(",")[1])
            else:
                # Handle URL
                response = requests.get(encoded_image)
                decoded_image = response.content
    # Format 2: Object with image property
    elif "image" in result:
        encoded_image = result["image"]
        if isinstance(encoded_image, str):
            if encoded_image.startswith("data:"):
                # Handle data URI
                decoded_image = base64.b64decode(encoded_image.split(",")[1])
            else:
                # Handle URL
                response = requests.get(encoded_image)
                decoded_image = response.content
    # Format 3: Nested structure
    elif "result" in result and "images" in result["result"]:
        encoded_image = result["result"]["images"][0]
        if isinstance(encoded_image, str):
            if encoded_image.startswith("data:"):
                # Handle data URI
                decoded_image = base64.b64decode(encoded_image.split(",")[1])
            else:
                # Handle URL
                response = requests.get(encoded_image)
                decoded_image = response.content
    if decoded_image is None:
        raise ValueError(f"Could not extract image from Ideogram v2 response: {result}")
    return decoded_image


def _parse_imagen4_response(result: Dict[str, Any], model_name: str) -> bytes:
    """Parse Imagen 4 response format (all variants)."""
    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        image_obj = result["images"][0]
        # Extract URL from the File object
        if isinstance(image_obj, dict) and "url" in image_obj:
            image_url = image_obj["url"]
            # Download the image from URL
            response = requests.get(image_url)
            return response.content
        else:
            raise ValueError(f"Unexpected {model_name} image format: {image_obj}")
    else:
        raise ValueError(f"Could not extract image from {model_name} response: {result}")


def _parse_gemini_flash_image_response(result: Dict[str, Any]) -> bytes:
    """Parse Gemini 2.5 Flash Image response format."""
    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        image_obj = result["images"][0]
        if isinstance(image_obj, dict) and "url" in image_obj:
            image_url = image_obj["url"]
            response = requests.get(image_url)
            return response.content
        else:
            raise ValueError(f"Unexpected Gemini 2.5 Flash Image format: {image_obj}")
    else:
        raise ValueError(f"Could not extract image from Gemini 2.5 Flash Image response: {result}")


def _parse_flux_pro_response(result: Dict[str, Any]) -> bytes:
    """Parse FLUX.1 PRO response format."""
    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        image_obj = result["images"][0]
        if isinstance(image_obj, dict) and "url" in image_obj:
            image_url = image_obj["url"]
            # Handle data URI
            if image_url.startswith("data:image/jpeg;base64,"):
                return base64.b64decode(image_url.split(",")[1])
            # Handle regular URL
            response = requests.get(image_url)
            return response.content
        else:
            raise ValueError(f"Unexpected FLUX.1 PRO image format: {image_obj}")
    else:
        raise ValueError(f"Could not extract image from FLUX.1 PRO response: {result}")


def _parse_seedream_response(result: Dict[str, Any]) -> bytes:
    """Parse SeeDream v3 response format."""
    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        image_obj = result["images"][0]
        if isinstance(image_obj, dict) and "url" in image_obj:
            image_url = image_obj["url"]
            response = requests.get(image_url)
            return response.content
        else:
            raise ValueError(f"Unexpected SeeDream v3 image format: {image_obj}")
    else:
        raise ValueError(f"Could not extract image from SeeDream v3 response: {result}")


def _parse_seedream_v4_response(result: Dict[str, Any]) -> bytes:
    """Parse SeeDream v4 response format."""
    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        image_obj = result["images"][0]
        if isinstance(image_obj, dict) and "url" in image_obj:
            image_url = image_obj["url"]
            response = requests.get(image_url)
            return response.content
        else:
            raise ValueError(f"Unexpected SeeDream v4 image format: {image_obj}")
    else:
        raise ValueError(f"Could not extract image from SeeDream v4 response: {result}")


def _parse_wan_response(result: Dict[str, Any]) -> bytes:
    """Parse WAN v2.2-5b response format."""
    if "image" in result and isinstance(result["image"], dict) and "url" in result["image"]:
        image_url = result["image"]["url"]
        response = requests.get(image_url)
        return response.content
    else:
        raise ValueError(f"Could not extract image from WAN v2.2-5b response: {result}")


def _parse_nano_banana_response(result: Dict[str, Any]) -> bytes:
    """Parse Nano Banana response format."""
    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        image_obj = result["images"][0]
        if isinstance(image_obj, dict) and "url" in image_obj:
            image_url = image_obj["url"]
            # Handle data URI
            if image_url.startswith("data:image/"):
                return base64.b64decode(image_url.split(",")[1])
            # Handle regular URL
            else:
                response = requests.get(image_url)
                return response.content
        else:
            raise ValueError(f"Unexpected Nano Banana image format: {image_obj}")
    else:
        raise ValueError(f"Could not extract image from Nano Banana response: {result}")


def _parse_qwen_image_response(result: Dict[str, Any]) -> bytes:
    """Parse Qwen Image response format."""
    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        image_obj = result["images"][0]
        if isinstance(image_obj, dict) and "url" in image_obj:
            image_url = image_obj["url"]
            # Handle data URI
            if image_url.startswith("data:image/"):
                return base64.b64decode(image_url.split(",")[1])
            # Handle regular URL
            else:
                response = requests.get(image_url)
                return response.content
        else:
            raise ValueError(f"Unexpected Qwen Image format: {image_obj}")
    else:
        raise ValueError(f"Could not extract image from Qwen Image response: {result}")


def _parse_bria_fibo_response(result: Dict[str, Any]) -> bytes:
    """Parse BRIA FIBO generate response format."""
    # Expected: { "image": { "url": "...", ... } }
    if "image" in result and isinstance(result["image"], dict):
        image_obj = result["image"]
        if "url" in image_obj and isinstance(image_obj["url"], str):
            image_url = image_obj["url"]
            # Download the image from the provided URL
            response = requests.get(image_url)
            response.raise_for_status()
            return response.content
    raise ValueError(f"Could not extract image from BRIA FIBO response: {result}")


def _parse_gemini_3_pro_response(result: Dict[str, Any]) -> bytes:
    """Parse Gemini 3 Pro Image Preview response format."""
    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        image_obj = result["images"][0]
        if isinstance(image_obj, dict) and "url" in image_obj:
            image_url = image_obj["url"]
            if image_url.startswith("data:"):
                # Handle data URI
                return base64.b64decode(image_url.split(",")[1])
            else:
                # Handle regular URL
                response = requests.get(image_url)
                return response.content
        else:
            raise ValueError(f"Unexpected Gemini 3 Pro Image format: {image_obj}")
    else:
        raise ValueError(f"Could not extract image from Gemini 3 Pro Image response: {result}")


def _parse_standard_response(result: Dict[str, Any]) -> bytes:
    """Parse standard response format."""
    image_data = result["images"][0]
    encoded_image = image_data["url"]
    return base64.b64decode(encoded_image.split(",")[1])


def submit_image_generation(model: str, prompt: str):
    """
    Submit an image generation request asynchronously.
    
    Args:
        model: The model to use for generation
        prompt: The text prompt for image generation
        
    Returns:
        Request handle for polling completion
        
    Raises:
        ValueError: If model is not supported
    """
    if model not in MODELS:
        raise ValueError(f"Unsupported model: {model}")
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    LOGGER.debug("Submitting generation request model=%s prompt_len=%d", model, len(prompt))

    # Model-specific submission logic
    if model == "fal-ai/ideogram/v2":
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "enable_safety_checker": "False",
                "safety_tolerance": 5
            }
        )
    elif model in ["fal-ai/imagen4/preview", "fal-ai/imagen4/preview/fast", "fal-ai/imagen4/preview/ultra"]:
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "aspect_ratio": "4:3",
                "enable_safety_checker": "False",
                "safety_tolerance": 5
            }
        )
    elif model == "fal-ai/gemini-25-flash-image":
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "num_images": 1
            }
        )
    elif model == "fal-ai/flux-1/srpo":
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "image_size": "landscape_4_3",
                "enable_safety_checker": "False",
                "guidance_scale": 4.5,
                "num_inference_steps": 28,
                "sync_mode": "true",
            }
        )
    elif model == "fal-ai/bytedance/seedream/v3/text-to-image":
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "enable_safety_checker": "False",
                "safety_tolerance": 5
            }
        )
    elif model == "fal-ai/bytedance/seedream/v4/text-to-image":
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "enable_safety_checker": "False",
                "safety_tolerance": 5
            }
        )
    elif model == "fal-ai/wan/v2.2-5b/text-to-image":
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "num_inference_steps": 40,
                "enable_safety_checker": False,
                "enable_prompt_expansion": False,
                "guidance_scale": 3.5,
                "shift": 2,
                "image_size": "landscape_4_3"
            }
        )
    elif model == "fal-ai/nano-banana":
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "aspect_ratio": "4:3",
                "enable_safety_checker": "False",
                "safety_tolerance": 5
            }
        )
    elif model == "fal-ai/qwen-image":
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "image_size": "landscape_4_3",
                "enable_safety_checker": False,
                "guidance_scale": 2.5,
                "num_inference_steps": 30,
            }
        )
    elif model == "bria/fibo/generate":
        # BRIA FIBO accepts "prompt" and supports aspect ratios like "4:3"
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "aspect_ratio": "4:3",
                # Optional tuning parameters can be passed, using sensible defaults
                # "guidance_scale": 5,
                # "steps_num": 50,
            }
        )
    elif model == "fal-ai/gemini-3-pro-image-preview":
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "aspect_ratio": "4:3",
                "sync_mode": True
            }
        )
    else:
        # Standard handling for other models
        return fal_client.submit(
            model,
            arguments={
                "prompt": prompt,
                "num_images": 1,
                "enable_safety_checker": "False",
                "image_size": "landscape_4_3",
                "sync_mode": "true",
                "safety_tolerance": 5,
            }
        )


def generate_image(model: str, prompt: str) -> Image.Image:
    """
    Generate an image using the specified model and prompt.
    This is a blocking wrapper around the async API for backward compatibility.

    Args:
        model: The model to use for generation
        prompt: The text prompt for image generation

    Returns:
        PIL Image object

    Raises:
        ValueError: If model is not supported or response parsing fails
        Exception: If API call fails
    """
    import time

    start = time.time()
    handle = submit_image_generation(model, prompt)
    LOGGER.debug("Submitted request for model=%s handle=%s", model, type(handle).__name__)

    poll_count = 0
    while True:
        poll_count += 1
        is_complete, result = poll_generation_result(handle, model)
        if is_complete:
            elapsed = time.time() - start
            if isinstance(result, str):
                LOGGER.debug("Generation failed model=%s after %.2fs message=%s", model, elapsed, result)
                raise Exception(result)
            LOGGER.debug("Generation complete model=%s in %.2fs polls=%d", model, elapsed, poll_count)
            return result
        if poll_count % 10 == 0:
            LOGGER.debug("Generation still running model=%s polls=%d elapsed=%.2fs", model, poll_count, time.time() - start)
        time.sleep(0.5)


def poll_generation_result(handle, model: str):
    """
    Poll a generation handle for completion.
    
    Args:
        handle: Request handle from submit_image_generation
        model: The model name to determine parsing logic
        
    Returns:
        tuple: (is_complete, result_or_error)
        - is_complete: True if done, False if still processing
        - result_or_error: PIL Image if successful, error string if failed
    """
    try:
        status = handle.status()
        status_str = str(status)
        status_upper = status_str.upper()
        status_name = getattr(status, 'name', None)
        LOGGER.debug(
            "Polled status model=%s status=%s name=%s", model, status_str, status_name
        )

        # Determine completion by checking status name or prefix
        completed = (
            (status_name is not None and status_name.upper() == 'COMPLETED')
            or status_upper.startswith('COMPLETED')
            or status_upper.startswith('SUCCESS')
            or status_upper.startswith('DONE')
        )

        if completed:
            result = handle.get()
            
            # Parse based on model type
            if model == "fal-ai/ideogram/v2":
                decoded_image = _parse_ideogram_response(result)
            elif model in ["fal-ai/imagen4/preview", "fal-ai/imagen4/preview/fast", "fal-ai/imagen4/preview/ultra"]:
                decoded_image = _parse_imagen4_response(result, model)
            elif model == "fal-ai/gemini-25-flash-image":
                decoded_image = _parse_gemini_flash_image_response(result)
            elif model == "fal-ai/flux-1/srpo":
                decoded_image = _parse_flux_pro_response(result)
            elif model == "fal-ai/bytedance/seedream/v3/text-to-image":
                decoded_image = _parse_seedream_response(result)
            elif model == "fal-ai/bytedance/seedream/v4/text-to-image":
                decoded_image = _parse_seedream_v4_response(result)
            elif model == "fal-ai/wan/v2.2-5b/text-to-image":
                decoded_image = _parse_wan_response(result)
            elif model == "fal-ai/nano-banana":
                decoded_image = _parse_nano_banana_response(result)
            elif model == "fal-ai/qwen-image":
                decoded_image = _parse_qwen_image_response(result)
            elif model == "bria/fibo/generate":
                decoded_image = _parse_bria_fibo_response(result)
            elif model == "fal-ai/gemini-3-pro-image-preview":
                decoded_image = _parse_gemini_3_pro_response(result)
            else:
                # Standard handling for other models
                decoded_image = _parse_standard_response(result)
            
            return True, Image.open(io.BytesIO(decoded_image))

        failed = (
            (status_name is not None and status_name.upper() in {'FAILED', 'ERROR'})
            or status_upper.startswith('FAILED')
            or status_upper.startswith('ERROR')
        )

        if failed:
            LOGGER.debug("Generation reported failure status model=%s", model)
            return True, "Generation failed"
        else:
            # Still processing
            return False, None
    except Exception as e:
        LOGGER.exception("Exception polling generation result model=%s", model)
        return True, str(e)


