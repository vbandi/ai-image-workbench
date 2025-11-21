import tkinter as tk
import time
from ui_app_refactored import ImageGeneratorApp
from PIL import ImageGrab
import os

class AutomatedApp(ImageGeneratorApp):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.automation_step = 0
        # Give some time for UI to settle
        self.root.after(2000, self.run_automation)

    def run_automation(self):
        if self.automation_step == 0:
            print("Step 0: Maximizing and setting prompt")
            try:
                self.root.state('zoomed')
            except:
                # Fallback for non-windows or if zoomed fails
                self.root.attributes('-fullscreen', True)
            
            self.prompt_input.set_text("A majestic mountain landscape at sunset, high quality, 8k")
            self.automation_step += 1
            self.root.after(1000, self.run_automation)
        
        elif self.automation_step == 1:
            print("Step 1: Starting generation")
            self.manual_generate()
            self.automation_step += 1
            self.root.after(2000, self.check_generation_status)

    def check_generation_status(self):
        status = self.status_label.cget("text")
        print(f"Status: {status}")
        
        # Check for success or error
        if ("Ready" in status and "Generated" in status) or "Completed" in status:
             print("Generation complete. Taking screenshot...")
             # Wait a bit for the image to actually render on canvas
             self.root.after(2000, self.take_screenshot)
        elif "Error" in status:
            print("Error detected. Taking screenshot anyway and exiting.")
            self.root.after(1000, self.take_screenshot)
        else:
            # Still generating or just "Ready" (if it hasn't started yet, but manual_generate should have changed it)
            # If it's just "Ready" and we passed step 1, maybe it failed to start?
            # But manual_generate sets it to "Generating..." usually.
            self.root.after(1000, self.check_generation_status)

    def take_screenshot(self):
        try:
            # Force update
            self.root.update()
            self.root.update_idletasks()
            
            # Capture full screen
            screenshot = ImageGrab.grab()
            screenshot.save("app_screenshot.png")
            print("Screenshot saved to app_screenshot.png")
            
            # Verify copy functionality
            print("Testing copy to clipboard...")
            self.copy_image_to_clipboard()
            print("Copy executed successfully.")
        except Exception as e:
            print(f"Failed to take screenshot: {e}")
        finally:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutomatedApp(root)
    root.mainloop()
