#!/usr/bin/env python3
"""
Test script to demonstrate the new moveable separator functionality
in the AI Image Workbench application.

This script creates a simple demonstration showing how the moveable
separator between the model selection area and prompt input area works.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ImageGeneratorApp


def main():
    """Run AI Image Workbench with the new moveable separator feature."""
    print("Starting AI Image Workbench with moveable separator...")
    print("Features:")
    print("1. Moveable separator between model selection (top) and prompt input (bottom)")
    print("2. Drag the horizontal separator line to resize the areas")
    print("3. Default layout: model area ~400px, prompt area at minimum size needed")
    print("4. Visual separator styling (thicker, raised relief) for better visibility")
    print()
    
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    
    # The application is now running with:
    # - Vertical PanedWindow (sidebar_splitter) separating model selection and prompt areas
    # - Moveable sash that can be dragged to resize the areas
    # - Visual styling on the separator for better visibility
    
    print("Application started. Close the window to exit.")
    root.mainloop()


if __name__ == "__main__":
    main()
