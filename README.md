# AI Image Generator

A Python desktop application for generating AI images using various models through the Fal.ai API. This application provides a user-friendly Tkinter interface for creating images from text prompts.

## Features

- **Multiple AI Models**: Support for various image generation models including Flux, Imagen, HiDream, Stable Diffusion, and more
- **Model Memory System**: Caches generated images per model for quick comparison and re-selection
- **Prompt Enhancement**: Uses OpenAI GPT to enhance user prompts for better results
- **Threading**: Background processing to keep the UI responsive during image generation
- **Clipboard Integration**: Easy copying of generated images to clipboard
- **Zoom and Pan**: Interactive image viewing with zoom and pan controls

## Screenshot

Here's an example of the application running with a generated beautiful mountain landscape:

![Mountain Landscape](mountain_landscape.png)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/vbandi/image-generator-python.git
   cd image-generator-python
   ```

2. Install dependencies:
   ```bash
   pip install fal-client openai pillow requests
   ```

3. Set up environment variables:
   - `FAL_KEY`: Your Fal.ai API key
   - `OPENAI_API_KEY`: Your OpenAI API key (for prompt enhancement)

## Usage

Run the application:
```bash
python ui_app_refactored.py
```

1. Select an AI model from the dropdown
2. Enter your image prompt
3. Optionally enhance the prompt using AI
4. Click "Generate" to create the image
5. Use the controls to zoom, pan, or copy the image

## Architecture

- `ui_app_refactored.py`: Main application entry point
- `image_gen_api.py`: API integration for image generation
- `ai_api.py`: OpenAI integration for prompt enhancement
- `image_handler.py`: Image processing utilities
- `config.py`: Application configuration and constants
- `threading_utils.py`: Background processing management

## Models Supported

- Flux models (fast generation)
- Imagen models
- HiDream models
- Stable Diffusion variants
- And many more...

## Requirements

- Python 3.8+
- Tkinter (usually included with Python)
- Internet connection for API calls

## License

This project is private and proprietary.