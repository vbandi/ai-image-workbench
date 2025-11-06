"""
Demo script showing the model memory feature in action.
This creates mock generations to demonstrate the caching behavior.
"""

import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
from ui_app_refactored import ImageGeneratorApp
import time


def create_colored_image(color, text):
    """Create a test image with a color and text label."""
    img = Image.new('RGB', (512, 512), color=color)
    draw = ImageDraw.Draw(img)
    
    # Add text to identify the image
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default()
    
    # Draw text in center
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    position = ((512 - text_width) // 2, (512 - text_height) // 2)
    draw.text(position, text, fill='white', font=font)
    
    return img


def demo_model_memory():
    """Demonstrate the model memory feature."""
    print("\n" + "="*60)
    print("MODEL MEMORY FEATURE DEMO")
    print("="*60)
    
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    
    # Set a test prompt
    test_prompt = "A beautiful sunset over the ocean"
    app.prompt_input.set_text(test_prompt)
    app.current_prompt = test_prompt
    
    print(f"\nPrompt: '{test_prompt}'")
    print("\n" + "-"*60)
    
    # Simulate generating with multiple models
    models_to_test = [
        ("fal-ai/flux/schnell", "red", "Flux Schnell"),
        ("fal-ai/flux-pro/v1.1", "blue", "Flux Pro"),
        ("fal-ai/hidream-i1-fast", "green", "HiDream Fast")
    ]
    
    print("\nSTEP 1: Generating images with different models...")
    print("-"*60)
    
    for model, color, label in models_to_test:
        print(f"  Generating with {label}...")
        
        # Create mock image
        test_image = create_colored_image(color, label)
        
        # Cache it
        app.current_image = test_image
        app.model_image_cache[model] = test_image
        app.model_selection.set_model_generated(model)
        app.image_display_manager.set_image(test_image)
        
        # Update display
        root.update()
        time.sleep(0.1)
        
        print(f"    ✓ Cached for {label}")
    
    print(f"\n  Cache contains {len(app.model_image_cache)} images")
    print(f"  {len(app.model_selection.models_with_ticks)} models have ticks")
    
    # Show button text with ticks
    print("\n  Model buttons now show:")
    for model, _, label in models_to_test:
        btn = app.model_selection.model_buttons[model]
        print(f"    • {btn.cget('text')}")
    
    print("\n" + "-"*60)
    print("\nSTEP 2: Switching between models (using cache)...")
    print("-"*60)
    
    # Simulate clicking on cached models
    for model, color, label in models_to_test:
        print(f"  Clicking on ✓ {label}...")
        
        # Simulate selecting the model
        if model in app.model_image_cache:
            app.current_image = app.model_image_cache[model]
            app.image_display_manager.set_image(app.current_image)
            root.update()
            time.sleep(0.1)
            print(f"    → Instantly showing {color} image from cache")
    
    print("\n" + "-"*60)
    print("\nSTEP 3: Changing prompt (cache will clear)...")
    print("-"*60)
    
    new_prompt = "A majestic mountain landscape"
    print(f"  New prompt: '{new_prompt}'")
    print("  Triggering generation...")
    
    # Simulate prompt change
    app.prompt_input.set_text(new_prompt)
    app._clear_model_cache()
    
    root.update()
    time.sleep(0.1)
    
    print(f"\n  Cache contains {len(app.model_image_cache)} images")
    print(f"  {len(app.model_selection.models_with_ticks)} models have ticks")
    
    print("\n  Model buttons now show:")
    for model, _, label in models_to_test:
        btn = app.model_selection.model_buttons[model]
        print(f"    • {btn.cget('text')}")
    
    print("\n" + "-"*60)
    print("\nSTEP 4: Generate with new prompt...")
    print("-"*60)
    
    # Generate with one model
    model, color, label = models_to_test[0]
    print(f"  Generating with {label} (new prompt)...")
    
    test_image = create_colored_image("orange", f"{label}\n(New)")
    app.current_image = test_image
    app.model_image_cache[model] = test_image
    app.model_selection.set_model_generated(model)
    
    root.update()
    time.sleep(0.1)
    
    print(f"    ✓ Cached for {label}")
    print(f"\n  Cache contains {len(app.model_image_cache)} images")
    
    btn = app.model_selection.model_buttons[model]
    print(f"  Model button now shows: {btn.cget('text')}")
    
    print("\n" + "="*60)
    print("DEMO COMPLETE!")
    print("="*60)
    print("\nKey takeaways:")
    print("  • Images are cached per model for the current prompt")
    print("  • Tick marks (✓) show which models have generated images")
    print("  • Clicking a ticked model shows cached image instantly")
    print("  • Changing prompt clears all caches and tick marks")
    print("  • New generations start fresh with the new prompt")
    print("\nClose the window to exit...")
    
    root.mainloop()


if __name__ == "__main__":
    demo_model_memory()
