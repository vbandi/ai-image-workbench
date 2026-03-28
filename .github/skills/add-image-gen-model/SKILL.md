---
name: add-image-gen-model
description: Add a new image generation model to the Python/Tkinter AI Image Workbench app, wiring API config, UI listing, and display label.
---

# Skill: Add Image Generation Model

## Purpose
Add a new image generation model to the Python/Tkinter AI Image Workbench app, including API wiring, UI listing, and display label.

## Applies To
- [image_gen_api.py](image_gen_api.py)
- [config.py](config.py)

## When To Use
Use this skill when you need to integrate a new fal.ai (or compatible) image model into the app.

## Prerequisites
- The model’s endpoint ID (e.g., `fal-ai/glm-image`).
- Basic API schema details (input args and output format).

## Steps
1. **Add model configuration** in `MODEL_REGISTRY`:
   - File: [image_gen_api.py](image_gen_api.py)
   - Add a new entry with `arguments` and `parser`.
   - Choose a parser:
     - `images_array` for `{ "images": [{"url": "..."}] }`.
     - `single_image` for `{ "image": {"url": "..."} }`.
     - `ideogram` for Ideogram v2 special formats.
     - `standard` for base64 data URI in `images[0].url`.
   - Set any model-specific arguments (e.g., `image_size`, `guidance_scale`, `num_inference_steps`, `output_format`, `sync_mode`).

2. **Add model to supported list**:
   - File: [image_gen_api.py](image_gen_api.py)
   - Append the model ID to the `MODELS` list.

3. **Add model to UI categories**:
   - File: [config.py](config.py)
   - Place the model ID in an appropriate `MODEL_CATEGORIES` section (usually `Other` unless it fits an existing group).

4. **Add a UI label**:
   - File: [config.py](config.py)
   - Add a display label in `MODEL_ABBREVIATIONS` using the cleaned model name key.
   - The cleaned key is produced by:
     - `model.replace("fal-ai/", "").replace("/", " ").title()`
   - Example:
     - Model ID `fal-ai/glm-image` → key `Glm-Image` → label `GLM Image`.

## Validation
- The app should show the new model button in the sidebar.
- Selecting the model and generating should return an image.

## Notes
- If the model requires different response parsing, implement or reuse a parser in `image_gen_api.py`.
- Keep changes minimal and aligned with existing defaults.
