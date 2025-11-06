# Model Memory Feature

## Overview

The Image Generator now includes a model memory feature that caches generated images per model and displays visual indicators (tick marks) on models that have generated images. This allows quick switching between models to compare results without regenerating images.

## Features

### 1. Image Caching
- Each model remembers its last generated image for the current prompt
- Images are stored in memory only (not saved to disk)
- Cache is automatically managed based on prompt changes

### 2. Visual Indicators (Ticks)
- Models that have generated images show a checkmark (✓) next to their name
- Ticks are displayed on the model selection buttons
- Example: "✓ Flux Schnell" instead of just "Flux Schnell"

### 3. Quick Model Switching
- Clicking a **different** model with a tick instantly shows its cached image (no regeneration)
- Clicking the **same** model (already selected) always triggers regeneration
- No need to wait for API calls when switching back to a model you've already used
- Seamless comparison between different model outputs

### 4. Automatic Cache Management
- Cache is cleared when the prompt changes
- All tick marks are removed when cache is cleared
- Ensures memory efficiency and prevents showing outdated results

## User Workflow

### Typical Usage Scenario

1. **Enter a prompt**: Type your image description in the prompt field

2. **Generate with first model**: 
   - Select a model (e.g., "Flux Schnell")
   - Image generates, model button shows "✓ Flux Schnell"
   - Image is cached for this model

3. **Try another model**:
   - Click another model (e.g., "Flux Pro")
   - Image generates automatically
   - Model button shows "✓ Flux Pro"
   - This image is also cached

4. **Compare results**:
   - Click "✓ Flux Schnell" → Instantly shows the first image
   - Click "✓ Flux Pro" → Instantly shows the second image
   - No regeneration needed!
   - Click "✓ Flux Pro" again → Regenerates with Flux Pro (reselection)

5. **Change prompt**:
   - Modify your prompt text
   - Trigger generation (press Enter, click Generate, or auto-generate)
   - All ticks disappear
   - Cache is cleared
   - Fresh generation starts

## Regeneration Triggers

The following actions trigger image regeneration (and clear cache if prompt changed):

1. **Clicking the Generate button**
2. **Pressing Enter while editing the prompt** (if auto-generate is disabled)
3. **Auto-generation while typing** (if enabled for the model)
4. **Clicking on a model button that doesn't have a tick**
5. **Clicking on the currently selected model** (reselection always regenerates)
6. **Enhancing the prompt** (with or without directions)

## Cache Invalidation

The cache is automatically cleared in these situations:

1. **Prompt text changes and generation is triggered**
   - Type new text → press Enter: cache clears before generation
   - Type new text → click Generate: cache clears before generation
   - Type new text → auto-generate fires: cache clears before generation

2. **Prompt enhancement**
   - Using "Enhance" or "Enhance..." buttons clears cache
   - The enhanced prompt is treated as a new prompt

## Technical Implementation

### Key Components

#### `ui_app_refactored.py`
- **`model_image_cache`**: Dictionary storing `{model_name: PIL.Image}` mappings
- **`current_prompt`**: Tracks the current prompt to detect changes
- **`_clear_model_cache()`**: Clears cache and removes all tick marks
- **`_on_model_select()`**: Checks cache before generating
- **`_generate_image()`**: Caches generated images

#### `ui_components.py`
- **`models_with_ticks`**: Set tracking which models have generated images
- **`model_button_texts`**: Stores original button text (without ticks)
- **`set_model_generated()`**: Adds tick mark to a model button
- **`clear_all_ticks()`**: Removes all tick marks
- **`_update_button_text()`**: Updates button text with/without tick

### Data Flow

```
1. User enters prompt
   ↓
2. Selects model A → Generates → Image cached for model A → Tick added
   ↓
3. Selects model B → Generates → Image cached for model B → Tick added
   ↓
4. Clicks model A → Shows cached image (no generation)
   ↓
5. Modifies prompt + triggers generation → Cache cleared, ticks removed
   ↓
6. Fresh generation starts
```

## Benefits

1. **Faster comparisons**: No waiting when switching back to previous models
2. **Better workflow**: Easily compare outputs from different models
3. **Memory efficient**: Cache is automatically cleared when no longer relevant
4. **Visual feedback**: Clear indication of which models have been tried
5. **Seamless UX**: Works transparently with existing features

## Memory Management

- Images are stored as PIL Image objects in memory
- Typical memory usage: ~1-5 MB per cached image (depends on resolution)
- Cache is cleared on prompt change to prevent memory buildup
- Maximum cache size = number of models × average image size
- Example: 20 models × 3 MB = ~60 MB maximum (only if all models used)

## Testing

Run the test suite to verify the feature:

```bash
python test_model_memory.py
```

The test verifies:
- Initial empty state
- Cache storage after generation
- Tick mark display on buttons
- Cache clearing functionality
- Multiple model caching
- Complete tick removal

## Future Enhancements

Possible improvements for future versions:

1. **Persistent cache**: Store images to disk for session persistence
2. **Cache size limit**: Implement LRU eviction policy
3. **Thumbnail preview**: Show small previews of cached images
4. **Cache statistics**: Display memory usage and cache hit rate
5. **Manual cache control**: Allow users to clear cache manually
6. **Per-prompt history**: Keep a history of prompts and their generated images

## Known Limitations

1. **Memory only**: Cache is lost when application closes
2. **Single image per model**: Only the most recent image is cached per model
3. **No partial updates**: Changing any part of the prompt clears entire cache
4. **No cache persistence**: Cannot recover cached images after restart

## Compatibility

- Works with all existing models and features
- Compatible with auto-generate functionality
- Works with prompt enhancement features
- No breaking changes to existing workflows
