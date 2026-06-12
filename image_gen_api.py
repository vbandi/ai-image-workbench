"""Image Generation API module for handling various AI image generation models."""

import base64
import io
import logging
import time
from typing import Dict, Any, Callable, Optional, TypedDict

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


# =============================================================================
# Response Parsers - Consolidated into 3 generic patterns
# =============================================================================

def _download_from_url(url: str) -> bytes:
    """Download image content from a URL, handling data URIs."""
    if url.startswith("data:"):
        # Handle data URI (e.g., "data:image/jpeg;base64,...")
        return base64.b64decode(url.split(",")[1])
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def _parse_images_array_url(result: Dict[str, Any], model_name: str) -> bytes:
    """
    Parse response with format: {"images": [{"url": "..."}]}
    Used by: Imagen4, Gemini Flash, SeeDream, Nano Banana, Qwen, Gemini 3 Pro, Flux 2 Flex, FLUX PRO
    """
    if "images" not in result or not isinstance(result["images"], list) or len(result["images"]) == 0:
        raise ValueError(f"Could not extract image from {model_name} response: {result}")
    
    image_obj = result["images"][0]
    if isinstance(image_obj, dict) and "url" in image_obj:
        return _download_from_url(image_obj["url"])
    raise ValueError(f"Unexpected {model_name} image format: {image_obj}")


def _parse_single_image_url(result: Dict[str, Any], model_name: str) -> bytes:
    """
    Parse response with format: {"image": {"url": "..."}}
    Used by: WAN, BRIA FIBO
    """
    if "image" not in result or not isinstance(result["image"], dict) or "url" not in result["image"]:
        raise ValueError(f"Could not extract image from {model_name} response: {result}")
    
    return _download_from_url(result["image"]["url"])


def _parse_ideogram_response(result: Dict[str, Any]) -> bytes:
    """
    Parse Ideogram v2 response - handles multiple formats.
    Format 1: {"images": ["url_or_data_uri"]}
    Format 2: {"image": "url_or_data_uri"}
    Format 3: {"result": {"images": [...]}}
    """
    # Format 1: Direct array of image URLs or data URIs
    if "images" in result and isinstance(result["images"], list) and len(result["images"]) > 0:
        encoded_image = result["images"][0]
        if isinstance(encoded_image, str):
            return _download_from_url(encoded_image)
    
    # Format 2: Object with image property
    if "image" in result and isinstance(result["image"], str):
        return _download_from_url(result["image"])
    
    # Format 3: Nested structure
    if "result" in result and "images" in result["result"]:
        encoded_image = result["result"]["images"][0]
        if isinstance(encoded_image, str):
            return _download_from_url(encoded_image)
    
    raise ValueError(f"Could not extract image from Ideogram v2 response: {result}")


def _parse_standard_response(result: Dict[str, Any], model_name: str) -> bytes:
    """Parse standard response format with base64 data URI in images array."""
    if "images" not in result or not result["images"]:
        raise ValueError(f"Could not extract image from {model_name} response: {result}")
    image_data = result["images"][0]
    encoded_image = image_data["url"]
    return base64.b64decode(encoded_image.split(",")[1])


# =============================================================================
# Model Configuration Registry
# =============================================================================

class ModelConfig(TypedDict, total=False):
    """Configuration for a model's API arguments and response parser."""
    arguments: Dict[str, Any]
    parser: str  # Parser function name: "images_array", "single_image", "ideogram", "standard"


# Default arguments applied to all models unless overridden
_DEFAULT_ARGUMENTS: Dict[str, Any] = {
    "prompt": "",  # Placeholder - always replaced
    "num_images": 1,
    "enable_safety_checker": False,
    "enable_prompt_expansion": False,
    "expand_prompt": False,
    "image_size": "landscape_4_3",
    "sync_mode": True,
    "safety_tolerance": 5,
}

# Model-specific configurations
MODEL_REGISTRY: Dict[str, ModelConfig] = {
    # Ideogram - unique response format
    "fal-ai/ideogram/v2": {
        "arguments": {
            "enable_safety_checker": False,
            "safety_tolerance": 5,
        },
        "parser": "ideogram",
    },
    
    # Imagen4 variants - images array with URL objects
    "fal-ai/imagen4/preview": {
        "arguments": {
            "num_images": 1,
            "aspect_ratio": "4:3",
            "enable_safety_checker": False,
            "safety_tolerance": 5,
        },
        "parser": "images_array",
    },
    "fal-ai/imagen4/preview/fast": {
        "arguments": {
            "num_images": 1,
            "aspect_ratio": "4:3",
            "enable_safety_checker": False,
            "safety_tolerance": 5,
        },
        "parser": "images_array",
    },
    "fal-ai/imagen4/preview/ultra": {
        "arguments": {
            "num_images": 1,
            "aspect_ratio": "4:3",
            "enable_safety_checker": False,
            "safety_tolerance": 5,
        },
        "parser": "images_array",
    },
    
    # Gemini models
    "fal-ai/gemini-25-flash-image": {
        "arguments": {
            "num_images": 1,
        },
        "parser": "images_array",
    },
    "fal-ai/gemini-3-pro-image-preview": {
        "arguments": {
            "num_images": 1,
            "aspect_ratio": "4:3",
            "sync_mode": True,
        },
        "parser": "images_array",
    },
    
    # Flux models
    "fal-ai/flux-1/srpo": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
            "guidance_scale": 4.5,
            "num_inference_steps": 28,
            "sync_mode": True,
        },
        "parser": "images_array",
    },
    "fal-ai/flux-2-flex": {
        "arguments": {
            "image_size": "landscape_4_3",
            "safety_tolerance": "5",
            "enable_safety_checker": False,
            "output_format": "jpeg",
            "guidance_scale": 3.5,
            "num_inference_steps": 28,
        },
        "parser": "images_array",
    },
    "fal-ai/flux-2-pro": {
        "arguments": {
            "image_size": "landscape_4_3",
            "safety_tolerance": 5,
            "enable_safety_checker": False,
            "output_format": "jpeg",
            "sync_mode": True,
        },
        "parser": "images_array",
    },
    "fal-ai/flux-2-max": {
        "arguments": {
            "image_size": "landscape_4_3",
            "safety_tolerance": 5,
            "enable_safety_checker": False,
            "output_format": "jpeg",
            "sync_mode": True,
        },
        "parser": "images_array",
    },
    "fal-ai/flux-2/flash": {
        "arguments": {
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
            "output_format": "jpeg",
            "guidance_scale": 2.5,
        },
        "parser": "images_array",
    },
    "fal-ai/flux-2/klein/9b/base": {
        "arguments": {
            "image_size": "landscape_4_3",
            "guidance_scale": 5,
            "num_inference_steps": 28,
            "acceleration": "high",
            "enable_safety_checker": False,
            "output_format": "png",
        },
        "parser": "images_array",
    },
    "fal-ai/flux-2/klein/4b": {
        "arguments": {
            "image_size": "landscape_4_3",
            "num_inference_steps": 4,
            "enable_safety_checker": False,
            "output_format": "png",
        },
        "parser": "images_array",
    },
    "fal-ai/flux-2/klein/4b/base": {
        "arguments": {
            "image_size": "landscape_4_3",
            "guidance_scale": 5,
            "num_inference_steps": 28,
            "acceleration": "high",
            "enable_safety_checker": False,
            "output_format": "png",
        },
        "parser": "images_array",
    },
    
    # SeeDream models
    "fal-ai/bytedance/seedream/v3/text-to-image": {
        "arguments": {
            "num_images": 1,
            "enable_safety_checker": False,
            "safety_tolerance": 5,
        },
        "parser": "images_array",
    },
    "fal-ai/bytedance/seedream/v4/text-to-image": {
        "arguments": {
            "num_images": 1,
            "enable_safety_checker": False,
            "safety_tolerance": 5,
        },
        "parser": "images_array",
    },
    "fal-ai/bytedance/seedream/v4.5/text-to-image": {
        "arguments": {
            "num_images": 1,
            "enable_safety_checker": False,
            "safety_tolerance": 5,
        },
        "parser": "images_array",
    },
    
    # WAN - single image response format
    "fal-ai/wan/v2.2-5b/text-to-image": {
        "arguments": {
            "num_inference_steps": 40,
            "enable_safety_checker": False,
            "guidance_scale": 3.5,
            "shift": 2,
            "image_size": "landscape_4_3",
        },
        "parser": "single_image",
    },
    "wan/v2.6/text-to-image": {
        "arguments": {
            "max_images": 1,
            "negative_prompt": "",
            "image_size": "landscape_16_9",
            "enable_safety_checker": False,
        },
        "parser": "images_array",
    },
    "fal-ai/wan/v2.7/text-to-image": {
        "arguments": {
            "max_images": 1,
            "negative_prompt": "",
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
        },
        "parser": "images_array",
    },
    
    # Other models with images array format
    "fal-ai/nano-banana": {
        "arguments": {
            "num_images": 1,
            "aspect_ratio": "4:3",
            "enable_safety_checker": False,
            "safety_tolerance": 5,
        },
        "parser": "images_array",
    },
    "fal-ai/nano-banana-2": {
        "arguments": {
            "num_images": 1,
            "aspect_ratio": "4:3",
            "output_format": "png",
            "safety_tolerance": "4",
            "image_size": None,
            "enable_safety_checker": False,
        },
        "parser": "images_array",
    },
    "fal-ai/qwen-image": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
            "guidance_scale": 2.5,
            "num_inference_steps": 30,
        },
        "parser": "images_array",
    },
    "fal-ai/qwen-image-2512": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
            "guidance_scale": 5,
            "num_inference_steps": 28,
        },
        "parser": "images_array",
    },
    "fal-ai/glm-image": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
            "output_format": "jpeg",
            "sync_mode": True,
        },
        "parser": "images_array",
    },
    "xai/grok-imagine-image": {
        "arguments": {
            "num_images": 1,
            "aspect_ratio": "4:3",
            "output_format": "jpeg",
            "sync_mode": True,
        },
        "parser": "images_array",
    },
    "fal-ai/hunyuan-image/v3/instruct/text-to-image": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
            "output_format": "png",
            "sync_mode": True,
            "guidance_scale": 3.5,
            "num_inference_steps": 28,
        },
        "parser": "images_array",
    },
    "microsoft/mai-image-2.5": {
        "arguments": {
            "num_images": 1,
            "aspect_ratio": "auto",
            "output_format": "png",
            "enable_safety_checker": False,
            "sync_mode": True,
        },
        "parser": "images_array",
    },
    "fal-ai/qwen-image-max/text-to-image": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
            "output_format": "png",
            "sync_mode": True,
        },
        "parser": "images_array",
    },
    "fal-ai/qwen-image-2/text-to-image": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
            "output_format": "png",
            "sync_mode": True,
            "safety_tolerance": None,
        },
        "parser": "images_array",
    },
    "fal-ai/qwen-image-2/pro/text-to-image": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
            "output_format": "png",
            "sync_mode": True,
            "safety_tolerance": None,
        },
        "parser": "images_array",
    },
    "fal-ai/z-image/base": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "num_inference_steps": 28,
            "guidance_scale": 4,
            "enable_safety_checker": False,
            "output_format": "png",
            "sync_mode": True,
        },
        "parser": "images_array",
    },
    
    # BRIA - single image response format
    "bria/fibo/generate": {
        "arguments": {
            "aspect_ratio": "4:3",
        },
        "parser": "single_image",
    },
    # Bitdance
    "fal-ai/bitdance": {
        "arguments": {
            "image_size": "landscape_4_3",
            "num_images": 1,
            "enable_safety_checker": False,
            "output_format": "jpeg",
            "sync_mode": True,
            "safety_tolerance": None,  # not supported by this model
        },
        "parser": "images_array",
    },
    "fal-ai/longcat-image": {
        "arguments": {
            "image_size": None,
            "num_images": None,
            "enable_safety_checker": False,
            "safety_tolerance": None,
        },
        "parser": "images_array",
    },
    
    # ImagineArt models
    "imagineart/imagineart-1.5-pro-preview/text-to-image": {
        "arguments": {
            "aspect_ratio": "4:3",
        },
        "parser": "images_array",
    },
    
    # Flux 2 Turbo
    "fal-ai/flux-2/turbo": {
        "arguments": {
            "image_size": "landscape_4_3",
            "guidance_scale": 2.5,
            "num_images": 1,
            "enable_safety_checker": False,
            "output_format": "jpeg",
        },
        "parser": "images_array",
    },
    
    # Kling Image v3
    "fal-ai/kling-image/v3/text-to-image": {
        "arguments": {
            "num_images": 1,
            "resolution": "1K",
            "aspect_ratio": "4:3",
            "output_format": "png",
        },
        "parser": "images_array",
    },
    
    # Phota (Grok Imagine)
    "fal-ai/phota": {
        "arguments": {
            "num_images": 1,
            "output_format": "jpeg",
            "resolution": "1K",
            "aspect_ratio": "4:3",
            "image_size": None,
            "enable_safety_checker": False,
            "safety_tolerance": None,
        },
        "parser": "images_array",
    },

    # HiDream O1
    "fal-ai/hidream-o1-image": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
        },
        "parser": "images_array",
    },
    "fal-ai/hidream-o1-image/dev": {
        "arguments": {
            "num_images": 1,
            "image_size": "landscape_4_3",
            "enable_safety_checker": False,
        },
        "parser": "images_array",
    },

    # Luma Uni-1
    "luma/agent/uni-1/v1/text-to-image": {
        "arguments": {
            "aspect_ratio": "3:2",
            "style": "auto",
            "output_format": "jpeg",
            "num_images": None,
            "enable_safety_checker": False,
            "image_size": None,
            "sync_mode": None,
            "safety_tolerance": None,
        },
        "parser": "images_array",
    },
    "luma/agent/uni-1/v1/max": {
        "arguments": {
            "aspect_ratio": "3:2",
            "style": "auto",
            "output_format": "jpeg",
            "num_images": None,
            "enable_safety_checker": False,
            "image_size": None,
            "sync_mode": None,
            "safety_tolerance": None,
        },
        "parser": "images_array",
    },

    # Krea v2
    "krea/v2/large/text-to-image": {
        "arguments": {
            "aspect_ratio": "4:3",
            "creativity": "medium",
            "num_images": None,
            "enable_safety_checker": False,
            "image_size": None,
            "sync_mode": None,
            "safety_tolerance": 5,
        },
        "parser": "images_array",
    },
    "krea/v2/medium/text-to-image": {
        "arguments": {
            "aspect_ratio": "4:3",
            "creativity": "medium",
            "num_images": None,
            "enable_safety_checker": False,
            "image_size": None,
            "sync_mode": None,
            "safety_tolerance": 5,
        },
        "parser": "images_array",
    },
}

# Parser function mapping
_PARSERS: Dict[str, Callable[[Dict[str, Any], str], bytes]] = {
    "images_array": _parse_images_array_url,
    "single_image": _parse_single_image_url,
    "ideogram": lambda result, _: _parse_ideogram_response(result),
    "standard": _parse_standard_response,
}


# Available models - derived from registry + defaults
MODELS = [
    "fal-ai/flux/schnell",
    "fal-ai/flux-1/srpo",
    "fal-ai/flux-pro/v1.1",
    "fal-ai/flux-pro/v1.1-ultra",
    "fal-ai/flux-2-flex",
    "fal-ai/flux-2-pro",
    "fal-ai/flux-2-max",
    "fal-ai/flux-2/flash",
    "fal-ai/flux-2/klein/9b/base",
    "fal-ai/flux-2/klein/4b",
    "fal-ai/flux-2/klein/4b/base",
    "fal-ai/imagen4/preview",
    "fal-ai/imagen4/preview/fast",
    "fal-ai/imagen4/preview/ultra",
    "fal-ai/hidream-i1-fast",
    "fal-ai/hidream-i1-dev",
    "fal-ai/hidream-i1-full",
    "fal-ai/hidream-o1-image",
    "fal-ai/hidream-o1-image/dev",
    "fal-ai/stable-diffusion-v35-large",
    "fal-ai/stable-diffusion-v35-medium",
    "fal-ai/luma-photon",
    "luma/agent/uni-1/v1/text-to-image",
    "luma/agent/uni-1/v1/max",
    "fal-ai/ideogram/v2",
    "fal-ai/recraft-20b",
    "fal-ai/sana",
    "fal-ai/bytedance/seedream/v3/text-to-image",
    "fal-ai/bytedance/seedream/v4/text-to-image",
    "fal-ai/bytedance/seedream/v4.5/text-to-image",
    "fal-ai/wan/v2.2-5b/text-to-image",
    "wan/v2.6/text-to-image",
    "fal-ai/wan/v2.7/text-to-image",
    "fal-ai/gemini-25-flash-image",
    "fal-ai/gemini-3-pro-image-preview",
    "fal-ai/nano-banana",
    "fal-ai/nano-banana-2",
    "fal-ai/qwen-image",
    "fal-ai/qwen-image-2512",
    "fal-ai/qwen-image-max/text-to-image",
    "fal-ai/qwen-image-2/text-to-image",
    "fal-ai/qwen-image-2/pro/text-to-image",
    "fal-ai/glm-image",
    "xai/grok-imagine-image",
    "fal-ai/hunyuan-image/v3/instruct/text-to-image",
    "microsoft/mai-image-2.5",
"bria/fibo/generate",
    "fal-ai/z-image/base",
    "fal-ai/z-image/turbo",
    "fal-ai/longcat-image",
    "imagineart/imagineart-1.5-pro-preview/text-to-image",
    "fal-ai/flux-2/turbo",
    "fal-ai/kling-image/v3/text-to-image",
    "fal-ai/bitdance",
    "fal-ai/phota",
    "krea/v2/large/text-to-image",
    "krea/v2/medium/text-to-image",
]


# =============================================================================
# API Functions
# =============================================================================

def _get_model_arguments(model: str, prompt: str) -> Dict[str, Any]:
    """Build API arguments for a model using registry or defaults."""
    config = MODEL_REGISTRY.get(model, {})
    model_args = config.get("arguments", {})
    
    # Start with defaults, override with model-specific args
    arguments = {**_DEFAULT_ARGUMENTS, **model_args}
    arguments["prompt"] = prompt
    
    # Filter out None values to allow unsetting defaults
    return {k: v for k, v in arguments.items() if v is not None}


def _get_parser(model: str) -> Callable[[Dict[str, Any], str], bytes]:
    """Get the response parser for a model."""
    config = MODEL_REGISTRY.get(model, {})
    parser_name = config.get("parser", "standard")
    return _PARSERS.get(parser_name, _parse_standard_response)


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
    
    arguments = _get_model_arguments(model, prompt)
    return fal_client.submit(model, arguments=arguments)


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
        status_type_name = type(status).__name__
        LOGGER.debug(
            "Polled status model=%s status=%s name=%s type=%s", model, status_str, status_name, status_type_name
        )

        # Determine completion by checking:
        # 1. Status class type name (newer fal_client versions use Completed/InProgress classes)
        # 2. Status name attribute
        # 3. String representation prefix
        completed = (
            status_type_name == 'Completed'
            or (status_name is not None and status_name.upper() == 'COMPLETED')
            or status_upper.startswith('COMPLETED')
            or status_upper.startswith('SUCCESS')
            or status_upper.startswith('DONE')
        )

        if completed:
            result = handle.get()
            parser = _get_parser(model)
            decoded_image = parser(result, model)
            return True, Image.open(io.BytesIO(decoded_image))

        failed = (
            status_type_name == 'Failed'
            or (status_name is not None and status_name.upper() in {'FAILED', 'ERROR'})
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
