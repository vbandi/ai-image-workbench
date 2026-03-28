"""
Configuration module for AI Image Workbench.
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
        "fal-ai/nano-banana-2",
        "fal-ai/qwen-image",
        "fal-ai/qwen-image-2512",
        "fal-ai/qwen-image-max/text-to-image",
        "fal-ai/qwen-image-2/text-to-image",
        "fal-ai/qwen-image-2/pro/text-to-image",
        "fal-ai/glm-image",
        "xai/grok-imagine-image",
        "fal-ai/hunyuan-image/v3/instruct/text-to-image",
"bria/fibo/generate",
        "fal-ai/z-image/base",
        "fal-ai/z-image/turbo",
        "fal-ai/longcat-image",
        "imagineart/imagineart-1.5-pro-preview/text-to-image",
        "fal-ai/kling-image/v3/text-to-image",
        "fal-ai/bitdance",
        "fal-ai/phota"
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
    "Nano-Banana-2": "Nano Banana 2",
    "Qwen Image": "Qwen Image",
    "Qwen Image 2512": "Qwen 2.5",
    "Qwen-Image-Max Text-To-Image": "Qwen Image Max",
    "Qwen-Image-2 Text-To-Image": "Qwen Image 2",
    "Qwen-Image-2 Pro Text-To-Image": "Qwen Image 2 Pro",
    "Z-Image Turbo": "Z-Image Turbo",
    "Xai Grok-Imagine-Image": "Grok Imagine",
    "Hunyuan-Image V3 Instruct Text-To-Image": "Hunyuan V3 Instruct",
    "Qwen-Image-Max Text-To-Image": "Qwen Image Max",
    "Z-Image Base": "Z-Image Base",
# BRIA models
    "Bria Fibo Generate": "BRIA Fibo",
    "Longcat-Image": "Longcat",
    "Glm-Image": "GLM Image",
    # ImagineArt models
    "Imagineart Imagineart 1.5 Pro Preview Text To Image": "ImagineArt 1.5 Pro",
    # Kling Image models
    "Kling-Image V3 Text-To-Image": "Kling Image v3",
    # Bitdance
    "Bitdance": "Bitdance",
    # Phota
    "Phota": "Phota"
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

# UI Styling Constants - Light Mode (Legacy - kept for backwards compatibility)
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

# Theme Color Definitions
THEMES = {
    'light': {
        'background': '#f5f5f5',
        'text': '#333333',
        'button_bg': '#ffffff',
        'selected_button': '#e0e0e0',
        'hover_button': '#f0f0f0',
        'active_button': '#d0d0d0',
        'accent': '#007bff',
        'accent_hover': '#0056b3',
        'canvas_bg': '#f5f5f5',
        'input_bg': '#ffffff',
        'border': '#d0d0d0',
        'category_bg': '#f3f4f6',
        'hidden_group': '#e5e7eb',
        'hidden_group_text': '#374151',
        'star_selected': '#f59e0b',
        'hide_selected': '#6b7280',
        'footer_bg': '#e4e6eb',
        'footer_text': '#65676b',
        'queue_bg': '#ffffff',
        'queue_highlight': '#e0e0e0',
        'tooltip_bg': '#ffffe0',
        'tooltip_text': '#000000',
        'status_error': '#dc3545',
        'status_success': '#28a745',
        'status_processing': '#007bff',
        'status_pending': '#666666',
        'status_cancelled': '#999999',
        'link_color': '#0078d4',
        'link_hover': '#004578',
        'scrollbar_bg': '#f0f0f0',
        'scrollbar_fg': '#007bff',
        'splitter_bg': '#e0e0e0',
        'trough_bg': '#f5f5f5',
    },
    'dark': {
        'background': '#1a1a1a',
        'text': '#ffffff',
        'button_bg': '#3a3a3a',
        'selected_button': '#3d5a80',
        'hover_button': '#4a6fa5',
        'active_button': '#5c8bd6',
        'accent': '#5c8bd6',
        'accent_hover': '#7aa3e0',
        'canvas_bg': '#1a1a1a',
        'input_bg': '#2d2d2d',
        'border': '#404040',
        'category_bg': '#252525',
        'hidden_group': '#2d2d2d',
        'hidden_group_text': '#a0a0a0',
        'star_selected': '#f59e0b',
        'hide_selected': '#9ca3af',
        'footer_bg': '#2d2d2d',
        'footer_text': '#a0a0a0',
        'queue_bg': '#2d2d2d',
        'queue_highlight': '#3d5a80',
        'tooltip_bg': '#3d3d3d',
        'tooltip_text': '#ffffff',
        'status_error': '#dc3545',
        'status_success': '#28a745',
        'status_processing': '#5c8bd6',
        'status_pending': '#808080',
        'status_cancelled': '#666666',
        'link_color': '#5c8bd6',
        'link_hover': '#7aa3e0',
        'scrollbar_bg': '#2d2d2d',
        'scrollbar_fg': '#5c8bd6',
        'splitter_bg': '#2d2d2d',
        'trough_bg': '#1a1a1a',
    }
}

# Current theme tracker
CURRENT_THEME = 'light'


def get_theme_color(color_key, theme=None):
    """Get a color value from the current or specified theme.
    
    Args:
        color_key: The key for the color (e.g., 'background', 'text', 'accent')
        theme: Optional theme name ('light' or 'dark'). If None, uses CURRENT_THEME.
    
    Returns:
        The color value (hex string) or None if key not found.
    """
    target_theme = theme if theme else CURRENT_THEME
    return THEMES.get(target_theme, THEMES['light']).get(color_key)


def set_theme(theme_name):
    """Set the current theme.
    
    Args:
        theme_name: 'light' or 'dark'
    """
    global CURRENT_THEME
    if theme_name in THEMES:
        CURRENT_THEME = theme_name


def get_current_theme():
    """Get the name of the current theme.
    
    Returns:
        'light' or 'dark'
    """
    return CURRENT_THEME

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
