"""
Test generating (hourglass) indicator behavior.
"""

import tkinter as tk
from ui_app_refactored import ImageGeneratorApp
from PIL import Image


def test_hourglass_indicator():
    print("Testing hourglass indicator...")
    root = tk.Tk()
    app = ImageGeneratorApp(root)

    model = "fal-ai/flux/schnell"

    # Simulate starting generation
    app.model_selection.set_model_generating(model)
    btn_text = app.model_selection.model_buttons[model].cget('text')
    assert btn_text.startswith("⏳ "), f"Expected hourglass prefix, got '{btn_text}'"
    print("✓ Hourglass shown on start")

    # Simulate success completion
    img = Image.new('RGB', (10, 10))
    app.model_image_cache[model] = img
    app.model_selection.set_model_generated(model)
    btn_text2 = app.model_selection.model_buttons[model].cget('text')
    assert btn_text2.startswith("✓ "), f"Expected tick prefix, got '{btn_text2}'"
    print("✓ Tick shown on success; hourglass removed")

    # Simulate clearing all
    app._clear_model_cache()
    btn_text3 = app.model_selection.model_buttons[model].cget('text')
    assert not (btn_text3.startswith("⏳ ") or btn_text3.startswith("✓ "))
    print("✓ Indicators cleared with cache")

    root.destroy()
    print("All hourglass tests passed! ✓")


if __name__ == "__main__":
    test_hourglass_indicator()
