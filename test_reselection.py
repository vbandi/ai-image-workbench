"""
Test script for model reselection behavior.
Verifies that clicking on an already-selected model triggers regeneration.
"""

import tkinter as tk
from PIL import Image
from main import ImageGeneratorApp


def test_reselection():
    """Test that reselecting a model triggers regeneration."""
    print("Testing Model Reselection Behavior...")
    
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    
    # Set a test prompt
    test_prompt = "A beautiful landscape"
    app.prompt_input.set_text(test_prompt)
    app.current_prompt = test_prompt
    
    test_model = "fal-ai/flux/schnell"
    
    # Test 1: Initial selection
    print("\n1. Testing initial model selection...")
    
    # Create and cache an image
    test_image_1 = Image.new('RGB', (100, 100), color='red')
    app.current_image = test_image_1
    app.model_image_cache[test_model] = test_image_1
    app.model_selection.set_model_generated(test_model)
    app.model_selection.model_var.set(test_model)
    
    assert test_model in app.model_image_cache, "Model should be in cache"
    print("✓ Model selected and image cached")
    
    # Test 2: Select another model with cache
    print("\n2. Testing switching to different model with cache...")
    
    test_model_2 = "fal-ai/flux-pro/v1.1"
    test_image_2 = Image.new('RGB', (100, 100), color='blue')
    app.model_image_cache[test_model_2] = test_image_2
    app.model_selection.set_model_generated(test_model_2)
    
    # Mock the selection without triggering actual generation
    generation_triggered = []
    original_manual_generate = app.manual_generate
    
    def mock_manual_generate():
        generation_triggered.append(True)
        # Don't actually generate
    
    app.manual_generate = mock_manual_generate
    
    # Select the second model (should show cached image, no regeneration)
    app._on_model_select(test_model_2, is_reselection=False)
    
    assert len(generation_triggered) == 0, "Should not regenerate when switching to different model with cache"
    assert app.current_image == test_image_2, "Should show cached image"
    print("✓ Switching to different model shows cached image (no regeneration)")
    
    # Test 3: Reselect the same model (should regenerate)
    print("\n3. Testing reselection of current model...")
    
    generation_triggered.clear()
    
    # Reselect the currently selected model
    app._on_model_select(test_model_2, is_reselection=True)
    
    assert len(generation_triggered) == 1, "Should regenerate when reselecting current model"
    print("✓ Reselecting current model triggers regeneration")
    
    # Test 4: Test via select_model method (full flow)
    print("\n4. Testing full reselection flow via select_model...")
    
    generation_triggered.clear()
    
    # Set current model
    app.model_selection.model_var.set(test_model)
    
    # Call select_model with the same model (simulates button click)
    app.model_selection.select_model(test_model)
    
    assert len(generation_triggered) == 1, "Should regenerate when clicking on selected model button"
    print("✓ Clicking on selected model button triggers regeneration")
    
    # Restore original method
    app.manual_generate = original_manual_generate
    
    print("\n" + "="*50)
    print("All reselection tests passed! ✓")
    print("="*50)
    
    print("\nBehavior Summary:")
    print("  • Clicking different model with cache → Shows cached image")
    print("  • Clicking different model without cache → Generates")
    print("  • Clicking same model (reselection) → Always regenerates")
    
    root.destroy()


if __name__ == "__main__":
    test_reselection()
