"""
Test 'viewed' (eye icon) indicator behavior.
"""

import tkinter as tk
from main import ImageGeneratorApp
from PIL import Image
import pytest

def test_viewed_indicator():
    print("Testing viewed indicator...")
    root = tk.Tk()
    app = ImageGeneratorApp(root)

    model = "fal-ai/flux/schnell"

    # 1. Start Generation -> Hourglass
    app.model_selection.set_model_generating(model)
    btn_text = app.model_selection.model_buttons[model].cget('text')
    assert btn_text.startswith("⏳ "), f"Expected hourglass prefix, got '{btn_text}'"
    print("✓ Hourglass shown on start")

    # 2. Finish Generation (Background) -> Tick
    # Simulate generation completion without viewing
    img = Image.new('RGB', (10, 10))
    app.model_image_cache[model] = img
    app.model_selection.set_model_generated(model)
    
    btn_text2 = app.model_selection.model_buttons[model].cget('text')
    assert btn_text2.startswith("✓ "), f"Expected tick prefix, got '{btn_text2}'"
    print("✓ Tick shown on success (not viewed yet)")

    # 3. View Image -> Eye
    # Simulate viewing the image
    app.model_selection.set_model_viewed(model)
    
    btn_text3 = app.model_selection.model_buttons[model].cget('text')
    # Note: The eye icon might be represented by a specific character or string.
    # Based on the plan, we expect an eye icon.
    assert btn_text3.startswith("👁 "), f"Expected eye prefix, got '{btn_text3}'"
    print("✓ Eye shown on viewed")

    # 4. Clear Cache -> Cleared
    app._clear_model_cache()
    btn_text4 = app.model_selection.model_buttons[model].cget('text')
    assert not (btn_text4.startswith("⏳ ") or btn_text4.startswith("✓ ") or btn_text4.startswith("👁 "))
    print("✓ Indicators cleared with cache")

    root.destroy()
    print("All viewed indicator tests passed! ✓")

if __name__ == "__main__":
    try:
        test_viewed_indicator()
    except AttributeError:
        print("AttributeError caught: likely 'set_model_viewed' not implemented yet.")
    except AssertionError as e:
        print(f"Assertion failed: {e}")
