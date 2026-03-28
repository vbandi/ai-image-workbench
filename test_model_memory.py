"""
Test script for model memory feature.
This script tests the model caching and tick functionality.
"""

import tkinter as tk
from PIL import Image
from main import ImageGeneratorApp


def test_model_memory():
    """Test the model memory functionality."""
    print("Testing Model Memory Feature...")
    
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    
    # Test 1: Check initial state
    print("\n1. Testing initial state...")
    assert len(app.model_image_cache) == 0, "Cache should be empty initially"
    assert len(app.model_selection.models_with_ticks) == 0, "No ticks initially"
    print("✓ Initial state is correct")
    
    # Test 2: Simulate image generation
    print("\n2. Testing cache storage after generation...")
    test_model = "fal-ai/flux/schnell"
    test_image = Image.new('RGB', (100, 100), color='red')
    
    app.current_image = test_image
    app.model_image_cache[test_model] = test_image
    app.model_selection.set_model_generated(test_model)
    
    assert test_model in app.model_image_cache, "Model should be in cache"
    assert test_model in app.model_selection.models_with_ticks, "Model should have tick"
    print("✓ Cache and tick storage works")
    
    # Test 3: Check button text update
    print("\n3. Testing button text with tick...")
    btn = app.model_selection.model_buttons[test_model]
    btn_text = btn.cget('text')
    assert "✓" in btn_text, f"Button should have tick mark, got: {btn_text}"
    print(f"✓ Button text updated correctly: {btn_text}")
    
    # Test 4: Test cache clearing
    print("\n4. Testing cache clearing...")
    app._clear_model_cache()
    
    assert len(app.model_image_cache) == 0, "Cache should be empty after clear"
    assert len(app.model_selection.models_with_ticks) == 0, "Ticks should be cleared"
    
    btn_text_after = btn.cget('text')
    assert "✓" not in btn_text_after, f"Button should not have tick after clear, got: {btn_text_after}"
    print("✓ Cache clearing works correctly")
    
    # Test 5: Test multiple model caching
    print("\n5. Testing multiple model caching...")
    models = ["fal-ai/flux/schnell", "fal-ai/flux-pro/v1.1", "fal-ai/hidream-i1-fast"]
    
    for model in models:
        test_img = Image.new('RGB', (100, 100), color='blue')
        app.model_image_cache[model] = test_img
        app.model_selection.set_model_generated(model)
    
    assert len(app.model_image_cache) == 3, "Should have 3 cached images"
    assert len(app.model_selection.models_with_ticks) == 3, "Should have 3 ticks"
    
    for model in models:
        btn = app.model_selection.model_buttons[model]
        assert "✓" in btn.cget('text'), f"Model {model} should have tick"
    
    print("✓ Multiple model caching works")
    
    # Test 6: Clear and verify all ticks removed
    print("\n6. Testing clearing multiple ticks...")
    app._clear_model_cache()
    
    for model in models:
        btn = app.model_selection.model_buttons[model]
        assert "✓" not in btn.cget('text'), f"Model {model} should not have tick after clear"
    
    print("✓ All ticks cleared correctly")
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)
    
    root.destroy()


if __name__ == "__main__":
    test_model_memory()
