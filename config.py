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
        "fal-ai/flux-pro/v1.1-ultra"
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
        "fal-ai/wan/v2.2-5b/text-to-image",
        "fal-ai/gemini-25-flash-image",
        "fal-ai/nano-banana",
        "fal-ai/qwen-image",
        "bria/fibo/generate"
    ]
}

# Model display name abbreviations for button labels
MODEL_ABBREVIATIONS = {
    # Flux Models
    "Flux Schnell": "Flux Schnell",
    "Flux 1 Srpo": "Flux SRPO",
    "Flux Pro V1.1": "Flux Pro",
    "Flux Pro V1.1 Ultra": "Flux Pro Ultra",
    # Imagen Models
    "Imagen4 Preview": "Imagen4",
    "Imagen4 Preview Fast": "Imagen4 Fast",
    "Imagen4 Preview Ultra": "Imagen4 Ultra",
    # HiDream Models
    "Hidream I1 Fast": "HiDream Fast",
    "Hidream I1 Dev": "HiDream Dev",
    "Hidream I1 Full": "HiDream Full",
    # Stable Diffusion Models
    "Stable Diffusion V35 Large": "SD35 Large",
    "Stable Diffusion V35 Medium": "SD35 Medium",
    # Other Models
    "Luma Photon": "Luma Photon",
    "Ideogram V2": "Ideogram v2",
    "Recraft 20B": "Recraft",
    "Sana": "Sana",
    "Bytedance Seedream V3 Text To Image": "Seedream v3",
    "Bytedance Seedream V4 Text To Image": "Seedream v4",
    "Wan V2.2-5B Text To Image": "WAN v2.2",
    "Gemini 25 Flash Image": "Gemini Flash",
    "Nano Banana": "Nano Banana",
    "Qwen Image": "Qwen Image",
    # BRIA models
    "Bria Fibo Generate": "BRIA Fibo"
}

# UI Constants
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

# Application settings
DEFAULT_MODEL = "fal-ai/flux/schnell"
AUTO_GENERATE_MODELS = ["fal-ai/flux/schnell", "fal-ai/flux-1/srpo"]

# Window settings
MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 600

# Image settings
MIN_ZOOM_LEVEL = 0.1
MAX_ZOOM_LEVEL = 10.0
ZOOM_FACTOR = 1.1

# UI Colors
BACKGROUND_COLOR = '#f5f5f5'
FOOTER_BACKGROUND_COLOR = '#e0e0e0'
SELECTED_BUTTON_COLOR = '#C7E0F4'
HOVER_BUTTON_COLOR = '#E6F3FF'
ACTIVE_BUTTON_COLOR = '#A9D0F5'

# Font settings
BASE_FONT = ('Arial', 10)
BUTTON_FONT = ('Arial', 9)
BUTTON_BOLD_FONT = ('Arial', 9, 'bold')

# Threading settings
UPDATE_THREAD_INTERVAL = 30  # milliseconds
DISPLAY_QUEUE_CHECK_INTERVAL = 30  # milliseconds
CLIPBOARD_RETRY_ATTEMPTS = 5
CLIPBOARD_RETRY_DELAY = 0.01  # seconds

# File settings
DEFAULT_SAVE_FORMAT = "JPEG"
DEFAULT_SAVE_EXTENSION = ".jpg"
SUPPORTED_SAVE_FORMATS = [("JPEG files", "*.jpg"), ("All files", "*.*")]