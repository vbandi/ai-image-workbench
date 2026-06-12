"""
Image handling module for processing, displaying, and manipulating images.
Handles zoom, pan, resize operations and image display management.
"""

import tkinter as tk
from typing import Optional, Tuple
from PIL import Image, ImageTk
from config import get_theme_color


class ImageProcessor:
    """Handles image processing operations like zoom, pan, and resize."""
    
    def __init__(self):
        """Initialize the image processor."""
        self.zoom_level = 1.0
        self.view_offset_x = 0
        self.view_offset_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        
    def reset_view(self):
        """Reset zoom and pan to default values."""
        self.zoom_level = 1.0
        self.view_offset_x = 0
        self.view_offset_y = 0
        
    def calculate_display_dimensions(self, image: Image.Image, frame_width: int, frame_height: int) -> Tuple[int, int]:
        """
        Calculate the optimal display dimensions for an image within a frame.
        
        Args:
            image: The PIL Image to display
            frame_width: Width of the display frame
            frame_height: Height of the display frame
            
        Returns:
            Tuple of (width, height) for the displayed image
        """
        if not image or frame_width <= 1 or frame_height <= 1:
            return (0, 0)
            
        image_ratio = image.width / image.height
        frame_ratio = frame_width / frame_height
        
        if frame_ratio > image_ratio:
            # Frame is wider than image
            base_height = frame_height
            base_width = int(base_height * image_ratio)
        else:
            # Frame is taller than image
            base_width = frame_width
            base_height = int(base_width / image_ratio)
            
        return (base_width, base_height)
    
    def apply_zoom(self, zoom_factor: float, cursor_x: int = 0, cursor_y: int = 0, 
                   frame_width: int = 0, frame_height: int = 0, image: Optional[Image.Image] = None):
        """
        Apply zoom to the current view.
        
        Args:
            zoom_factor: Factor to multiply current zoom by
            cursor_x: X position of cursor for zoom centering
            cursor_y: Y position of cursor for zoom centering
            frame_width: Width of the display frame
            frame_height: Height of the display frame
            image: The current image being displayed
        """
        new_zoom_level = self.zoom_level * zoom_factor
        new_zoom_level = max(0.1, min(new_zoom_level, 10.0))  # Clamp zoom
        
        if image and frame_width > 1 and frame_height > 1:
            # Calculate new offset to zoom towards cursor
            image_ratio = image.width / image.height
            frame_ratio = frame_width / frame_height
            
            if frame_ratio > image_ratio:
                base_height = frame_height
                base_width = int(base_height * image_ratio)
            else:
                base_width = frame_width
                base_height = int(base_width / image_ratio)
            
            # Position of cursor relative to the center of the frame
            cursor_relative_x = cursor_x - frame_width / 2
            cursor_relative_y = cursor_y - frame_height / 2
            
            # How much the pan offset should change
            dx = cursor_relative_x * (zoom_factor - 1)
            dy = cursor_relative_y * (zoom_factor - 1)
            
            self.view_offset_x += int(dx)
            self.view_offset_y += int(dy)
            
        self.zoom_level = new_zoom_level
    
    def start_pan(self, x: int, y: int):
        """Start a pan operation."""
        self.pan_start_x = x
        self.pan_start_y = y
    
    def continue_pan(self, x: int, y: int):
        """Continue a pan operation."""
        dx = x - self.pan_start_x
        dy = y - self.pan_start_y
        
        self.view_offset_x -= dx
        self.view_offset_y -= dy
        
        self.pan_start_x = x
        self.pan_start_y = y
    
    def get_zoom_level(self) -> float:
        """Get the current zoom level."""
        return self.zoom_level
    
    def get_view_offset(self) -> Tuple[int, int]:
        """Get the current view offset."""
        return (self.view_offset_x, self.view_offset_y)


class ImageDisplayManager:
    """Manages image display operations and updates."""
    
    def __init__(self, update_callback=None):
        """Initialize the image display manager."""
        self.current_image: Optional[Image.Image] = None
        self.update_callback = update_callback
        self.processor = ImageProcessor()
        
    def set_image(self, image: Image.Image):
        """Set the current image to display."""
        self.current_image = image
        self.processor.reset_view()
        
    def get_current_image(self) -> Optional[Image.Image]:
        """Get the current image."""
        return self.current_image
    
    def create_display_image(self, frame_width: int, frame_height: int) -> Optional[ImageTk.PhotoImage]:
        """
        Create a display-ready image for the given frame dimensions.
        
        Args:
            frame_width: Width of the display frame
            frame_height: Height of the display frame
            
        Returns:
            PhotoImage ready for display, or None if no image available
        """
        if not self.current_image or frame_width <= 1 or frame_height <= 1:
            return None
        
        # Calculate base dimensions
        base_width, base_height = self.processor.calculate_display_dimensions(
            self.current_image, frame_width, frame_height
        )
        
        if base_width < 1 or base_height < 1:
            return None
        
        # Apply zoom
        zoom_level = self.processor.get_zoom_level()
        zoomed_width = int(base_width * zoom_level)
        zoomed_height = int(base_height * zoom_level)
        
        if zoomed_width < 1 or zoomed_height < 1:
            return None
        
        # Resize the image
        resized_image = self.current_image.resize((zoomed_width, zoomed_height), Image.Resampling.BICUBIC)
        
        # Create final image with pan offset
        final_image = Image.new('RGB', (frame_width, frame_height))
        offset_x, offset_y = self.processor.get_view_offset()
        paste_x = (frame_width - zoomed_width) // 2 - offset_x
        paste_y = (frame_height - zoomed_height) // 2 - offset_y
        final_image.paste(resized_image, (paste_x, paste_y))
        
        return ImageTk.PhotoImage(final_image)
    
    def handle_zoom(self, event, frame_width: int, frame_height: int):
        """Handle zoom events."""
        if not self.current_image:
            return
            
        # Determine zoom direction
        if event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):  # Zoom out
            zoom_factor = 0.9
        else:  # Zoom in
            zoom_factor = 1.1
        
        cursor_x = getattr(event, 'x', 0)
        cursor_y = getattr(event, 'y', 0)
        
        self.processor.apply_zoom(
            zoom_factor, cursor_x, cursor_y, 
            frame_width, frame_height, self.current_image
        )
        
        if self.update_callback:
            self.update_callback()
    
    def handle_pan_start(self, event):
        """Handle the start of a pan operation."""
        self.processor.start_pan(event.x, event.y)
    
    def handle_pan_continue(self, event):
        """Handle continuation of a pan operation."""
        if not self.current_image:
            return
            
        self.processor.continue_pan(event.x, event.y)
        
        if self.update_callback:
            self.update_callback()
    
    def reset_view(self):
        """Reset zoom and pan to default."""
        self.processor.reset_view()
        if self.update_callback:
            self.update_callback()


class TooltipManager:
    """Manages tooltip functionality for UI elements."""

    def __init__(self):
        """Initialize the tooltip manager."""
        self.active_tooltips = {}

    def add_tooltip(self, widget, text: str):
        """Add a tooltip to a widget."""
        self.set_tooltip_region([widget], text)

    def set_tooltip(self, widget, text: str):
        """Set or update tooltip text for a single widget."""
        self.set_tooltip_region([widget], text)

    def set_tooltip_region(self, widgets, text: str):
        """Set tooltip for one or more widgets treated as a single hover region."""
        if not widgets:
            return

        anchor = widgets[0]
        anchor._tooltip_text = text
        anchor._tooltip_widgets = widgets

        if getattr(anchor, '_tooltip_bound', False):
            return

        anchor._tooltip_bound = True
        hover_count = [0]
        pending_hide = [None]

        def cancel_pending_hide():
            if pending_hide[0] is not None:
                anchor.after_cancel(pending_hide[0])
                pending_hide[0] = None

        def destroy_tooltip():
            if hasattr(anchor, 'tooltip'):
                anchor.tooltip.destroy()
                del anchor.tooltip

        def show_tooltip():
            tooltip_text = getattr(anchor, '_tooltip_text', '')
            if not tooltip_text:
                return

            destroy_tooltip()
            anchor.update_idletasks()

            x = anchor.winfo_rootx() + 10
            y = anchor.winfo_rooty() + anchor.winfo_height() + 5

            tooltip = tk.Toplevel(anchor)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")

            label = tk.Label(
                tooltip,
                text=tooltip_text,
                background=get_theme_color('tooltip_bg'),
                foreground=get_theme_color('tooltip_text'),
                relief='solid',
                borderwidth=1,
                wraplength=360,
                justify='left',
            )
            label.pack()

            anchor.tooltip = tooltip

        def try_hide():
            pending_hide[0] = None
            if hover_count[0] <= 0:
                destroy_tooltip()

        def on_enter(_event):
            hover_count[0] += 1
            cancel_pending_hide()
            show_tooltip()

        def on_leave(_event):
            hover_count[0] = max(0, hover_count[0] - 1)
            cancel_pending_hide()
            pending_hide[0] = anchor.after(100, try_hide)

        for widget in widgets:
            widget.bind('<Enter>', on_enter, add='+')
            widget.bind('<Leave>', on_leave, add='+')

    def clear_tooltip_region(self, widgets):
        """Remove tooltip bindings from a hover region."""
        if not widgets:
            return

        anchor = widgets[0]
        if hasattr(anchor, 'tooltip'):
            anchor.tooltip.destroy()
            del anchor.tooltip

        bound_widgets = getattr(anchor, '_tooltip_widgets', widgets)
        for widget in bound_widgets:
            widget.unbind('<Enter>')
            widget.unbind('<Leave>')

        anchor._tooltip_bound = False
        if hasattr(anchor, '_tooltip_text'):
            del anchor._tooltip_text
        if hasattr(anchor, '_tooltip_widgets'):
            del anchor._tooltip_widgets

    def remove_tooltip(self, widget):
        """Remove tooltip from a widget."""
        self.clear_tooltip_region([widget])