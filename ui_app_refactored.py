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
from threading_utils import UpdateThreadManager, SpinnerAnimator
from generation_manager import GenerationManager, RequestStatus
from settings_manager import SettingsManager, WindowSettings


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
        
        # Initialize settings manager and load saved window state
        self.settings_manager = SettingsManager()
        self._saved_window_settings = self.settings_manager.load_window_settings()
        
        # Initialize managers and components
        self.generation_manager = GenerationManager()
        self.update_thread_manager = UpdateThreadManager()
        self.clipboard_manager = ClipboardManager()
        self.tooltip_manager = TooltipManager()
        self.spinner_animator = SpinnerAnimator(SPINNER_FRAMES)
        
        # Current image and state
        self.current_image: Optional[Image.Image] = None
        # Keep a reference to the current Tk photo image to prevent GC
        self._current_photo = None
        
        # Model memory cache: stores generated images per model
        self.model_image_cache: Dict[str, Image.Image] = {}
        self.current_prompt: str = ""
        
        # Track models in queue for overlay display
        self.models_with_errors: Dict[str, str] = {}  # model -> error message
        # Track models in queue for overlay display
        self.models_with_errors: Dict[str, str] = {}  # model -> error message
        self.handled_request_ids: set = set() # Track processed requests
        self.last_overlay_hash: str = "" # To prevent UI flickering
        
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
        
        # Apply saved window state after UI is fully created
        self._apply_saved_window_state()
        
        # Bind window close event to save state
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
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
        # Default splitter positions (will be overridden by saved settings if available)
        self._default_main_splitter_pos = 350
        self._default_sidebar_splitter_pos = 400
        self.root.after(0, lambda: self.main_splitter.sashpos(0, self._default_main_splitter_pos))
        self.root.after(0, lambda: self.sidebar_splitter.sashpos(0, self._default_sidebar_splitter_pos))
    
    def _apply_saved_window_state(self):
        """Apply saved window position, size, and splitter positions."""
        settings = self._saved_window_settings
        
        if not settings.is_valid():
            LOGGER.debug("No valid saved window settings, using defaults")
            return
        
        try:
            # Apply window geometry (position and size)
            if settings.width and settings.height:
                # Check if the saved position is within current screen bounds
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                
                x = settings.x if settings.x is not None else 100
                y = settings.y if settings.y is not None else 100
                
                # Ensure window is visible on screen (at least partially)
                # Allow some buffer to ensure window is accessible
                if x < -settings.width + 100:
                    x = 100
                if x > screen_width - 100:
                    x = screen_width - settings.width
                if y < 0:
                    y = 0
                if y > screen_height - 100:
                    y = screen_height - settings.height
                
                geometry = f"{settings.width}x{settings.height}+{x}+{y}"
                self.root.geometry(geometry)
                LOGGER.debug(f"Applied window geometry: {geometry}")
            
            # Apply maximized state
            if settings.is_maximized:
                self.root.state('zoomed')
                LOGGER.debug("Restored maximized state")
            
            # Apply splitter positions after a short delay to ensure window is rendered
            def apply_splitter_positions():
                try:
                    if settings.main_splitter_position is not None:
                        self.main_splitter.sashpos(0, settings.main_splitter_position)
                        LOGGER.debug(f"Applied main splitter position: {settings.main_splitter_position}")
                    
                    if settings.sidebar_splitter_position is not None:
                        self.sidebar_splitter.sashpos(0, settings.sidebar_splitter_position)
                        LOGGER.debug(f"Applied sidebar splitter position: {settings.sidebar_splitter_position}")
                except Exception as e:
                    LOGGER.warning(f"Error applying splitter positions: {e}")
            
            # Delay splitter position application to ensure window is fully visible
            self.root.after(100, apply_splitter_positions)
            
        except Exception as e:
            LOGGER.warning(f"Error applying saved window state: {e}")
    
    def _save_window_state(self):
        """Save current window position, size, and splitter positions."""
        try:
            # Check if window is maximized
            is_maximized = self.root.state() == 'zoomed'
            
            # Get window geometry
            # Use winfo_geometry for actual window position/size
            geometry = self.root.geometry()
            # Parse geometry string (e.g., "1024x768+100+50")
            parts = geometry.replace('x', '+').split('+')
            width = int(parts[0])
            height = int(parts[1])
            x = int(parts[2]) if len(parts) > 2 else 0
            y = int(parts[3]) if len(parts) > 3 else 0
            
            # If maximized, we want to save the restored (non-maximized) geometry
            # but Tkinter doesn't easily provide this, so we save current and note maximized
            
            # Get splitter positions
            try:
                main_splitter_pos = self.main_splitter.sashpos(0)
            except Exception:
                main_splitter_pos = None
            
            try:
                sidebar_splitter_pos = self.sidebar_splitter.sashpos(0)
            except Exception:
                sidebar_splitter_pos = None
            
            settings = WindowSettings(
                x=x,
                y=y,
                width=width,
                height=height,
                main_splitter_position=main_splitter_pos,
                sidebar_splitter_position=sidebar_splitter_pos,
                is_maximized=is_maximized
            )
            
            self.settings_manager.save_window_settings(settings)
            LOGGER.debug(f"Saved window state: {settings.to_dict()}")
            
        except Exception as e:
            LOGGER.warning(f"Error saving window state: {e}")
    
    def _on_window_close(self):
        """Handle window close event - save state and exit."""
        self._save_window_state()
        self.root.destroy()

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
        self.queue_overlay_expanded = False # Track expanded state
        self.queue_model_labels: Dict[str, tk.Label] = {}

        # Overlay view options/state
        self.queue_overlay_show_thumbnails = tk.BooleanVar(value=False)
        self.queue_thumbnail_images: Dict[str, ImageTk.PhotoImage] = {}

        # Debounced collapse to prevent disappearing during redraws
        self._overlay_collapse_after_id: Optional[str] = None
        self._overlay_rebuilding: bool = False
        
        # Bind hover events for auto-expand
        self.queue_overlay_frame.bind('<Enter>', self._on_overlay_hover_enter)
        self.queue_overlay_frame.bind('<Leave>', self._on_overlay_hover_leave)
    
    def _update_queue_overlay(self, active_requests=None):
        """Update the queue overlay with current model states."""
        # Import here to avoid circular import issues
        from config import MODEL_ABBREVIATIONS
        
        # Get requests if not provided
        if active_requests is None:
            active_requests = self.generation_manager.get_all_requests()
            
        # We now want to show ALL requests in the "History" / "Generations" view
        # so we don't filter out finished ones.
        # so we don't filter out finished ones.
        relevant_items = active_requests # All tracked requests
        
        show_thumbnails = bool(self.queue_overlay_show_thumbnails.get())

        # Calculate state hash to prevent flashing (only redraw if changed)
        # Hash comprises: count + expanded_state + thumbnails + model status sets + for each item: id, status, seen
        current_hash_parts = [str(len(relevant_items)), str(self.queue_overlay_expanded), str(show_thumbnails)]

        # Include model list status so overlay stays in sync even when only tick/eye state changes
        try:
            viewed_models = sorted(getattr(self.model_selection, "models_viewed", set()))
            ticked_models = sorted(getattr(self.model_selection, "models_with_ticks", set()))
        except Exception:
            viewed_models = []
            ticked_models = []
        current_hash_parts.append("viewed:" + ",".join(viewed_models))
        current_hash_parts.append("ticked:" + ",".join(ticked_models))
        # Sort for stable hash
        sorted_for_hash = sorted(relevant_items, key=lambda r: r.request_id)
        for r in sorted_for_hash:
            current_hash_parts.append(f"{r.request_id}:{r.status.name}:{r.seen}")
        
        current_hash = "|".join(current_hash_parts)
        
        # If hash matches, nothing changed fundamentally in the list structure/status
        # (Assuming we don't need to animate progress bars here, just status icons)
        if current_hash == self.last_overlay_hash and self.queue_overlay_visible:
            return
            
        self.last_overlay_hash = current_hash
        
        # Always show the overlay
        if not self.queue_overlay_visible:
            self.queue_overlay_frame.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)
            self.queue_overlay_visible = True
            
        # Clear existing labels
        self._overlay_rebuilding = True
        try:
            for widget in self.queue_overlay_frame.winfo_children():
                widget.destroy()
            self.queue_model_labels.clear()
            self.queue_thumbnail_images.clear()
        finally:
            self._overlay_rebuilding = False
        
        # --- Header Section ---
        header_frame = tk.Frame(self.queue_overlay_frame, bg='#ffffff')
        header_frame.pack(fill='x', pady=(0, 4))
        
        # Title
        # Count pending items (QUEUED or PROCESSING)
        pending_count = sum(1 for r in relevant_items if r.status in (RequestStatus.QUEUED, RequestStatus.PROCESSING))
        title_text = f"Generations ({pending_count})" if pending_count > 0 else "Generations"
        title_label = tk.Label(
            header_frame,
            text=title_text,
            font=('Segoe UI', 9, 'bold'),
            background='#ffffff',
            foreground='#333333'
        )
        title_label.pack(side='left')
        
        # Clear Button (only if there are items to clear)
        # Clear Buttons
        btn_frame = tk.Frame(header_frame, bg='#ffffff')
        btn_frame.pack(side='right')
        
        # Navigation Buttons
        nav_frame = tk.Frame(header_frame, bg='#ffffff')
        nav_frame.pack(side='right', padx=(0, 8))

        prev_btn = tk.Label(
            nav_frame,
            text="Prev Unseen",
            font=('Segoe UI', 8),
            background='#ffffff',
            foreground='#0078d4',
            cursor='hand2'
        )
        prev_btn.pack(side='left', padx=4)
        prev_btn.bind('<Button-1>', lambda e: self._show_prev_unseen())
        self._add_hover_effect(prev_btn, '#0078d4', '#004578', underline=True)

        next_btn = tk.Label(
            nav_frame,
            text="Next Unseen",
            font=('Segoe UI', 8),
            background='#ffffff',
            foreground='#0078d4',
            cursor='hand2'
        )
        next_btn.pack(side='left', padx=4)
        next_btn.bind('<Button-1>', lambda e: self._show_next_unseen())
        self._add_hover_effect(next_btn, '#0078d4', '#004578', underline=True)

        if self.queue_overlay_expanded:
            # View toggle: thumbnails
            thumbs_cb = tk.Checkbutton(
                btn_frame,
                text="Thumbnails",
                variable=self.queue_overlay_show_thumbnails,
                command=lambda: self._update_queue_overlay(),
                background='#ffffff',
                activebackground='#ffffff',
                foreground='#333333',
                selectcolor='#ffffff',
                highlightthickness=0,
                bd=0,
                font=('Segoe UI', 8),
                cursor='hand2'
            )
            thumbs_cb.pack(side='right', padx=(8, 0))

            if any(r.status in (RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.CANCELLED) for r in relevant_items):
                # Clear All
                clear_all_btn = tk.Label(
                    btn_frame,
                    text="Clear All",
                    font=('Segoe UI', 8),
                    background='#ffffff',
                    foreground='#007bff',
                    cursor='hand2'
                )
                clear_all_btn.pack(side='right', padx=(5, 0))
                clear_all_btn.bind('<Button-1>', lambda e: self._clear_generations_history(all=True))
                self._add_hover_effect(clear_all_btn, '#007bff', '#0056b3', underline=True)

                # Clear Seen (only if there are seen items)
                if any(r.seen for r in relevant_items):
                    clear_seen_btn = tk.Label(
                        btn_frame,
                        text="Clear Seen",
                        font=('Segoe UI', 8),
                        background='#ffffff',
                        foreground='#007bff',
                        cursor='hand2'
                    )
                    clear_seen_btn.pack(side='right', padx=(5, 0))
                    clear_seen_btn.bind('<Button-1>', lambda e: self._clear_generations_history(all=False))
                    self._add_hover_effect(clear_seen_btn, '#007bff', '#0056b3', underline=True)

        # --- List Section (Only if Expanded) ---
        if self.queue_overlay_expanded:
            # Sort items: Newest first (by created_at)
            sorted_items = sorted(relevant_items, key=lambda r: r.created_at, reverse=True)

            # For syncing model-level viewed state to the latest completed request
            latest_completed_request_id_by_model: Dict[str, str] = {}
            for r in sorted_items:
                if r.status == RequestStatus.COMPLETED:
                    if r.model not in latest_completed_request_id_by_model:
                        latest_completed_request_id_by_model[r.model] = r.request_id
            
            # Limit the display if too many items (scrolling would be better, but for now cap it)
            display_items = sorted_items[:15] # Show latest 15
            
            # Create label for each request
            for req in display_items:
                model = req.model
                # Get display name
                display_name = model.replace("fal-ai/", "").replace("/", " ").title()
                display_name = MODEL_ABBREVIATIONS.get(display_name, display_name)
                
                # Determine icon and color based on state
                if req.status == RequestStatus.FAILED:
                    icon = "❌"
                    fg_color = '#dc3545'  # Red
                    state_text = "Failed"
                elif req.status == RequestStatus.COMPLETED:
                    model_is_viewed = False
                    try:
                        model_is_viewed = model in getattr(self.model_selection, "models_viewed", set())
                    except Exception:
                        model_is_viewed = False

                    is_latest_completed_for_model = (
                        latest_completed_request_id_by_model.get(model) == req.request_id
                    )
                    is_viewed = bool(req.seen) or (model_is_viewed and is_latest_completed_for_model)

                    if is_viewed:
                        icon = "👁"  # Eye for viewed
                        fg_color = '#28a745'
                        state_text = "Done (Viewed)"
                    else:
                        icon = "✓"
                        fg_color = '#28a745'
                        state_text = "Done (New)"
                elif req.status == RequestStatus.PROCESSING:
                    icon = "⏳"
                    fg_color = '#007bff'  # Blue
                    state_text = "Generating..."
                elif req.status == RequestStatus.QUEUED:
                    icon = "🕒"
                    fg_color = '#666666'  # Gray
                    state_text = "Queued"
                elif req.status == RequestStatus.CANCELLED:
                    icon = "🚫"
                    fg_color = '#999999'
                    state_text = "Cancelled"
                else:
                    icon = "?"
                    fg_color = 'black'
                    state_text = "?"
                
                # Label text
                label_text = f"{icon} {display_name}"
                
                # Create container frame for the row (to handle tooltip/clicks better)
                row_frame = tk.Frame(self.queue_overlay_frame, bg='white')
                row_frame.pack(anchor='w', fill='x', pady=1)

                # Optional thumbnail
                if show_thumbnails and req.status == RequestStatus.COMPLETED:
                    thumb_source = req.result_image or self.model_image_cache.get(model)
                    if thumb_source:
                        try:
                            thumb_img = thumb_source.copy()
                            # Larger thumbnails for readability in the Generations view
                            thumb_img.thumbnail((64, 64), Image.LANCZOS)
                            thumb_photo = ImageTk.PhotoImage(thumb_img)
                            self.queue_thumbnail_images[req.request_id] = thumb_photo
                            thumb_label = tk.Label(
                                row_frame,
                                image=thumb_photo,
                                background='#ffffff',
                                cursor='hand2' if req.result_image else 'arrow'
                            )
                            thumb_label.pack(side='left', padx=(0, 6))

                            # Make thumbnail behave like the row label for completed items
                            if req.result_image:
                                thumb_label.bind('<Button-1>', lambda e, rid=req.request_id: self._on_queue_model_click(rid))
                                thumb_label.bind('<Enter>', lambda e, lbl=thumb_label: lbl.configure(background='#f0f0f0'))
                                thumb_label.bind('<Leave>', lambda e, lbl=thumb_label: lbl.configure(background='#ffffff'))

                            # Tooltip mirrors the text label tooltip
                            if req.status == RequestStatus.FAILED:
                                self.tooltip_manager.add_tooltip(thumb_label, f"Error: {req.error_message}")
                            else:
                                self.tooltip_manager.add_tooltip(thumb_label, f"Status: {state_text}")
                        except Exception:
                            # Best-effort: if thumbnail creation fails, just skip
                            pass
                
                # Create clickable label
                model_label = tk.Label(
                    row_frame,
                    text=label_text,
                    font=('Segoe UI', 9),
                    background='#ffffff',
                    foreground=fg_color,
                    cursor='hand2' if req.status == RequestStatus.COMPLETED else 'arrow'
                )
                model_label.pack(side='left')
                
                # Add tooltip for error messages or status
                if req.status == RequestStatus.FAILED:
                    self.tooltip_manager.add_tooltip(model_label, f"Error: {req.error_message}")
                else:
                    self.tooltip_manager.add_tooltip(model_label, f"Status: {state_text}")
                
                # Bind click handler if image is available
                if req.status == RequestStatus.COMPLETED and req.result_image:
                    # Use request_id to robustly retrieve image even if cache is cleared
                    model_label.bind('<Button-1>', lambda e, rid=req.request_id: self._on_queue_model_click(rid))
                    # Add hover effect
                    model_label.bind('<Enter>', lambda e, lbl=model_label: lbl.configure(background='#f0f0f0'))
                    model_label.bind('<Leave>', lambda e, lbl=model_label: lbl.configure(background='#ffffff'))
                
                self.queue_model_labels[model] = model_label
        else:
            # Collapsed view - show nothing below header
            pass

    def _on_overlay_hover_enter(self, event):
        """Handle mouse enter on overlay."""
        if self._overlay_collapse_after_id:
            try:
                self.root.after_cancel(self._overlay_collapse_after_id)
            except Exception:
                pass
            self._overlay_collapse_after_id = None

        if not self.queue_overlay_expanded:
            self.queue_overlay_expanded = True
            self._update_queue_overlay()

    def _on_overlay_hover_leave(self, event):
        """Handle mouse leave on overlay."""
        # Debounce collapse to avoid disappearing while the overlay is rebuilding widgets
        if self._overlay_rebuilding:
            return

        if self._overlay_collapse_after_id:
            try:
                self.root.after_cancel(self._overlay_collapse_after_id)
            except Exception:
                pass

        self._overlay_collapse_after_id = self.root.after(150, self._maybe_collapse_overlay)

    def _maybe_collapse_overlay(self):
        """Collapse overlay if the pointer is outside the overlay."""
        self._overlay_collapse_after_id = None
        if self._overlay_rebuilding:
            return

        x, y = self.root.winfo_pointerxy()
        widget_under_mouse = self.root.winfo_containing(x, y)

        if widget_under_mouse is None:
            should_collapse = True
        else:
            widget_name = str(widget_under_mouse)
            should_collapse = not (
                widget_under_mouse == self.queue_overlay_frame or
                widget_name.startswith(str(self.queue_overlay_frame))
            )

        if not should_collapse:
            return

        if self.queue_overlay_expanded:
            self.queue_overlay_expanded = False
            self._update_queue_overlay()

        if not self.queue_overlay_visible:
            self.queue_overlay_frame.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)
            self.queue_overlay_visible = True

        self.queue_overlay_frame.lift()
    
    def _add_hover_effect(self, widget, normal_color, hover_color, underline=False):
        """Add generic hover effect to a label."""
        font_normal = ('Segoe UI', 8)
        font_hover = ('Segoe UI', 8, 'underline') if underline else ('Segoe UI', 8)
        
        widget.bind('<Enter>', lambda e: widget.configure(foreground=hover_color, font=font_hover))
        widget.bind('<Leave>', lambda e: widget.configure(foreground=normal_color, font=font_normal))

    def _clear_generations_history(self, all: bool = False):
        """Clear completed items from history."""
        if all:
            self.generation_manager.clear_completed()
        else:
            self.generation_manager.clear_seen()
        
        # Rebuild handled_request_ids from remaining requests
        remaining = self.generation_manager.get_all_requests()
        remaining_ids = {r.request_id for r in remaining}
        # Intersect to keep only valid ones
        self.handled_request_ids = self.handled_request_ids.intersection(remaining_ids)
        
        self._update_queue_overlay()
    
    def _on_queue_model_click(self, request_id: str):
        """Handle click on a history item in the queue overlay."""
        req = self.generation_manager.get_request(request_id)
        if req and req.result_image:
            # Switch to this model
            self.model_selection.set_selected_model(req.model, notify=False)
            
            # Mark as seen
            self.generation_manager.mark_seen(request_id)

            # Sync main model list indicator
            self.model_selection.set_model_viewed(req.model)
            
            # Display the image from the request object (robust vs cache clearing)
            self.current_image = req.result_image
            self.image_display_manager.processor.reset_view()
            self.image_display_manager.set_image(self.current_image)
            self._update_image_display()
            self.status_label.config(text=f"Viewing Result: {req.model}")
            
            # Update overlay to show seen status
            self._update_queue_overlay()
    
    def _show_next_unseen(self):
        """Show the next (newest) unseen generation."""
        requests = self.generation_manager.get_all_requests()
        # Filter for unseen and completed
        unseen = [r for r in requests if not r.seen and r.status == RequestStatus.COMPLETED]
        
        if not unseen:
            self.show_toast("No unseen generations")
            return
            
        # Requests are sorted Newest First by default
        # So the first one is the Newest Unseen
        target = unseen[0]
        self._on_queue_model_click(target.request_id)

    def _show_prev_unseen(self):
        """Show the previous (oldest) unseen generation."""
        requests = self.generation_manager.get_all_requests()
        # Filter for unseen and completed
        unseen = [r for r in requests if not r.seen and r.status == RequestStatus.COMPLETED]
        
        if not unseen:
            self.show_toast("No unseen generations")
            return
            
        # Requests are sorted Newest First by default
        # So the last one is the Oldest Unseen
        target = unseen[-1]
        self._on_queue_model_click(target.request_id)
    
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
            self._mark_latest_completed_request_seen_for_model(model)
            self._update_queue_overlay()
            self.status_label.config(text=StatusMessages.READY_CACHED)
        else:
            # Generate with the new model immediately
            current_prompt = self.prompt_input.get_text()
            if current_prompt:
                self.model_selection.set_model_generating(model)
                self.generation_manager.submit_request(model, current_prompt)
                self._update_queue_overlay()
                self.status_label.config(text=StatusMessages.GENERATING)

    def _mark_latest_completed_request_seen_for_model(self, model: str) -> None:
        """Best-effort sync: mark the latest completed request for a model as seen."""
        try:
            all_requests = self.generation_manager.get_all_requests()
            latest = None
            for r in all_requests:
                if r.model != model:
                    continue
                if r.status != RequestStatus.COMPLETED:
                    continue
                if latest is None or r.created_at > latest.created_at:
                    latest = r
            if latest is not None:
                self.generation_manager.mark_seen(latest.request_id)
        except Exception:
            # Best-effort only
            return
    
    def _on_auto_generate_change(self, enabled: bool):
        """Handle auto-generate toggle."""
        # Logic for auto-generate toggle if needed
        pass

    def _on_key_release(self, event):
        """Handle key release events for auto-generation."""
        ignored_keys = {'Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next', 
                        'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 
                        'Caps_Lock', 'Num_Lock', 'Scroll_Lock', 'Pause', 'Print', 'Insert'}

        if (not self.prompt_input.is_auto_generate_enabled() or 
            event.keysym == 'Return' or 
            event.keysym in ignored_keys):
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
            # Check if prompt has changed
            if current_prompt == self.current_prompt:
                return

            # Prompt has changed
            self._clear_model_cache()
            self.current_prompt = current_prompt
            
            # Always submit to queue, never block
            model = self.model_selection.get_selected_model()
            self.model_selection.set_model_generating(model)
            self.generation_manager.submit_request(model, current_prompt)
            # Update overlay immediately (optional, but good for responsiveness)
            self._update_queue_overlay()
            self.status_label.config(text=StatusMessages.GENERATING)
    
    def _on_enter(self, event):
        """Handle Enter key press."""
        if not self.prompt_input.is_auto_generate_enabled():
            current_prompt = self.prompt_input.get_text()
            if len(current_prompt) > 0:
                # Check if prompt has changed - if so, clear cache
                if current_prompt != self.current_prompt:
                    self._clear_model_cache()
                    self.current_prompt = current_prompt
                
                model = self.model_selection.get_selected_model()
                self.model_selection.set_model_generating(model)
                self.generation_manager.submit_request(model, current_prompt)
                self._update_queue_overlay()
                self.status_label.config(text=StatusMessages.GENERATING)
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
        """Enhance the prompt using AI API (async - runs in background thread)."""
        current_prompt = self.prompt_input.get_text()
        if not current_prompt:
            self.status_label.config(text=StatusMessages.ENTER_PROMPT_TO_ENHANCE)
            return
        
        # Show enhancing state in UI
        self.prompt_input.set_enhancing(True)
        self.status_label.config(text=StatusMessages.ENHANCING)
        
        def do_enhance():
            """Background thread function to call the enhancement API."""
            try:
                enhanced = enhance_prompt(current_prompt, directions=directions)
                # Schedule UI update on main thread
                self.root.after(0, lambda: self._on_enhance_complete(enhanced))
            except Exception as e:
                # Schedule error handling on main thread
                self.root.after(0, lambda: self._on_enhance_error(str(e)))
        
        # Start background thread
        thread = threading.Thread(target=do_enhance, daemon=True)
        thread.start()
    
    def _on_enhance_complete(self, enhanced_prompt: str):
        """Handle successful prompt enhancement (called on main thread)."""
        # Restore UI state
        self.prompt_input.set_enhancing(False)
        
        # Clear cache since prompt is changing
        self._clear_model_cache()
        
        self.prompt_input.set_text(enhanced_prompt)
        self.current_prompt = enhanced_prompt
        self.status_label.config(text=StatusMessages.ENHANCED)
        
        # Auto-generate if enabled in prompt input
        if self.prompt_input.should_autogenerate_after_enhance():
            self.manual_generate()
    
    def _on_enhance_error(self, error_message: str):
        """Handle prompt enhancement error (called on main thread)."""
        # Restore UI state
        self.prompt_input.set_enhancing(False)
        self.status_label.config(text=f"Error enhancing prompt: {error_message}")
    
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
            
            model = self.model_selection.get_selected_model()
            self.model_selection.set_model_generating(model)
            self.generation_manager.submit_request(model, current_prompt)
            self._update_queue_overlay()
            self.status_label.config(text=StatusMessages.GENERATING)
    
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

        # Check if prompt has changed - if so, clear cache
        if current_prompt != self.current_prompt:
            self._clear_model_cache()
            self.current_prompt = current_prompt
        
        # Submit all requests to the manager
        for model in starred_models:
            self.generation_manager.submit_request(model, current_prompt)
            # Optimistically mark as generating
            self.model_selection.set_model_generating(model)
        
        # Trigger overlay update immediately
        self._update_queue_overlay()
        
        self.status_label.config(text=f"Queued images for {len(starred_models)} models...")
    
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

        # Clear cache since we have a new prompt
        self._clear_model_cache()
        self.current_prompt = clipboard_prompt
        
        # Submit all requests to the manager
        for model in starred_models:
            self.generation_manager.submit_request(model, clipboard_prompt)
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
    

    
    def _clear_model_cache(self):
        """Clear all cached images and tick marks."""
        self.model_image_cache.clear()
        self.model_selection.clear_all_ticks()
        # Also clear any generating indicators
        self.model_selection.clear_all_generating()
        # Clear queue overlay tracking
        self.models_with_errors.clear()
        self._update_queue_overlay()
    
    def check_display_queue(self):
        """Check for pending display updates and generation results."""
        try:
            # 1. Handle Display Updates (Main thread UI updates from background)
            while self.update_thread_manager.has_pending_display_updates():
                photo = self.update_thread_manager.get_display_update()
                if photo:
                    self.image_label.configure(image=photo)
                    self._current_photo = photo

            # 2. Check Generation Requests
            # Get all requests that are completed/failed/cancelled but not yet handled
            all_requests = self.generation_manager.get_all_requests()
            
            # Update Overlay with active requests
            # Update Overlay with all requests (for history)
            self._update_queue_overlay_from_requests(all_requests)

            # Process completed requests
            for req in all_requests:
                if req.request_id in self.handled_request_ids:
                    continue
                
                if req.status == RequestStatus.COMPLETED:
                    self._handle_completed_request(req)
                    self.handled_request_ids.add(req.request_id)
                elif req.status == RequestStatus.FAILED:
                    self._handle_failed_request(req)
                    self.handled_request_ids.add(req.request_id)
                elif req.status == RequestStatus.CANCELLED:
                    # Just mark as handled so we don't check again
                    self.handled_request_ids.add(req.request_id)
            
            # Optional: Periodic cleanup of handled requests from manager to prevent memory leak
            # (In a real app, might want to keep history, but here we can clean up old ones)
            if len(self.handled_request_ids) > 100:
                 self.generation_manager.clear_completed()
                 self.handled_request_ids.clear()
                 
        finally:
            self.root.after(DISPLAY_QUEUE_CHECK_INTERVAL, self.check_display_queue)

    def _handle_completed_request(self, req):
        """Handle a successfully completed generation request."""
        model = req.model
        image = req.result_image
        duration = req.duration
        
        # Cache image
        if image:
            self.model_image_cache[model] = image
            
        # Update UI: Tick mark
        self.model_selection.set_model_generated(model)
        
        # Update Status
        self.status_label.config(text=f"Completed {model} in {duration:.1f}s")
        
        # If this model is currently selected, show the image
        if self.model_selection.get_selected_model() == model:
             self.current_image = image
             self.image_display_manager.processor.reset_view()
             self.image_display_manager.set_image(image)
             self._update_image_display()
             self.model_selection.set_model_viewed(model)
             self.generation_manager.mark_seen(req.request_id) # Mark as seen in manager/overlay
             self.status_label.config(text=f"Ready (Generated in {duration:.1f}s)")
             self.show_toast(f"Generated {model}!")

    def _handle_failed_request(self, req):
        """Handle a failed generation request."""
        model = req.model
        error_msg = req.error_message or "Unknown Error"
        
        self.models_with_errors[model] = error_msg
        self.model_selection.clear_model_generating(model)
        self.status_label.config(text=f"Error {model}: {error_msg}")
        LOGGER.error(f"Generation failed for {model}: {error_msg}")

    def _update_queue_overlay_from_requests(self, active_requests):
        """Update the queue overlay based on active requests."""
        # Map active requests to models to reuse existing overlay logic structure
        # (Though we might want to make it request-based later)
        
        # We need to construct a list of 'queued_models' for the existing overlay logic,
        # OR better, rewrite overlay logic to handle request objects.
        # Let's rewrite the overlay update method separately.
        # For now, just pass the list to the new overlay method.
        self._update_queue_overlay(active_requests=active_requests)


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
