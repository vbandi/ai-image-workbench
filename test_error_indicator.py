"""
Test error indicator behavior on model buttons.
"""

import tkinter as tk
from main import ImageGeneratorApp
from PIL import Image


def test_error_indicator():
    print("Testing error indicator...")
    root = tk.Tk()
    app = ImageGeneratorApp(root)

    model = "fal-ai/flux/schnell"
    error_msg = "Test API failure"

    app.model_selection.set_model_generating(model)
    btn_text = app.model_selection.model_buttons[model].cget('text')
    assert btn_text.startswith("⏳ "), f"Expected hourglass prefix, got '{btn_text}'"
    print("✓ Hourglass shown on start")

    app.model_selection.set_model_error(model, error_msg)
    btn_text2 = app.model_selection.model_buttons[model].cget('text')
    assert btn_text2.startswith("❌ "), f"Expected error prefix, got '{btn_text2}'"
    assert model in app.model_selection.models_with_errors
    assert app.model_selection.models_with_errors[model] == error_msg
    container = app.model_selection.model_button_containers[model]
    assert getattr(container, '_tooltip_text', '') == error_msg
    print("✓ Error icon shown with tooltip message")

    app.model_selection.set_model_generating(model)
    btn_text3 = app.model_selection.model_buttons[model].cget('text')
    assert btn_text3.startswith("⏳ "), f"Expected hourglass on retry, got '{btn_text3}'"
    assert model not in app.model_selection.models_with_errors
    assert not getattr(container, '_tooltip_bound', False)
    print("✓ Error cleared when generation restarts")

    img = Image.new('RGB', (10, 10))
    app.model_image_cache[model] = img
    app.model_selection.set_model_generated(model)
    btn_text4 = app.model_selection.model_buttons[model].cget('text')
    assert btn_text4.startswith("✓ "), f"Expected tick on success, got '{btn_text4}'"
    print("✓ Tick shown on success after error")

    app._clear_model_cache()
    btn_text5 = app.model_selection.model_buttons[model].cget('text')
    assert not (btn_text5.startswith("⏳ ") or btn_text5.startswith("✓ ") or btn_text5.startswith("❌ "))
    print("✓ Indicators cleared with cache")

    root.destroy()
    print("All error indicator tests passed! ✓")


if __name__ == "__main__":
    test_error_indicator()
