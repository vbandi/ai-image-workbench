# AI Coding Agent Guide for AI Image Workbench

## Architecture Overview

This is a Python/Tkinter desktop application for AI image generation with a modular architecture. The main application coordinates between specialized modules:

- `main.py` - Main application class (entry point)
- `config.py` - All constants, model definitions, and UI settings
- `ui_components.py` - Specialized UI components (model selection, prompt input, controls)
- `image_gen_api.py` - AI image generation API integration
- `ai_api.py` - Prompt enhancement using OpenAI
- `image_handler.py` - Image processing (zoom, pan, display)
- `clipboard_manager.py` - Cross-platform clipboard operations
- `threading_utils.py` - Background processing and queue management

## Key Patterns and Conventions

### 1. Modular Design
- Each module has a single responsibility
- UI components are separated from business logic
- Background operations use dedicated threading utilities
- Configuration is centralized in `config.py`
- Model memory system caches generated images per model (in-memory only)

### 2. Model Organization
AI models are categorized in `config.py`:
- Flux models (fastest)
- HiDream models
- Imagen models
- Other models (Stable Diffusion, Ideogram, etc.)

Each model requires specific parameter handling in `image_gen_api.py`.

### 3. Threading Pattern
- Uses `GenerationQueueManager` for image generation requests
- Uses `UpdateThreadManager` for UI updates
- Main thread handles UI events
- Background threads handle API calls and image processing

### 4. UI Component Pattern
- Components are encapsulated in classes (`ModelSelectionFrame`, `ControlPanel`, `PromptInputFrame`)
- Each component manages its own state and events
- Components communicate via callback functions

### 5. Model Memory System
- Generated images are cached per model (in-memory)
- Visual tick marks (✓) indicate models with cached images
- Cache is cleared when prompt changes
- Clicking a ticked model instantly shows cached image
- Improves workflow by allowing quick model comparisons

## Integration Points

### 1. AI Image Generation API
- All models integrated through `fal_client` in `image_gen_api.py`
- Each model requires specific response parsing logic
- Model-specific parameters are handled in `generate_image()` function

### 2. OpenAI Prompt Enhancement
- Integrated in `ai_api.py`
- Uses `gpt-4-turbo` model for prompt enhancement
- Requires `OPENAI_API_KEY` environment variable

### 3. Clipboard Operations
- Windows-specific implementation in `clipboard_manager.py`
- Converts PIL images to DIB format for clipboard compatibility

### 4. Image Display
- Uses `ImageDisplayManager` for zoom/pan functionality
- Dynamically resizes images to fit display frame

## Critical Developer Workflows

### 1. Adding New AI Models
1. Add model identifier to `MODELS` list in `image_gen_api.py`
2. Add model to appropriate category in `config.py`
3. Add model abbreviation in `config.py`
4. Update `generate_image()` function with model-specific logic if needed
5. Add response parsing function if format differs from standard

### 2. UI Component Development
1. Create new component classes in `ui_components.py`
2. Use callback pattern for communication with main application
3. Follow existing styling conventions from `config.py`

### 3. Image Processing Features
1. Extend `ImageProcessor` class in `image_handler.py`
2. Update `create_display_image()` method as needed
3. Add new event handlers in main application

## External Dependencies

- `tkinter` - UI framework
- `PIL (Pillow)` - Image processing
- `fal_client` - AI image generation API
- `openai` - Prompt enhancement API
- `ctypes` - Windows clipboard operations

## Testing Approach

- Manual testing via application execution
- No automated test framework currently implemented
- Test by running `python main.py` and verifying functionality