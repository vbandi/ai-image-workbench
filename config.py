"""
Configuration module for the Image Generator application.
Contains constants, model definitions, and application settings.
"""

from image_gen_api import MODELS

# Model categories for organized display
MODEL_CATEGORIES = {
"Flux": [
        "fal-ai/flux/schnell",
        "fal-ai/flux-1/srpo",
        "fal-ai/flux-pro/v1.1",
        "fal-ai/flux-pro/v1.1-ultra",
        "fal-ai/flux-2-flex",
        "fal-ai/flux-2-pro",
        "fal-ai/flux-2-max",
        "fal-ai/flux-2/flash",
        "fal-ai/flux-2/turbo",
        "fal-ai/flux-2/klein/9b/base",
        "fal-ai/flux-2/klein/4b",
        "fal-ai/flux-2/klein/4b/base"
    ],
    "HiDream": [
        "fal-ai/hidream-i1-fast",
        "fal-ai/hidream-i1-dev",
        "fal-ai/hidream-i1-full"
    ],
    "Imagen": [
        "fal-ai/imagen4/preview",
        "fal-ai/imagen4/preview/fast",
        "fal-ai/imagen4/preview/ultra"
    ],
    "Other": [
        "fal-ai/stable-diffusion-v35-large",
        "fal-ai/stable-diffusion-v35-medium",
        "fal-ai/ideogram/v2",
        "fal-ai/recraft-20b",
        "fal-ai/sana",
        "fal-ai/luma-photon",
        "fal-ai/bytedance/seedream/v3/text-to-image",
        "fal-ai/bytedance/seedream/v4/text-to-image",
        "fal-ai/bytedance/seedream/v4.5/text-to-image",
        "fal-ai/wan/v2.2-5b/text-to-image",
        "wan/v2.6/text-to-image",
        "fal-ai/gemini-25-flash-image",
        "fal-ai/gemini-3-pro-image-preview",
        "fal-ai/nano-banana",
        "fal-ai/qwen-image",
        "fal-ai/qwen-image-2512",
        "fal-ai/glm-image",
"bria/fibo/generate",
        "fal-ai/z-image/turbo",
        "fal-ai/longcat-image",
        "imagineart/imagineart-1.5-pro-preview/text-to-image"
    ]
}

# Model display name abbreviations for button labels
MODEL_ABBREVIATIONS = {
    # Flux Models
    "Flux Schnell": "Flux Schnell",
    "Flux-1-Srpo": "Flux SRPO",
    "Flux Pro V1.1": "Flux Pro",
    "Flux Pro V1.1 Ultra": "Flux Pro Ultra",
    "Flux-2-Flex": "Flux 2 Flex",
    "Flux-2-Pro": "Flux 2 Pro",
    "Flux-2-Max": "Flux 2 Max",
"Flux-2 Flash": "Flux 2 Flash",
    "Flux-2 Turbo": "Flux 2 Turbo",
    "Flux-2 Klein 9B Base": "Flux Klein 9B",
    "Flux-2 Klein 4B": "Flux Klein 4B",
    "Flux-2 Klein 4B Base": "Flux Klein 4B Base",
    # Imagen Models
    "Imagen4 Preview": "Imagen4",
    "Imagen4 Preview Fast": "Imagen4 Fast",
    "Imagen4 Preview Ultra": "Imagen4 Ultra",
    # HiDream Models
    "Hidream I1 Fast": "HiDream Fast",
    "Hidream I1 Dev": "HiDream Dev",
    "Hidream I1 Full": "HiDream Full",
    # Stable Diffusion Models
    "Stable-Diffusion-V35-Large": "SD35 Large",
    "Stable-Diffusion-V35-Medium": "SD35 Medium",
    # Other Models
    "Luma Photon": "Luma Photon",
    "Ideogram V2": "Ideogram v2",
    "Recraft 20B": "Recraft",
    "Sana": "Sana",
    "Bytedance Seedream V3 Text To Image": "Seedream v3",
    "Bytedance Seedream V4 Text To Image": "Seedream v4",
    "Bytedance Seedream V4.5 Text To Image": "Seedream v4.5",
    "Wan V2.2-5B Text To Image": "WAN v2.2",
    "Wan V2.6 Text To Image": "WAN v2.6",
    "Gemini 25 Flash Image": "Gemini Flash",
    "Gemini 3 Pro Image Preview": "Gemini 3 Pro",
    "Nano Banana": "Nano Banana",
    "Qwen Image": "Qwen Image",
    "Qwen Image 2512": "Qwen 2.5",
    "Z-Image Turbo": "Z-Image Turbo",
# BRIA models
    "Bria Fibo Generate": "BRIA Fibo",
    "Longcat-Image": "Longcat",
    "Glm-Image": "GLM Image",
    # ImagineArt models
    "Imagineart Imagineart 1.5 Pro Preview Text To Image": "ImagineArt 1.5 Pro"
}

# UI Constants
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Application settings
DEFAULT_MODEL = "fal-ai/flux/schnell"
AUTO_GENERATE_MODELS = ["fal-ai/flux/schnell", "fal-ai/flux-1/srpo", "fal-ai/flux-2/flash", "fal-ai/flux-2/klein/9b/base", "fal-ai/flux-2/klein/4b", "fal-ai/flux-2/klein/4b/base"]

# Window settings
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 600

# File settings
DEFAULT_SAVE_FORMAT = "JPEG"
DEFAULT_SAVE_EXTENSION = ".jpg"
SUPPORTED_SAVE_FORMATS = [("JPEG files", "*.jpg"), ("All files", "*.*")]

# UI Styling Constants
BACKGROUND_COLOR = '#f5f5f5'
SELECTED_BUTTON_COLOR = '#e0e0e0'
HOVER_BUTTON_COLOR = '#f0f0f0'
ACTIVE_BUTTON_COLOR = '#d0d0d0'
BASE_FONT = ('Segoe UI', 10)
BUTTON_FONT = ('Segoe UI', 10)
BUTTON_BOLD_FONT = ('Segoe UI', 10, 'bold')
ACCENT_COLOR = '#007bff'
ACCENT_HOVER_COLOR = '#0056b3'
TEXT_COLOR = '#333333'
PROMPT_FONT = ('Segoe UI', 11)
HEADER_FONT = ('Segoe UI', 12, 'bold')

# Threading Constants
UPDATE_THREAD_INTERVAL = 50
DISPLAY_QUEUE_CHECK_INTERVAL = 50
DEBOUNCE_DELAY_MS = 500

# Status Messages
class StatusMessages:
    """Centralized status messages for consistent UI text."""
    READY = "Ready"
    READY_CACHED = "Ready (Cached image)"
    GENERATING = "Generating image..."
    ENHANCING = "Enhancing prompt with AI..."
    ENHANCED = "Prompt enhanced successfully."
    NO_IMAGE_TO_SAVE = "No image to save."
    NO_IMAGE_TO_COPY = "No image to copy."
    COPIED_TO_CLIPBOARD = "Image copied to clipboard."
    COPY_NOT_SUPPORTED = "Copy not supported on this OS."
    ENTER_PROMPT = "Please enter a prompt to generate."
    ENTER_PROMPT_TO_ENHANCE = "Please enter a prompt to enhance."
    STAR_MODEL_FIRST = "Please star at least one model to use parallel generation."
    WAIT_FOR_GENERATION = "Please wait for the current generation to finish before starting parallel generation."
    PARALLEL_IN_PROGRESS = "Parallel generation is already in progress."
    PARALLEL_UNABLE = "Unable to start parallel generation."
    ALL_PARALLEL_COMPLETE = "All parallel generations completed"
