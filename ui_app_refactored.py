"""
Refactored Image Generator Application
A modular version using separate components for different functionalities.
"""

import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
from typing import Optional, Dict, Any
import time
import threading
import queue
import logging
import os
import sys

from PIL import Image, ImageTk
from ai_api import enhance_prompt
from image_gen_api import generate_image, MODELS
from config import (
    DEFAULT_MODEL, AUTO_GENERATE_MODELS, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
    SPINNER_FRAMES, UPDATE_THREAD_INTERVAL, DISPLAY_QUEUE_CHECK_INTERVAL,
    ACCENT_COLOR, BACKGROUND_COLOR, TEXT_COLOR, DEBOUNCE_DELAY_MS, StatusMessages
)
from ui_components import ModelSelectionFrame, PromptInputFrame
from image_handler import ImageDisplayManager, TooltipManager
from clipboard_manager import ClipboardManager
from threading_utils import GenerationQueueManager, UpdateThreadManager, SpinnerAnimator


def _configure_logger() -> logging.Logger:
    """Configure a module-level logger with optional debug output."""
    logger = logging.getLogger("image_generator.app")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    debug_enabled = os.environ.get("IMAGE_GEN_DEBUG", "0") not in ("0", "", "false", "False")
    logger.setLevel(logging.DEBUG if debug_enabled else logging.INFO)
    return logger


LOGGER = _configure_logger()


def set_debug_logging(enabled: bool):
    """Toggle debug logging at runtime."""
    level = logging.DEBUG if enabled else logging.INFO
    for name in ("image_generator.app", "image_generator.api"):
        logging.getLogger(name).setLevel(level)
    LOGGER.debug("Debug logging %s", "enabled" if enabled else "disabled")


class ImageGeneratorApp:
    """Main application class for the Image Generator."""
    
    def __init__(self, root):
        """Initialize the image generator application."""
        self.root = root
        self.root.title("Image Generator")
        
        # Set minimum window size
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Initialize managers and components
        self.generation_queue = GenerationQueueManager()
        self.update_thread_manager = UpdateThreadManager()
        self.clipboard_manager = ClipboardManager()
        self.tooltip_manager = TooltipManager()
        self.spinner_animator = SpinnerAnimator(SPINNER_FRAMES)
        self._single_generation_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        
        # Current image and state
        self.current_image: Optional[Image.Image] = None
        # Keep a reference to the current Tk photo image to prevent GC
        self._current_photo = None
        
        # Model memory cache: stores generated images per model
        self.model_image_cache: Dict[str, Image.Image] = {}
        self.current_prompt: str = ""
        
        # Track models in queue for overlay display
        self.queued_models: list = []  # Models in generation queue (ordered)
        self.models_with_errors: Dict[str, str] = {}  # model -> error message
        
        # Debounce timer for auto-generation
        self.debounce_timer: Optional[str] = None
        self.debounce_delay = DEBOUNCE_DELAY_MS
        
        # Create UI components
        self._create_main_frame()
        self._create_model_selection()
        self._create_prompt_input()
        self._create_image_display()
        self._create_status_bar()
        

        # Configure custom styles
        self._configure_styles()
        
        # Set up threading and callbacks
        self._setup_callbacks()
        self._start_background_threads()
        
        # Bind keyboard shortcuts
        self._bind_shortcuts()
        
        # Configure inner splitter styling to make separator more visible
        self._configure_inner_splitter_styling()
    
    def _create_main_frame(self):
        """Create the main application frame."""
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)


        # Splitter allows drag-to-resize between controls and image area
        self.main_splitter = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.main_splitter.grid(row=0, column=0, sticky="nsew")

        # Left pane hosts controls with internal splitter for model/prompt separation
        self.control_frame = ttk.Frame(self.main_splitter, padding=(0, 8, 8, 8))
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_rowconfigure(0, weight=1)

        # Internal splitter for model selection and prompt areas
        self.sidebar_splitter = ttk.PanedWindow(self.control_frame, orient=tk.VERTICAL)
        self.sidebar_splitter.grid(row=0, column=0, sticky="nsew")

        # Model selection frame (top pane)
        self.model_frame = ttk.Frame(self.sidebar_splitter, padding=(0, 0, 0, 0))
        self.model_frame.grid_columnconfigure(0, weight=1)
        self.model_frame.grid_rowconfigure(0, weight=1)


        # Prompt frame (bottom pane)
        self.prompt_frame = ttk.Frame(self.sidebar_splitter, padding=(0, 0, 0, 0))
        self.prompt_frame.grid_columnconfigure(0, weight=1)
        self.prompt_frame.grid_rowconfigure(0, weight=1)  # Allow prompt to expand

        # Right pane hosts the image display
        self.content_frame = ttk.Frame(self.main_splitter, padding=(8, 8, 0, 8))
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)



        # Add panes with weights so areas can be resized
        self.sidebar_splitter.add(self.model_frame, weight=3)  # Model selection default priority
        self.sidebar_splitter.add(self.prompt_frame, weight=2)  # Prompt area can expand/shrink
        self.main_splitter.add(self.control_frame, weight=0)
        self.main_splitter.add(self.content_frame, weight=1)
        self.root.after(0, lambda: self.main_splitter.sashpos(0, 350)) # Slightly wider sidebar
        self.root.after(0, lambda: self.sidebar_splitter.sashpos(0, 400)) # Default model area height
    

    def _create_model_selection(self):
        """Create the model selection component."""
        self.model_selection = ModelSelectionFrame(
            self.model_frame,
            self._on_model_select,
            DEFAULT_MODEL
        )
    

    def _create_prompt_input(self):
        """Create the prompt input component."""
        self.prompt_input = PromptInputFrame(
            self.prompt_frame,
            self._on_key_release,
            self._on_enter,
            self.enhance_prompt,
            self.enhance_prompt_with_directions,
            self.manual_generate,
            self.parallel_generate,
            self.parallel_generate_from_clipboard,
            self.save_image,
            self.copy_image_to_clipboard,
            self._on_auto_generate_change
        )
        
    def _create_image_display(self):
        """Create the image display area."""
        # Create frame for image to enable proper centering and expansion
        self.image_frame = ttk.Frame(self.content_frame)
        self.image_frame.grid(row=0, column=0, sticky="nsew")
        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1)
        
        # Create label for image display
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.grid(row=0, column=0, sticky="nsew")
        
        # Create queue overlay frame (top-right corner)
        self._create_queue_overlay()
        
        # Initialize image display manager
        self.image_display_manager = ImageDisplayManager(self._schedule_image_update)
        
        # Bind mouse events for zoom and pan
        self.image_label.bind("<MouseWheel>", self._on_mouse_wheel)
        self.image_label.bind("<Button-4>", self._on_mouse_wheel)    # Linux scroll up
        self.image_label.bind("<Button-5>", self._on_mouse_wheel)    # Linux scroll down
        self.image_label.bind("<ButtonPress-1>", self._on_pan_start)
        self.image_label.bind("<B1-Motion>", self._on_pan_motion)
    
    def _create_queue_overlay(self):
        """Create the overlay frame for showing queued model generations."""
        # Use a tk.Frame for the overlay to allow custom styling
        self.queue_overlay_frame = tk.Frame(
            self.image_frame,
            background='#ffffff',
            padx=8,
            pady=6,
            highlightbackground='#e0e0e0',
            highlightthickness=1
        )
        # Initially hidden
        self.queue_overlay_visible = False
        self.queue_model_labels: Dict[str, tk.Label] = {}
    
    def _update_queue_overlay(self):
        """Update the queue overlay with current model states."""
        # Import here to avoid circular import issues
        from config import MODEL_ABBREVIATIONS
        
        # Only show overlay if there are multiple models queued (parallel generation)
        # For single model generation, the overlay is not needed
        if len(self.queued_models) <= 1:
            if self.queue_overlay_visible:
                self.queue_overlay_frame.place_forget()
                self.queue_overlay_visible = False
            return
        
        # Clear existing labels
        for widget in self.queue_overlay_frame.winfo_children():
            widget.destroy()
        self.queue_model_labels.clear()
        
        # Create title label
        title_label = tk.Label(
            self.queue_overlay_frame,
            text="Generation Queue",
            font=('Segoe UI', 9, 'bold'),
            background='#ffffff',
            foreground='#333333'
        )
        title_label.pack(anchor='w', pady=(0, 4))
        
        # Create label for each queued model
        for model in self.queued_models:
            # Get display name
            display_name = model.replace("fal-ai/", "").replace("/", " ").title()
            display_name = MODEL_ABBREVIATIONS.get(display_name, display_name)
            
            # Determine icon based on state
            if model in self.models_with_errors:
                icon = "❌"
                fg_color = '#dc3545'  # Red for error
            elif model in self.model_image_cache:
                icon = "✓"
                fg_color = '#28a745'  # Green for completed
            else:
                icon = "⏳"
                fg_color = '#666666'  # Gray for pending
            
            label_text = f"{icon} {display_name}"
            
            # Create clickable label
            model_label = tk.Label(
                self.queue_overlay_frame,
                text=label_text,
                font=('Segoe UI', 9),
                background='#ffffff',
                foreground=fg_color,
                cursor='hand2' if model in self.model_image_cache else 'arrow'
            )
            model_label.pack(anchor='w', pady=1)
            
            # Add tooltip for error messages
            if model in self.models_with_errors:
                self.tooltip_manager.add_tooltip(model_label, f"Error: {self.models_with_errors[model]}")
            
            # Bind click handler if image is available
            if model in self.model_image_cache:
                model_label.bind('<Button-1>', lambda e, m=model: self._on_queue_model_click(m))
                # Add hover effect
                model_label.bind('<Enter>', lambda e, lbl=model_label: lbl.configure(background='#f0f0f0'))
                model_label.bind('<Leave>', lambda e, lbl=model_label: lbl.configure(background='#ffffff'))
            
            self.queue_model_labels[model] = model_label
        
        # Position the overlay in the top-right corner of the image frame
        if not self.queue_overlay_visible:
            self.queue_overlay_frame.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)
            self.queue_overlay_visible = True
        
        # Raise overlay to ensure it's on top
        self.queue_overlay_frame.lift()
    
    def _on_queue_model_click(self, model: str):
        """Handle click on a model in the queue overlay."""
        if model in self.model_image_cache:
            # Switch to this model and display its cached image
            self.model_selection.set_selected_model(model, notify=False)
            self.current_image = self.model_image_cache[model]
            self.image_display_manager.processor.reset_view()
            self.image_display_manager.set_image(self.current_image)
            self._update_image_display()
            self.model_selection.set_model_viewed(model)
            self.status_label.config(text=StatusMessages.READY_CACHED)
    
    def _create_status_bar(self):
        """Create the status bar."""
        # Create footer frame
        self.footer_frame = ttk.Frame(self.main_frame, style='Footer.TFrame')
        self.footer_frame.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        self.footer_frame.grid_columnconfigure(0, weight=1)
        
        # Create status label
        self.status_label = ttk.Label(self.footer_frame, text="Ready", style='Footer.TLabel')
        self.status_label.grid(row=0, column=0, padx=12, pady=6, sticky="w")
    
    def _configure_styles(self):
        """Configure application styles."""
        style = ttk.Style()
        
        # Use a modern theme (clam) for a consistent look across platforms
        try:
            style.theme_use('clam')
        except Exception:
            pass
        
        # Set base font for all ttk widgets
        style.configure('.', font=('Segoe UI', 10))
        
        # Set default background for frames and labels
        style.configure('TFrame', background=BACKGROUND_COLOR)
        style.configure('TLabel', background=BACKGROUND_COLOR, foreground=TEXT_COLOR)
        
        # Footer style
        style.configure('Footer.TFrame', background='#e4e6eb')
        style.configure('Footer.TLabel', background='#e4e6eb', foreground='#65676b')
    
    def _setup_callbacks(self):
        """Set up callbacks for threading managers."""
        self.update_thread_manager.set_create_photo_callback(self._create_photo_image)
    
    def _start_background_threads(self):
        """Start background update threads."""
        self.update_thread_manager.start_update_thread()
        self.check_display_queue()
    

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.root.bind('<Configure>', self._on_window_resize)
        self.root.bind_all('<Control-c>', self._on_copy_shortcut)
        self.root.bind_all('<Control-C>', self._on_copy_shortcut)
        
        # Bind splitter motion events to resize image when splitter is moved
        self.main_splitter.bind('<ButtonRelease-1>', self._on_splitter_move)
        # Also bind to the virtual event for pane size changes
        self.main_splitter.bind('<<PanedWindowPaneSelected>>', self._on_splitter_move)
        # Bind to Configure events on the content frame to resize when splitter moves
        self.content_frame.bind('<Configure>', self._on_content_frame_resize)
        # Bind inner splitter movement to handle prompt area resizing
        self.sidebar_splitter.bind('<ButtonRelease-1>', self._on_inner_splitter_move)
        self.sidebar_splitter.bind('<Configure>', self._on_inner_splitter_configure)
    
    def _on_model_select(self, model: str, is_reselection: bool = False):
        """Handle model selection change."""
        # Update auto-generate settings based on model
        if model in AUTO_GENERATE_MODELS:
            self.prompt_input.set_auto_generate_enabled(True)
        else:
            self.prompt_input.set_auto_generate_enabled(False)
        
        # If clicking on already-selected model, always regenerate
        if is_reselection:
            current_prompt = self.prompt_input.get_text()
            if current_prompt:
                self.manual_generate()
            return
        
        # Check if this model has a cached image for the current prompt
        if model in self.model_image_cache:
            # Show the cached image immediately
            self.current_image = self.model_image_cache[model]
            self.image_display_manager.processor.reset_view()
            self.image_display_manager.set_image(self.current_image)
            self._update_image_display()
            self.model_selection.set_model_viewed(model)
            self.status_label.config(text=StatusMessages.READY_CACHED)
        else:
            # Generate with the new model immediately
            current_prompt = self.prompt_input.get_text()
            if current_prompt:
                self._start_generation(current_prompt)
    
    def _on_auto_generate_change(self, enabled: bool):
        """Handle auto-generate toggle."""
        # Logic for auto-generate toggle if needed
        pass

    def _on_key_release(self, event):
        """Handle key release events for auto-generation."""
        if not self.prompt_input.is_auto_generate_enabled() or event.keysym == 'Return':
            return
        
        # Use after_idle to ensure the text widget has fully updated before reading
        self.root.after_idle(self._process_key_release)
    
    def _process_key_release(self):
        """Process the key release after the text widget has updated."""
        # Cancel any pending debounce timer
        if self.debounce_timer:
            self.root.after_cancel(self.debounce_timer)
            self.debounce_timer = None
        
        # Set a new debounce timer
        self.debounce_timer = self.root.after(self.debounce_delay, self._execute_generation)
    
    def _execute_generation(self):
        """Execute generation with the current prompt."""
        self.debounce_timer = None
        current_prompt = self.prompt_input.get_text()
        if len(current_prompt) > 0:
            # Check if prompt has changed - if so, clear cache
            if current_prompt != self.current_prompt:
                self._clear_model_cache()
                self.current_prompt = current_prompt
            
            if self.generation_queue.is_currently_generating():
                # If currently generating, update the queue with the latest prompt
                self.generation_queue.queue_prompt(current_prompt)
            else:
                # If not generating, start generation
                self._start_generation(current_prompt)
    
    def _on_enter(self, event):
        """Handle Enter key press."""
        if not self.prompt_input.is_auto_generate_enabled():
            current_prompt = self.prompt_input.get_text()
            if len(current_prompt) > 0:
                # Check if prompt has changed - if so, clear cache
                if current_prompt != self.current_prompt:
                    self._clear_model_cache()
                    self.current_prompt = current_prompt
                
                if self.generation_queue.is_currently_generating():
                    self.generation_queue.queue_prompt(current_prompt)
                else:
                    self._start_generation(current_prompt)
        return 'break'  # Prevents the default behavior of adding a newline
    
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel events for zooming."""
        self.image_display_manager.handle_zoom(event, self.image_frame.winfo_width(), self.image_frame.winfo_height())
    
    def _on_pan_start(self, event):
        """Handle the start of pan operations."""
        self.image_display_manager.handle_pan_start(event)
    
    def _on_pan_motion(self, event):
        """Handle pan motion events."""
        self.image_display_manager.handle_pan_continue(event)
    
    def _on_window_resize(self, event):
        """Handle window resize events."""
        if event.widget == self.root:
            self._schedule_image_update()
    

    def _on_content_frame_resize(self, event):
        """Handle content frame resize events (triggered by splitter movement)."""
        if event.widget == self.content_frame:
            self._schedule_image_update()

    def _on_inner_splitter_move(self, event):
        """Handle inner splitter movement to resize model/prompt areas."""
        if event.widget == self.sidebar_splitter:
            # Update the image display when the splitter moves
            self._schedule_image_update()

    def _on_inner_splitter_configure(self, event):
        """Handle inner splitter configuration changes."""
        if event.widget == self.sidebar_splitter:
            # Schedule image update when splitter configuration changes
            self._schedule_image_update()

    def _configure_inner_splitter_styling(self):
        """Configure styling for the inner splitter to make the separator more visible."""
        # Configure the sash styling for better visibility
        style = ttk.Style()
        
        # Create a more visible sash style
        style.configure('Vertical.TPanedwindow.Sash',
                       sashthickness=8,  # Thicker sash for better grip
                       background='#cccccc',  # Light gray background
                       sashrelief='raised')  # Raised relief to make it stand out
        
        # Apply the style to the inner splitter
        try:
            self.sidebar_splitter.configure(style='Vertical.TPanedwindow')
        except Exception:
            # Fallback if the style doesn't apply
            pass
    
    def _on_splitter_move(self, event):
        """Handle splitter movement events."""
        # Check if the event is from the splitter handle
        if event.widget == self.main_splitter:
            # Check if the click was on a sash using the identify method
            try:
                # identify returns a list with [index, type] if on a sash or handle
                result = event.widget.identify(event.x, event.y)
                if result:  # Non-empty result means we clicked on a sash or handle
                    self._schedule_image_update()
            except Exception:
                # If identify fails, just update anyway
                self._schedule_image_update()
    
    def _on_copy_shortcut(self, event):
        """Handle copy keyboard shortcut."""
        # If focus is in a text/entry-like widget, let it handle Ctrl+C
        focused = self.root.focus_get()
        try:
            widget_class = focused.winfo_class() if focused else ''
        except Exception:
            widget_class = ''
        
        if isinstance(focused, (tk.Text, tk.Entry)) or widget_class in ('Text', 'Entry', 'TEntry', 'TCombobox'):
            return  # allow default copy behavior
        
        self.copy_image_to_clipboard()
        return 'break'
    
    def enhance_prompt(self, directions: Optional[str] = None):
        """Enhance the prompt using AI API."""
        current_prompt = self.prompt_input.get_text()
        if not current_prompt:
            self.status_label.config(text=StatusMessages.ENTER_PROMPT_TO_ENHANCE)
            return
        
        try:
            self.status_label.config(text=StatusMessages.ENHANCING)
            enhanced_prompt = enhance_prompt(current_prompt, directions=directions)
            
            # Clear cache since prompt is changing
            self._clear_model_cache()
            
            self.prompt_input.set_text(enhanced_prompt)
            self.current_prompt = enhanced_prompt
            self.status_label.config(text=StatusMessages.ENHANCED)
            
            # Auto-generate if enabled in prompt input
            if self.prompt_input.should_autogenerate_after_enhance():
                self.manual_generate()
                
        except Exception as e:
            self.status_label.config(text=f"Error enhancing prompt: {e}")
    
    def enhance_prompt_with_directions(self):
        """Ask for directions and then enhance the prompt."""
        directions = simpledialog.askstring(
            "Enhancement Directions", 
            "Enter directions for the enhancement:", 
            parent=self.root
        )
        if directions:
            self.enhance_prompt(directions=directions)
    
    def manual_generate(self):
        """Generate image when Generate button is clicked."""
        current_prompt = self.prompt_input.get_text()
        if len(current_prompt) > 0:
            # Check if prompt has changed - if so, clear cache
            if current_prompt != self.current_prompt:
                self._clear_model_cache()
                self.current_prompt = current_prompt
            
            if self.generation_queue.is_currently_generating():
                self.generation_queue.queue_prompt(current_prompt)
            else:
                self._start_generation(current_prompt)
    
    def parallel_generate(self):
        """Generate images in parallel for all starred models."""
        current_prompt = self.prompt_input.get_text()
        if len(current_prompt) == 0:
            self.status_label.config(text=StatusMessages.ENTER_PROMPT)
            return
        
        # Get starred models
        starred_models = self.model_selection.get_starred_models()
        if not starred_models:
            self.status_label.config(text=StatusMessages.STAR_MODEL_FIRST)
            return

        if self.generation_queue.is_currently_generating():
            self.status_label.config(text=StatusMessages.WAIT_FOR_GENERATION)
            return
        if self.generation_queue.is_parallel_active():
            self.status_label.config(text=StatusMessages.PARALLEL_IN_PROGRESS)
            return
        
        # Check if prompt has changed - if so, clear cache
        if current_prompt != self.current_prompt:
            self._clear_model_cache()
            self.current_prompt = current_prompt
        
        # Start parallel generation
        started = self.generation_queue.start_parallel_generation(
            starred_models,
            current_prompt,
            self._generate_image_for_model
        )
        if not started:
            self.status_label.config(text=StatusMessages.PARALLEL_UNABLE)
            return
        
        # Reset generating indicators then mark starred models as in-progress
        self.model_selection.clear_all_generating()
        # Clear previous queue and track new queued models for overlay display
        self.queued_models.clear()
        self.models_with_errors.clear()
        self.queued_models = starred_models.copy()
        self._update_queue_overlay()
        # Set all starred models as generating
        for model in starred_models:
            self.model_selection.set_model_generating(model)
        
        self.status_label.config(text=f"Generating images for {len(starred_models)} models...")
    
    def parallel_generate_from_clipboard(self):
        """Generate images in parallel for all starred models using prompt from clipboard."""
        # Try to get text from clipboard
        try:
            clipboard_text = self.root.clipboard_get()
        except tk.TclError:
            self.status_label.config(text="No text in clipboard")
            return
        
        if not clipboard_text or not clipboard_text.strip():
            self.status_label.config(text="Clipboard is empty")
            return
        
        # Set the prompt from clipboard
        clipboard_prompt = clipboard_text.strip()
        self.prompt_input.set_text(clipboard_prompt)
        
        # Get starred models
        starred_models = self.model_selection.get_starred_models()
        if not starred_models:
            self.status_label.config(text=StatusMessages.STAR_MODEL_FIRST)
            return

        if self.generation_queue.is_currently_generating():
            self.status_label.config(text=StatusMessages.WAIT_FOR_GENERATION)
            return
        if self.generation_queue.is_parallel_active():
            self.status_label.config(text=StatusMessages.PARALLEL_IN_PROGRESS)
            return
        
        # Clear cache since we have a new prompt
        self._clear_model_cache()
        self.current_prompt = clipboard_prompt
        
        # Start parallel generation
        started = self.generation_queue.start_parallel_generation(
            starred_models,
            clipboard_prompt,
            self._generate_image_for_model
        )
        if not started:
            self.status_label.config(text=StatusMessages.PARALLEL_UNABLE)
            return
        
        # Reset generating indicators then mark starred models as in-progress
        self.model_selection.clear_all_generating()
        # Clear previous queue and track new queued models for overlay display
        self.queued_models.clear()
        self.models_with_errors.clear()
        self.queued_models = starred_models.copy()
        self._update_queue_overlay()
        # Set all starred models as generating
        for model in starred_models:
            self.model_selection.set_model_generating(model)
        
        self.status_label.config(text=f"Generating from clipboard for {len(starred_models)} models...")
    
    def _generate_image_for_model(self, model: str, prompt: str):
        """Generate an image for a specific model (used in parallel generation)."""
        try:
            # Use the image generation API
            image = generate_image(model, prompt)
            return image
        except Exception as e:
            raise RuntimeError(str(e)) from e
    
    def _start_generation(self, prompt: str):
        """Start the image generation process."""
        try:
            selected_model = self.model_selection.get_selected_model()
        except Exception as exc:
            self.status_label.config(text=f"Error selecting model: {exc}")
            return

        # Mark the selected model as generating (show hourglass)
        try:
            self.model_selection.set_model_generating(selected_model)
            # Clear previous queue and start fresh for new generation
            if not self.generation_queue.is_parallel_active():
                self.queued_models.clear()
                self.models_with_errors.clear()
                self.queued_models.append(selected_model)
                self._update_queue_overlay()
            # Update status from the main thread to avoid cross-thread UI calls
            self.status_label.config(text=StatusMessages.GENERATING)
            LOGGER.debug("Starting generation for model=%s prompt_len=%d", selected_model, len(prompt))
        except Exception:
            # Non-fatal: if UI update fails, continue generation
            pass

        self.generation_queue.start_generation_thread(
            self._generate_image,
            (prompt, selected_model)
        )
    
    def _generate_image(self, prompt: str, model: str):
        """Generate an image in a background thread."""
        start_time = time.time()
        try:
            LOGGER.debug("Background thread running generate_image for model=%s", model)
            image = generate_image(model, prompt)
            LOGGER.debug("Background thread completed generate_image for model=%s", model)
            generation_time = time.time() - start_time
            self._single_generation_queue.put({
                "type": "success",
                "model": model,
                "image": image,
                "time": generation_time,
            })
            LOGGER.debug("Queued success result for model=%s", model)
        except Exception as e:
            self._single_generation_queue.put({
                "type": "error",
                "model": model,
                "error": str(e),
            })
            LOGGER.exception("Error during background generation for model=%s", model)
        finally:
            self.generation_queue.finish_generation()
            self._single_generation_queue.put({
                "type": "cleanup",
                "model": model,
            })
            LOGGER.debug("Queued cleanup for model=%s", model)
    
    def _update_image_display(self):
        """Update the displayed image."""
        self._schedule_image_update()
    
    def _schedule_image_update(self):
        """Schedule an image update with current parameters."""
        if self.current_image:
            params = {
                "zoom": self.image_display_manager.processor.get_zoom_level(),
                "offset_x": self.image_display_manager.processor.get_view_offset()[0],
                "offset_y": self.image_display_manager.processor.get_view_offset()[1],
                "frame_width": self.image_frame.winfo_width(),
                "frame_height": self.image_frame.winfo_height(),
            }
            self.update_thread_manager.schedule_update(params)
    
    def _create_photo_image(self, params):
        """Create a photo image for display."""
        return self.image_display_manager.create_display_image(
            params["frame_width"], 
            params["frame_height"]
        )
    
    def _check_for_next_generation(self):
        """Check if there's another generation queued."""
        next_prompt = self.generation_queue.get_next_prompt()
        if next_prompt:
            self._start_generation(next_prompt)
    
    def _clear_model_cache(self):
        """Clear all cached images and tick marks."""
        self.model_image_cache.clear()
        self.model_selection.clear_all_ticks()
        # Also clear any generating indicators
        self.model_selection.clear_all_generating()
        # Clear queue overlay tracking
        self.queued_models.clear()
        self.models_with_errors.clear()
        self._update_queue_overlay()
    
    def check_display_queue(self):
        """Check for pending display updates and parallel generation results."""
        try:
            while self.update_thread_manager.has_pending_display_updates():
                photo = self.update_thread_manager.get_display_update()
                if photo:
                    self.image_label.configure(image=photo)
                    # Store reference on the app instance to avoid type-checker complaint
                    self._current_photo = photo

            # Process sequential generation results
            while not self._single_generation_queue.empty():
                result = self._single_generation_queue.get_nowait()
                LOGGER.debug("Processing sequential result type=%s model=%s", result.get("type"), result.get("model"))
                self._handle_single_result(result)
            
            # Check for parallel generation results
            while self.generation_queue.has_parallel_results():
                result = self.generation_queue.get_parallel_result()
                if result:
                    LOGGER.debug("Processing parallel result for model=%s first=%s", result.get("model"), result.get("first"))
                    self._handle_parallel_result(result)
        finally:
            self.root.after(DISPLAY_QUEUE_CHECK_INTERVAL, self.check_display_queue)
    
    def _handle_parallel_result(self, result: Dict[str, Any]):
        """Handle a result from parallel generation."""
        model = result["model"]
        
        if "error" in result:
            # Handle error - track error for overlay
            self.models_with_errors[model] = result['error']
            self._update_queue_overlay()
            self.root.after(0, lambda: self.status_label.config(text=f"Error for {model}: {result['error']}"))
            self.root.after(0, lambda m=model: self.model_selection.clear_model_generating(m))
        else:
            # Handle successful generation
            image = result["result"]
            generation_time = result["time"]
            
            # Cache the generated image
            self.model_image_cache[model] = image
            
            # Update model button to show tick
            self.root.after(0, lambda m=model: self.model_selection.set_model_generated(m))
            
            # If this is the first completion, switch to this model and display the image
            if result["first"]:
                self.current_image = image
                self.model_selection.set_selected_model(model, notify=False)
                self.image_display_manager.processor.reset_view()
                self.image_display_manager.set_image(self.current_image)
                self._update_image_display()
                self.model_selection.set_model_viewed(model)
                self.root.after(0, lambda t=generation_time: self.status_label.config(
                    text=f"Ready (Generated in {t:.1f}s) - Switched to first completed model"
                ))
            else:
                # Update status to show completion without switching
                self.root.after(0, lambda m=model, t=generation_time: self.status_label.config(
                    text=f"Completed {m} in {t:.1f}s"
                ))
        
        # Update the queue overlay
        self._update_queue_overlay()
        
        # Check if all parallel generation is complete
        if not self.generation_queue.is_parallel_active():
            self.root.after(0, lambda: self.status_label.config(text=StatusMessages.ALL_PARALLEL_COMPLETE))
    
    def _handle_single_result(self, result: Dict[str, Any]):
        """Handle sequential generation results on the main thread."""
        result_type = result.get("type")
        model = result.get("model")

        if result_type == "success" and model and result.get("image") is not None:
            image = result["image"]
            generation_time = result.get("time", 0.0)
            # Cache the generated image
            self.model_image_cache[model] = image
            # Update model button to show tick
            self.model_selection.set_model_generated(model)
            # Update queue overlay to show completion
            self._update_queue_overlay()
            # Only switch to display the image if this model is still selected
            if model == self.model_selection.get_selected_model():
                self.current_image = image
                self.image_display_manager.processor.reset_view()
                self.image_display_manager.set_image(image)
                self._update_image_display()
                self.model_selection.set_model_viewed(model)
                self.status_label.config(text=f"Ready (Generated in {generation_time:.1f}s)")
            else:
                # Update status to show completion without switching
                self.status_label.config(text=f"Completed {model} in {generation_time:.1f}s")
            LOGGER.debug("Single generation success handled for model=%s", model)
        elif result_type == "error" and model:
            error_msg = result.get("error", "Unknown error")
            # Track error for overlay display
            self.models_with_errors[model] = error_msg
            self._update_queue_overlay()
            self.status_label.config(text=f"Error: {error_msg}")
            LOGGER.debug("Single generation error handled for model=%s message=%s", model, error_msg)
        elif result_type == "cleanup" and model:
            self.model_selection.clear_model_generating(model)
            current_status = self.status_label.cget("text")
            if current_status.lower().startswith("generating image"):
                self.status_label.config(text=StatusMessages.READY)
                LOGGER.debug("Cleanup forced status reset to Ready for model=%s", model)
            # Start next queued generation, if any
            self._check_for_next_generation()

    def show_toast(self, message: str, duration: int = 2000):
        """Show a temporary toast notification overlay."""
        toast = tk.Label(
            self.image_frame, 
            text=message, 
            background="#333333", 
            foreground="white", 
            padx=15, 
            pady=8, 
            font=('Segoe UI', 10)
        )
        # Place centered at the bottom of the image frame
        toast.place(relx=0.5, rely=0.9, anchor="center")
        
        # Destroy after duration
        self.root.after(duration, toast.destroy)

    def save_image(self):
        """Save the current image to file."""
        if not self.current_image:
            self.status_label.config(text=StatusMessages.NO_IMAGE_TO_SAVE)
            return
        
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")]
            )
            
            if not filepath:
                return  # User cancelled
            
            # Save the image
            self.current_image.save(filepath, "jpeg")
            self.status_label.config(text=f"Image saved to {filepath}")
            self.show_toast("Image Saved! 💾")
            
        except Exception as e:
            self.status_label.config(text=f"Error saving image: {e}")
    
    def copy_image_to_clipboard(self):
        """Copy the current image to clipboard."""
        if not self.current_image:
            self.status_label.config(text=StatusMessages.NO_IMAGE_TO_COPY)
            return
        
        if self.clipboard_manager.copy_image_to_clipboard(self.current_image):
            self.status_label.config(text=StatusMessages.COPIED_TO_CLIPBOARD)
            self.show_toast("Copied to Clipboard! 📋")
        else:
            self.status_label.config(text=StatusMessages.COPY_NOT_SUPPORTED)


def main(argv: Optional[list[str]] = None):
    """Main application entry point."""
    args = argv if argv is not None else sys.argv[1:]

    debug_requested = False
    remaining_args: list[str] = []
    for arg in args:
        if arg in {"--debug", "-d"}:
            debug_requested = True
        else:
            remaining_args.append(arg)

    if debug_requested:
        set_debug_logging(True)

    if remaining_args:
        LOGGER.warning("Ignoring unused CLI arguments: %s", " ".join(remaining_args))

    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
