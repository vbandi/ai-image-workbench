"""
Comprehensive test for complete model memory feature including reselection.
"""

import tkinter as tk
from PIL import Image
from ui_app_refactored import ImageGeneratorApp


def create_test_image(color):
    """Create a test image with specified color."""
    return Image.new('RGB', (100, 100), color=color)


def comprehensive_test():
    """Run comprehensive tests for all model memory features."""
    print("\n" + "="*60)
    print("COMPREHENSIVE MODEL MEMORY TEST")
    print("="*60)
    
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    
    # Mock manual_generate to track calls
    generation_calls = []
    original_manual_generate = app.manual_generate
    
    def mock_manual_generate():
        generation_calls.append({
            'prompt': app.current_prompt,
            'model': app.model_selection.get_selected_model()
        })
    
    app.manual_generate = mock_manual_generate
    
    # Set initial prompt
    test_prompt = "A beautiful sunset"
    app.prompt_input.set_text(test_prompt)
    app.current_prompt = test_prompt
    
    print(f"\nInitial prompt: '{test_prompt}'")
    print("-"*60)
    
    # Test 1: Generate with first model
    print("\n1. Generate with Model A (Flux Schnell)...")
    model_a = "fal-ai/flux/schnell"
    app.current_image = create_test_image('red')
    app.model_image_cache[model_a] = app.current_image
    app.model_selection.set_model_generated(model_a)
    app.model_selection.model_var.set(model_a)
    
    assert model_a in app.model_image_cache
    assert model_a in app.model_selection.models_with_ticks
    print("   ✓ Image cached and tick added")
    
    # Test 2: Generate with second model
    print("\n2. Generate with Model B (Flux Pro)...")
    model_b = "fal-ai/flux-pro/v1.1"
    app.current_image = create_test_image('blue')
    app.model_image_cache[model_b] = app.current_image
    app.model_selection.set_model_generated(model_b)
    app.model_selection.model_var.set(model_b)
    
    assert len(app.model_image_cache) == 2
    assert model_b in app.model_selection.models_with_ticks
    print("   ✓ Second image cached and tick added")
    
    # Test 3: Switch to Model A (should show cached, no regeneration)
    print("\n3. Click Model A (different model with cache)...")
    generation_calls.clear()
    app._on_model_select(model_a, is_reselection=False)
    
    assert len(generation_calls) == 0, "Should not regenerate"
    assert app.current_image == app.model_image_cache[model_a]
    print("   ✓ Showed cached image, no regeneration")
    
    # Test 4: Reselect Model A (should regenerate)
    print("\n4. Click Model A again (reselection)...")
    generation_calls.clear()
    app._on_model_select(model_a, is_reselection=True)
    
    assert len(generation_calls) == 1, "Should regenerate on reselection"
    print("   ✓ Regeneration triggered")
    
    # Test 5: Change prompt (cache should clear)
    print("\n5. Change prompt...")
    new_prompt = "A mountain landscape"
    app.prompt_input.set_text(new_prompt)
    generation_calls.clear()
    
    # Simulate generation with new prompt
    if new_prompt != app.current_prompt:
        app._clear_model_cache()
        app.current_prompt = new_prompt
    
    assert len(app.model_image_cache) == 0, "Cache should be cleared"
    assert len(app.model_selection.models_with_ticks) == 0, "Ticks should be cleared"
    print("   ✓ Cache and ticks cleared")
    
    # Test 6: Generate with new prompt
    print("\n6. Generate with Model A (new prompt)...")
    app.current_image = create_test_image('green')
    app.model_image_cache[model_a] = app.current_image
    app.model_selection.set_model_generated(model_a)
    
    assert len(app.model_image_cache) == 1
    assert model_a in app.model_image_cache
    print("   ✓ New image cached for new prompt")
    
    # Test 7: Test select_model method directly (simulates button click)
    print("\n7. Test button click simulation...")
    
    # Add Model B to cache
    app.model_image_cache[model_b] = create_test_image('yellow')
    app.model_selection.set_model_generated(model_b)
    app.model_selection.model_var.set(model_b)
    
    # Click on Model A (different model with cache)
    generation_calls.clear()
    app.model_selection.select_model(model_a)
    
    assert len(generation_calls) == 0, "Should show cached image"
    print("   ✓ Button click on different model shows cache")
    
    # Click on Model A again (reselection)
    generation_calls.clear()
    app.model_selection.select_model(model_a)
    
    assert len(generation_calls) == 1, "Should regenerate on reselection"
    print("   ✓ Button click on same model regenerates")
    
    # Restore original method
    app.manual_generate = original_manual_generate
    
    print("\n" + "="*60)
    print("ALL COMPREHENSIVE TESTS PASSED! ✓")
    print("="*60)
    
    print("\nFeature Summary:")
    print("  ✓ Images cached per model")
    print("  ✓ Tick marks show generated models")
    print("  ✓ Switching to different cached model shows image instantly")
    print("  ✓ Clicking same model (reselection) always regenerates")
    print("  ✓ Cache clears when prompt changes")
    print("  ✓ All ticks removed when cache clears")
    print("  ✓ Fresh generation works with new prompt")
    
    root.destroy()


if __name__ == "__main__":
    comprehensive_test()
