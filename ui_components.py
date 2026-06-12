"""
UI Components module for AI Image Workbench.
Contains specialized UI components for model selection, controls, and prompt input.
"""

import tkinter as tk
from tkinter import ttk, simpledialog
from typing import Optional, Callable, Dict, Any, List
from PIL import Image, ImageTk
from config import (
    MODEL_CATEGORIES, MODEL_ABBREVIATIONS, SPINNER_FRAMES,
    BACKGROUND_COLOR, SELECTED_BUTTON_COLOR, HOVER_BUTTON_COLOR,
    ACTIVE_BUTTON_COLOR, BASE_FONT, BUTTON_FONT, BUTTON_BOLD_FONT,
    ACCENT_COLOR, ACCENT_HOVER_COLOR, TEXT_COLOR, PROMPT_FONT, HEADER_FONT,
    FILMSTRIP_ITEM_SIZE, FILMSTRIP_PROMPT_TRUNCATE,
    get_theme_color, get_current_theme
)
from generation_manager import RequestStatus


class ModelSelectionFrame(ttk.Frame):
    """Frame for model selection with categorized buttons."""
    
    def __init__(self, parent, on_model_select: Callable[[str, bool], None], default_model: str, on_hidden_change: Optional[Callable[[set], None]] = None):
        """Initialize the model selection frame."""
        super().__init__(parent)
        self.on_model_select = on_model_select
        self.on_hidden_change = on_hidden_change
        self.model_var = tk.StringVar(value=default_model)
        self.model_buttons: Dict[str, ttk.Button] = {}
        self.model_button_containers: Dict[str, ttk.Frame] = {}
        self.star_buttons: Dict[str, ttk.Button] = {}
        self.hide_buttons: Dict[str, ttk.Button] = {}
        self.model_button_texts: Dict[str, str] = {}  # Store original button text
        self.models_with_ticks: set = set()  # Track which models have generated images
        self.models_generating: set = set()  # Track which models are currently generating (hourglass)
        self.models_with_errors: Dict[str, str] = {}  # Track failed models and their error messages
        self.models_viewed: set = set()  # Track which models have been viewed
        self.starred_models: set = set()
        self.hidden_models: set = set()
        self.model_order = []  # Preserve insertion order for starred models retrieval
        self.tooltip_manager = TooltipManager()
        self.hidden_expanded = False  # Track if hidden group is expanded
        self.hidden_toggle_btn = None  # Reference to the hidden group toggle button
        
        # Create the label frame
        self.labelframe = ttk.LabelFrame(parent, text="Model Selection", padding=(10, 5))
        self.labelframe.grid(row=0, column=0, sticky="nsew", padx=8, pady=4)
        self.labelframe.grid_columnconfigure(0, weight=1)
        self.labelframe.grid_rowconfigure(0, weight=1)
        
        # Create canvas and scrollbar for scrolling
        self.canvas = tk.Canvas(self.labelframe, background=get_theme_color('canvas_bg'), highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.labelframe, orient="vertical", command=self.canvas.yview)
        self.model_matrix_frame = ttk.Frame(self.canvas)
        
        # Configure canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid layout for canvas and scrollbar
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Create window in canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.model_matrix_frame, anchor="nw")
        
        # Bind events for scrolling
        self.model_matrix_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.create_model_matrix()
        self.configure_styles()

    def _on_frame_configure(self, event):
        """Reset the scroll region to encompass the inner frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Resize the inner frame to match the canvas width."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling."""
        # Only scroll if the mouse is over the model selection area
        x, y = self.winfo_pointerxy()
        widget_under_mouse = self.winfo_containing(x, y)
        
        # Check if the widget under mouse is part of the model selection frame
        is_descendant = False
        if widget_under_mouse:
            parent = widget_under_mouse
            while parent:
                if parent == self.labelframe:
                    is_descendant = True
                    break
                parent = parent.master
        
        if is_descendant:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def configure_styles(self):
        """Configure custom styles for model selection buttons."""
        style = ttk.Style()
        
        # Use a modern theme (clam) for a consistent look across platforms
        try:
            style.theme_use('clam')
        except Exception:
            pass
            
        # Set base font for all ttk widgets
        style.configure('.', font=BASE_FONT)
        
        # Get theme colors
        bg_color = get_theme_color('background')
        text_color = get_theme_color('text')
        button_bg = get_theme_color('button_bg')
        selected_btn = get_theme_color('selected_button')
        hover_btn = get_theme_color('hover_button')
        active_btn = get_theme_color('active_button')
        accent = get_theme_color('accent')
        
        # Set default background for frames and labels
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=text_color)
        style.configure('TLabelframe', background=bg_color)
        style.configure('TLabelframe.Label', background=bg_color, foreground=text_color, font=BUTTON_BOLD_FONT)
        
        # Configure selected button style
        style.configure('Model.Selected.TButton',
                       background=selected_btn,
                       foreground=accent,
                       relief='flat',
                       borderwidth=0,
                       padding=(8, 6),
                       font=BUTTON_BOLD_FONT)
                       
        # Configure normal button style
        style.configure('Model.TButton',
                       background=button_bg,
                       foreground=text_color,
                       relief='flat',
                       borderwidth=1,
                       padding=(8, 6),
                       font=BUTTON_FONT)
                       
        # Configure hover effects
        style.map('Model.TButton',
                 background=[('active', hover_btn), ('!active', button_bg)],
                 relief=[('active', 'flat')])
        style.map('Model.Selected.TButton',
                 background=[('active', active_btn), ('!active', selected_btn)])

        # Expand the internal label to fill the button so hover/tooltip works on the full area
        model_button_layout = [
            ('Button.button', {
                'children': [
                    ('Button.focus', {
                        'children': [
                            ('Button.padding', {
                                'children': [
                                    ('Button.label', {'sticky': 'nswe'}),
                                ],
                                'sticky': 'nswe',
                            }),
                        ],
                        'sticky': 'nswe',
                    }),
                ],
                'sticky': 'nswe',
            }),
        ]
        style.layout('Model.TButton', model_button_layout)
        style.layout('Model.Selected.TButton', model_button_layout)

        # Configure star toggle buttons
        style.configure('Star.TButton',
                padding=(4, 2),
                width=2,
                background=button_bg,
                relief='flat',
                font=BUTTON_FONT)
        style.configure('Star.Selected.TButton',
                padding=(4, 2),
                width=2,
                background=button_bg,
                relief='flat',
                font=BUTTON_BOLD_FONT,
                foreground=get_theme_color('star_selected'))
        style.map('Star.TButton',
              background=[('active', hover_btn), ('!active', button_bg)])
        style.map('Star.Selected.TButton',
              background=[('active', hover_btn), ('!active', button_bg)])

        # Configure hide toggle buttons
        style.configure('Hide.TButton',
                padding=(4, 2),
                width=2,
                background=button_bg,
                relief='flat',
                font=BUTTON_FONT)
        style.configure('Hide.Selected.TButton',
                padding=(4, 2),
                width=2,
                background=button_bg,
                relief='flat',
                font=BUTTON_BOLD_FONT,
                foreground=get_theme_color('hide_selected'))
        style.map('Hide.TButton',
              background=[('active', hover_btn), ('!active', button_bg)])
        style.map('Hide.Selected.TButton',
              background=[('active', hover_btn), ('!active', button_bg)])

        # Configure hidden group toggle button
        hidden_bg = get_theme_color('hidden_group')
        hidden_hover = get_theme_color('hover_button')
        style.configure('HiddenGroup.TButton',
                padding=(8, 4),
                background=hidden_bg,
                relief='flat',
                font=BUTTON_BOLD_FONT,
                foreground=get_theme_color('hidden_group_text'))
        style.map('HiddenGroup.TButton',
              background=[('active', hidden_hover), ('!active', hidden_bg)])
    
    def create_model_matrix(self):
        """Create a vertical list of model selection buttons organized by category."""
        # Clear existing widgets
        for widget in self.model_matrix_frame.winfo_children():
            widget.destroy()
        
        self.model_buttons.clear()
        self.model_button_containers.clear()
        self.star_buttons.clear()
        self.hide_buttons.clear()
        self.model_order.clear()
        
        row = 0
        
        # Create regular categories (excluding hidden models)
        for category, models in MODEL_CATEGORIES.items():
            # Filter out hidden models
            visible_models = [m for m in models if m not in self.hidden_models]
            
            if not visible_models:
                continue  # Skip empty categories
                
            # Create category label (uses themed style)
            category_label = ttk.Label(
                self.model_matrix_frame,
                text=category,
                font=HEADER_FONT
            )
            category_label.grid(row=row, column=0, sticky="w", padx=2, pady=(12, 4))
            row += 1
            
            # Create buttons for each visible model in this category
            for model in visible_models:
                row = self._create_model_row(model, row)
        
        # Create hidden models group at the bottom
        if self.hidden_models:
            # Hidden group header with toggle button
            hidden_header_frame = ttk.Frame(self.model_matrix_frame)
            hidden_header_frame.grid(row=row, column=0, padx=2, pady=(12, 4), sticky="ew")
            hidden_header_frame.grid_columnconfigure(1, weight=1)
            
            # Toggle button for expanding/collapsing hidden group
            self.hidden_toggle_btn = ttk.Button(
                hidden_header_frame,
                text="▶" if not self.hidden_expanded else "▼",
                command=self.toggle_hidden_group,
                style='HiddenGroup.TButton',
                width=3
            )
            self.hidden_toggle_btn.grid(row=0, column=0, padx=(0, 4))
            
            # Hidden group label (uses themed style)
            hidden_label = ttk.Label(
                hidden_header_frame,
                text=f"Hidden ({len(self.hidden_models)})",
                font=HEADER_FONT
            )
            hidden_label.grid(row=0, column=1, sticky="w")
            
            row += 1
            
            # Create hidden model buttons if expanded
            if self.hidden_expanded:
                for model in sorted(self.hidden_models):  # Sort for consistent ordering
                    row = self._create_model_row(model, row, is_hidden=True)
        
        # Configure column weights for responsive layout
        self.model_matrix_frame.grid_columnconfigure(0, weight=1)

        for model in self.model_buttons:
            self._update_button_text(model)
            self._update_button_tooltip(model)
    
    def _create_model_row(self, model: str, row: int, is_hidden: bool = False) -> int:
        """Create a row for a single model with all its buttons."""
        # Create a shorter display name for the button
        display_name = model.replace("fal-ai/", "").replace("/", " ").title()
        display_name = MODEL_ABBREVIATIONS.get(display_name, display_name)

        # Track order for deterministic starred model retrieval
        self.model_order.append(model)
        
        # Store the original text for this model
        self.model_button_texts[model] = display_name

        # Create a container row for buttons and model button
        row_frame = ttk.Frame(self.model_matrix_frame)
        row_frame.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
        row_frame.grid_columnconfigure(2, weight=1)  # Model button expands

        # Star toggle button
        star_btn = ttk.Button(
            row_frame,
            command=lambda m=model: self.toggle_star(m),
            style='Star.TButton'
        )
        star_btn.grid(row=0, column=0, padx=(0, 2))
        self.tooltip_manager.add_tooltip(star_btn, "Star model for parallel generation")
        self.star_buttons[model] = star_btn

        # Hide toggle button
        hide_btn = ttk.Button(
            row_frame,
            command=lambda m=model: self.toggle_hide(m),
            style='Hide.TButton'
        )
        hide_btn.grid(row=0, column=1, padx=(0, 4))
        self.tooltip_manager.add_tooltip(hide_btn, "Hide/unhide this model")
        self.hide_buttons[model] = hide_btn

        # Model selection button in an expanding container so tooltips cover the full row area
        btn_container = ttk.Frame(row_frame)
        btn_container.grid(row=0, column=2, sticky="ew")
        btn_container.grid_columnconfigure(0, weight=1)

        btn = ttk.Button(
            btn_container,
            text=display_name,
            command=lambda m=model: self.select_model(m),
            style='Model.TButton'
        )
        btn.grid(row=0, column=0, sticky="ew")

        self.model_button_containers[model] = btn_container

        self.model_buttons[model] = btn

        # Configure button style based on selection
        if model == self.model_var.get():
            btn.configure(style='Model.Selected.TButton')

        # Initialize button states
        self._update_star_button(model)
        self._update_hide_button(model)

        return row + 1
    
    def select_model(self, model: str):
        """Select a model and update button states."""
        # Check if this is a reselection of the current model
        is_reselection = (model == self.model_var.get())
        self.set_selected_model(model, notify=True, is_reselection=is_reselection)

    def set_selected_model(self, model: str, notify: bool = True, is_reselection: Optional[bool] = None):
        """Set the selected model programmatically."""
        if model not in self.model_buttons:
            return

        previous_model = self.model_var.get()
        self.model_var.set(model)

        # Update button appearances
        for m, btn in self.model_buttons.items():
            if m == model:
                btn.configure(style='Model.Selected.TButton')
            else:
                btn.configure(style='Model.TButton')

        if notify:
            reselection = is_reselection if is_reselection is not None else (model == previous_model)
            self.on_model_select(model, reselection)
    
    def get_selected_model(self) -> str:
        """Get the currently selected model."""
        return self.model_var.get()
    
    def set_model_generated(self, model: str):
        """Mark a model as having generated an image (add tick)."""
        # Once generation completes successfully, remove hourglass and add tick
        if model in self.models_generating:
            self.models_generating.discard(model)
        self.models_with_errors.pop(model, None)
        if model not in self.models_with_ticks:
            self.models_with_ticks.add(model)
        self._update_button_text(model)
        self._update_button_tooltip(model)
    
    def set_model_viewed(self, model: str):
        """Mark a model as viewed (change tick to eye)."""
        if model not in self.models_viewed:
            self.models_viewed.add(model)
        self._update_button_text(model)
    
    def clear_all_ticks(self):
        """Clear all tick marks and viewed status from model buttons."""
        self.models_with_ticks.clear()
        self.models_viewed.clear()
        self.models_with_errors.clear()
        for model in self.model_buttons:
            self._update_button_text(model)
            self._update_button_tooltip(model)
    
    def set_model_generating(self, model: str):
        """Mark a model as currently generating (show hourglass, remove tick/eye)."""
        # When generating, ensure no tick, eye, or error is shown for this model
        if model in self.models_with_ticks:
            self.models_with_ticks.discard(model)
        if model in self.models_viewed:
            self.models_viewed.discard(model)
        self.models_with_errors.pop(model, None)
            
        self.models_generating.add(model)
        self._update_button_text(model)
        self._update_button_tooltip(model)
    
    def clear_model_generating(self, model: str):
        """Clear generating indicator (hourglass) for a model."""
        if model in self.models_generating:
            self.models_generating.discard(model)
            self._update_button_text(model)
    
    def set_model_error(self, model: str, error_message: str):
        """Mark a model as failed and show an error indicator with tooltip."""
        if model in self.models_generating:
            self.models_generating.discard(model)
        self.models_with_errors[model] = error_message
        self._update_button_text(model)
        self._update_button_tooltip(model)

    def clear_model_error(self, model: str):
        """Clear the error indicator for a model."""
        if model in self.models_with_errors:
            del self.models_with_errors[model]
            self._update_button_text(model)
            self._update_button_tooltip(model)
    
    def clear_all_generating(self):
        """Clear all generating indicators (hourglasses)."""
        if self.models_generating:
            self.models_generating.clear()
            for model in self.model_buttons:
                self._update_button_text(model)
    
    def _update_button_text(self, model: str):
        """Update button text to show/hide status indicators."""
        if model in self.model_buttons:
            base_text = self.model_button_texts.get(model, "")
            # Priority: generating hourglass > error icon > viewed eye > generated tick
            if model in self.models_generating:
                new_text = f"⏳ {base_text}"
            elif model in self.models_with_errors:
                new_text = f"❌ {base_text}"
            elif model in self.models_viewed:
                new_text = f"👁 {base_text}"
            elif model in self.models_with_ticks:
                new_text = f"✓ {base_text}"
            else:
                new_text = base_text
            self.model_buttons[model].configure(text=new_text)

    def _update_button_tooltip(self, model: str):
        """Update button tooltip when there is extra info to show (e.g. errors)."""
        btn = self.model_buttons.get(model)
        container = self.model_button_containers.get(model)
        if not btn or not container:
            return

        tooltip_widgets = [container, btn]
        if model in self.models_with_errors:
            self.tooltip_manager.set_tooltip_region(
                tooltip_widgets, self.models_with_errors[model]
            )
        else:
            self.tooltip_manager.clear_tooltip_region(tooltip_widgets)

    def toggle_star(self, model: str):
        """Toggle the starred state for a model."""
        if model not in self.model_buttons:
            return

        if model in self.starred_models:
            self.starred_models.remove(model)
        else:
            self.starred_models.add(model)
        self._update_star_button(model)

    def set_starred(self, model: str, starred: bool):
        """Explicitly set the starred state for a model."""
        if model not in self.model_buttons:
            return

        if starred:
            self.starred_models.add(model)
        else:
            self.starred_models.discard(model)
        self._update_star_button(model)

    def get_starred_models(self):
        """Return the starred models in their original order."""
        return [model for model in self.model_order if model in self.starred_models]

    def clear_all_stars(self):
        """Clear all starred models."""
        if not self.starred_models:
            return
        self.starred_models.clear()
        for model in self.model_buttons:
            self._update_star_button(model)

    def _update_star_button(self, model: str):
        """Update star button appearance for a model."""
        btn = self.star_buttons.get(model)
        if not btn:
            return

        if model in self.starred_models:
            btn.configure(text="★", style='Star.Selected.TButton')
        else:
            btn.configure(text="☆", style='Star.TButton')
    
    def toggle_hide(self, model: str):
        """Toggle the hidden state for a model."""
        if model not in self.model_buttons:
            return

        # Don't allow hiding the currently selected model
        if model == self.model_var.get():
            return

        if model in self.hidden_models:
            self.hidden_models.remove(model)
        else:
            self.hidden_models.add(model)
        self._update_hide_button(model)
        self.create_model_matrix()  # Recreate the matrix to move the model
        
        # Notify callback if provided
        if self.on_hidden_change:
            self.on_hidden_change(self.hidden_models.copy())

    def set_hidden(self, model: str, hidden: bool):
        """Explicitly set the hidden state for a model."""
        if model not in self.model_buttons:
            return

        if hidden:
            self.hidden_models.add(model)
        else:
            self.hidden_models.discard(model)
        self._update_hide_button(model)
        self.create_model_matrix()  # Recreate the matrix to move the model

    def get_hidden_models(self) -> set:
        """Return the set of hidden models."""
        return self.hidden_models.copy()

    def set_hidden_models(self, hidden_models: set):
        """Set the hidden models and refresh the UI."""
        self.hidden_models = hidden_models.copy()
        self.create_model_matrix()

    def toggle_hidden_group(self):
        """Toggle the expanded/collapsed state of the hidden group."""
        self.hidden_expanded = not self.hidden_expanded
        self.create_model_matrix()

    def _update_hide_button(self, model: str):
        """Update hide button appearance for a model."""
        btn = self.hide_buttons.get(model)
        if not btn:
            return

        if model in self.hidden_models:
            btn.configure(text="👁", style='Hide.Selected.TButton')  # Eye icon for hidden
        else:
            btn.configure(text="🙈", style='Hide.TButton')  # Monkey hiding eyes for visible


class PromptInputFrame(ttk.Frame):
    """Frame for prompt input with auto-resizing text widget and integrated controls."""
    
    def __init__(self, parent, on_text_change: Callable[[tk.Event], None], on_enter: Callable[[tk.Event], Any],
                 on_enhance: Callable[[], None], on_enhance_with_directions: Callable[[], None],
                 on_generate: Callable[[], None], on_parallel_generate: Callable[[], None],
                 on_parallel_generate_clipboard: Callable[[], None],
                 on_save: Callable[[], None], on_copy: Callable[[], None],
                 on_auto_generate_change: Callable[[bool], None]):
        """Initialize the prompt input frame."""
        super().__init__(parent)
        self.on_text_change = on_text_change
        self.on_enter = on_enter
        self.on_enhance = on_enhance
        self.on_enhance_with_directions = on_enhance_with_directions
        self.on_generate = on_generate
        self.on_parallel_generate = on_parallel_generate
        self.on_parallel_generate_clipboard = on_parallel_generate_clipboard
        self.on_save = on_save
        self.on_copy = on_copy
        self.on_auto_generate_change = on_auto_generate_change
        
        self._configure_styles()
        

        # Create prompt container that fills available space
        self.container = ttk.Frame(parent)
        self.container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.container.grid_rowconfigure(1, weight=1)  # Input area expands
        self.container.grid_columnconfigure(0, weight=1)
        
        # --- Header: Label + Auto-Generate + Enhance ---

        self.header_frame = ttk.Frame(self.container)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(5, 4))

        ttk.Label(self.header_frame, text="Prompt", font=HEADER_FONT).pack(side="left")
        
        # Auto-generate checkbox

        self.auto_generate = tk.BooleanVar(value=True)
        self.auto_generate_checkbox = ttk.Checkbutton(
            self.header_frame,
            text="Auto-generate",
            variable=self.auto_generate,
            command=self._on_auto_generate_toggle
        )
        self.auto_generate_checkbox.pack(side="right", padx=(10, 10))

        # Enhance buttons
        self.enhance_btn = ttk.Button(
            self.header_frame,
            text="✨ Auto Enhance",
            style='Action.TButton',
            command=self.on_enhance
        )
        self.enhance_btn.pack(side="right", padx=2)
        
        self.enhance_dir_btn = ttk.Button(
            self.header_frame,
            text="✨ Enhance...",
            style='Action.TButton',
            command=self.on_enhance_with_directions
        )
        self.enhance_dir_btn.pack(side="right")
        
        # --- Input Area ---
        self.input_frame = ttk.Frame(self.container)
        self.input_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 5))
        self.input_frame.grid_rowconfigure(0, weight=1)  # Text expands to fill
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        self.text_input = tk.Text(
            self.input_frame,
            height=1,  # Start with minimum height
            font=PROMPT_FONT,
            wrap='word',
            relief='flat',
            padx=10,
            pady=10,
            background=get_theme_color('input_bg'),
            foreground=get_theme_color('text'),
            insertbackground=get_theme_color('text')
        )
        self.text_input.grid(row=0, column=0, sticky="nsew")
        
        # --- Primary Action: Generate ---
        self.generate_btn = ttk.Button(
            self.container,
            text="GENERATE IMAGE",
            style='Primary.TButton',
            command=self.on_generate
        )
        self.generate_btn.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        
        # --- Footer: Secondary Actions (Parallel, Save, Copy) ---
        self.footer_frame = ttk.Frame(self.container)
        self.footer_frame.grid(row=3, column=0, sticky="ew")
        self.footer_frame.grid_columnconfigure(1, weight=1) # Spacer
        
        # Left side: Parallel
        self.parallel_btn = ttk.Button(
            self.footer_frame,
            text="Generate ★ Starred",
            style='Action.TButton',
            command=self.on_parallel_generate
        )
        self.parallel_btn.pack(side="left")
        
        self.parallel_clipboard_btn = ttk.Button(
            self.footer_frame,
            text="★ from 📋",
            style='Action.TButton',
            command=self.on_parallel_generate_clipboard
        )
        self.parallel_clipboard_btn.pack(side="left", padx=(4, 0))
        
        # Right side: Output actions
        self.copy_btn = ttk.Button(
            self.footer_frame,
            text="📋 Copy",
            style='Action.TButton',
            command=self.on_copy
        )
        self.copy_btn.pack(side="right", padx=(4, 0))
        
        self.save_btn = ttk.Button(
            self.footer_frame,
            text="💾 Save",
            style='Action.TButton',
            command=self.on_save
        )
        self.save_btn.pack(side="right")
        

        # Bind events
        self.text_input.bind('<KeyRelease>', self.on_text_change)
        self.text_input.bind('<<Modified>>', self._on_text_modified)
        self.text_input.bind('<Return>', self.on_enter)
        # Remove the old configure binding that adjusts height
        self.text_input.bind('<Configure>', lambda e: self._on_container_resize())
        
        self.adjust_text_height()  # Initial adjustment

    def _configure_styles(self):
        style = ttk.Style()
        
        # Get theme colors
        accent = get_theme_color('accent')
        accent_hover = get_theme_color('accent_hover')
        button_bg = get_theme_color('button_bg')
        hover_btn = get_theme_color('hover_button')
        
        # Primary CTA Button (Generate)
        style.configure('Primary.TButton',
            font=('Segoe UI', 11, 'bold'),
            background=accent,
            foreground='white',
            padding=(10, 12),
            relief='flat'
        )
        style.map('Primary.TButton',
            background=[('active', accent_hover), ('!active', accent)],
            foreground=[('!disabled', 'white')]
        )
        
        # Secondary Action Buttons
        style.configure('Action.TButton',
            font=BUTTON_FONT,
            padding=(8, 4),
            relief='flat',
            background=button_bg
        )
        style.map('Action.TButton',
            background=[('active', hover_btn), ('!active', button_bg)]
        )

    def _on_auto_generate_toggle(self):
        self.on_auto_generate_change(self.auto_generate.get())

    def set_auto_generate_enabled(self, enabled: bool):
        if enabled:
            self.auto_generate_checkbox.state(['!disabled'])
        else:
            self.auto_generate.set(False)
            self.auto_generate_checkbox.state(['disabled'])
    
    def is_auto_generate_enabled(self) -> bool:
        return self.auto_generate.get()
    
    def should_autogenerate_after_enhance(self) -> bool:
        # Simplified: always auto-generate if main auto-generate is on
        return self.auto_generate.get()
    
    def _on_text_modified(self, event):
        self.text_input.edit_modified(False)
        self.adjust_text_height()
    

    def adjust_text_height(self):
        """Adjust text widget height based on content while respecting container constraints."""
        try:
            text_content = self.text_input.get("1.0", tk.END).strip()
            if not text_content:
                text_content = " "
                
            actual_lines = max(1, text_content.count('\n') + 1)
            widget_width = self.text_input.winfo_width()
            
            if widget_width > 1:
                temp_text = tk.Text(self.input_frame, font=PROMPT_FONT, wrap='word', width=self.text_input.cget('width'))
                temp_text.insert("1.0", text_content)
                display_lines = max(1, int(temp_text.index('end-1c').split('.')[0]))
                temp_text.destroy()
                num_lines = max(actual_lines, display_lines)
            else:
                num_lines = actual_lines
            
            # Minimum height to ensure text is readable
            min_height = max(3, num_lines)
            
            # Maximum height should not exceed container height
            container_height = self.input_frame.winfo_height()
            if container_height > 0:
                # Reserve some space for padding
                max_height = max(3, container_height // 20)  # Rough estimate based on font size
            else:
                max_height = 10  # Default reasonable maximum
            
            # Final height within bounds
            new_height = max(min_height, min(num_lines, max_height))
            
            current_height = int(self.text_input.cget('height'))
            if current_height != new_height:
                self.text_input.configure(height=new_height)
        except Exception:
            pass
    
    def _on_container_resize(self):
        """Handle container resize events - called when splitter moves."""
        # Recalculate text widget height based on new container size
        self.after_idle(self.adjust_text_height)
    
    def get_text(self) -> str:
        return self.text_input.get("1.0", tk.END).strip()
    
    def set_text(self, text: str):
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert("1.0", text)
    
    def clear_text(self):
        self.text_input.delete("1.0", tk.END)
    
    def set_enhancing(self, is_enhancing: bool):
        """
        Set the enhancing state for the prompt input.
        
        When enhancing:
        - Disables enhance buttons to prevent multiple requests
        - Disables prompt text input to prevent edits during enhancement
        - Shows visual indicator that enhancement is in progress
        
        Args:
            is_enhancing: True when enhancement is in progress, False when done
        """
        if is_enhancing:
            # Disable enhance buttons
            self.enhance_btn.state(['disabled'])
            self.enhance_dir_btn.state(['disabled'])
            # Disable prompt text input to prevent edits during enhancement
            self.text_input.configure(state='disabled')
            # Update button text to show enhancing state
            self.enhance_btn.configure(text="✨ Enhancing...")
            self.enhance_dir_btn.configure(text="⏳ Please wait...")
        else:
            # Re-enable enhance buttons
            self.enhance_btn.state(['!disabled'])
            self.enhance_dir_btn.state(['!disabled'])
            # Re-enable prompt text input
            self.text_input.configure(state='normal')
            # Restore original button text
            self.enhance_btn.configure(text="✨ Auto Enhance")
            self.enhance_dir_btn.configure(text="✨ Enhance...")


class GenerationFilmstrip(tk.Frame):
    """Horizontal scrollable filmstrip showing generation queue and history."""

    ITEM_SIZE = FILMSTRIP_ITEM_SIZE
    PROMPT_TRUNCATE = FILMSTRIP_PROMPT_TRUNCATE

    def __init__(
        self,
        parent,
        tooltip_manager,
        on_item_click: Callable[[str], None],
        on_prev_unseen: Callable[[], None],
        on_next_unseen: Callable[[], None],
        on_clear_all: Callable[[], None],
        on_clear_seen: Callable[[], None],
        on_clear_failed: Callable[[], None],
    ):
        super().__init__(parent)
        self.tooltip_manager = tooltip_manager
        self.on_item_click = on_item_click
        self.on_prev_unseen = on_prev_unseen
        self.on_next_unseen = on_next_unseen
        self.on_clear_all = on_clear_all
        self.on_clear_seen = on_clear_seen
        self.on_clear_failed = on_clear_failed
        self._thumbnail_images: Dict[str, ImageTk.PhotoImage] = {}
        self._last_hash = ""
        self._create_widgets()

    def _create_widgets(self):
        bg = get_theme_color('queue_bg')
        self.configure(
            background=bg,
            highlightbackground=get_theme_color('border'),
            highlightthickness=1,
        )

        self.header_frame = tk.Frame(self, bg=bg)
        self.header_frame.pack(fill='x', padx=8, pady=(6, 4))

        scroll_container = tk.Frame(self, bg=bg)
        scroll_container.pack(fill='x', padx=8, pady=(0, 6))

        self.canvas = tk.Canvas(
            scroll_container,
            bg=bg,
            height=self.ITEM_SIZE + 10,
            highlightthickness=0,
        )
        self.h_scroll = ttk.Scrollbar(
            scroll_container,
            orient='horizontal',
            command=self.canvas.xview,
            style='Horizontal.TScrollbar',
        )
        self.canvas.configure(xscrollcommand=self.h_scroll.set)
        self.canvas.pack(side='top', fill='x', expand=True)
        self.h_scroll.pack(side='bottom', fill='x')

        self.items_frame = tk.Frame(self.canvas, bg=bg)
        self._canvas_window = self.canvas.create_window(
            (0, 0), window=self.items_frame, anchor='nw'
        )
        self.items_frame.bind('<Configure>', self._on_items_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self._bind_horizontal_scroll(self.canvas)
        self._bind_horizontal_scroll(self.items_frame)

    def _on_items_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self._canvas_window, height=event.height)

    def _bind_horizontal_scroll(self, widget):
        def on_mousewheel(event):
            if event.num == 5 or event.delta < 0:
                self.canvas.xview_scroll(1, 'units')
            elif event.num == 4 or event.delta > 0:
                self.canvas.xview_scroll(-1, 'units')

        widget.bind('<MouseWheel>', on_mousewheel)
        widget.bind('<Shift-MouseWheel>', on_mousewheel)
        widget.bind('<Button-4>', on_mousewheel)
        widget.bind('<Button-5>', on_mousewheel)

    def _format_model_name(self, model: str) -> str:
        display_name = model.replace("fal-ai/", "").replace("/", " ").title()
        return MODEL_ABBREVIATIONS.get(display_name, display_name)

    def _truncate_prompt(self, prompt: str) -> str:
        prompt = prompt.strip()
        if len(prompt) <= self.PROMPT_TRUNCATE:
            return prompt
        return prompt[: self.PROMPT_TRUNCATE - 1].rstrip() + "…"

    def _build_tooltip(self, req) -> str:
        model_name = self._format_model_name(req.model)
        return f"{model_name}\n{req.prompt}"

    def _add_link_button(self, parent, text: str, command: Callable[[], None]):
        btn = tk.Label(
            parent,
            text=text,
            font=('Segoe UI', 8),
            background=get_theme_color('queue_bg'),
            foreground=get_theme_color('link_color'),
            cursor='hand2',
        )
        btn.pack(side='left', padx=4)
        btn.bind('<Button-1>', lambda _e: command())
        self._add_hover_effect(
            btn,
            get_theme_color('link_color'),
            get_theme_color('link_hover'),
            underline=True,
        )
        return btn

    def _add_action_button(self, parent, text: str, command: Callable[[], None]):
        btn = tk.Label(
            parent,
            text=text,
            font=('Segoe UI', 8),
            background=get_theme_color('queue_bg'),
            foreground=get_theme_color('accent'),
            cursor='hand2',
        )
        btn.pack(side='right', padx=(5, 0))
        btn.bind('<Button-1>', lambda _e: command())
        self._add_hover_effect(
            btn,
            get_theme_color('accent'),
            get_theme_color('accent_hover'),
            underline=True,
        )
        return btn

    def _add_hover_effect(self, widget, normal_color, hover_color, underline=False):
        font_normal = ('Segoe UI', 8)
        font_hover = ('Segoe UI', 8, 'underline') if underline else ('Segoe UI', 8)

        widget.bind(
            '<Enter>',
            lambda _e: widget.configure(foreground=hover_color, font=font_hover),
        )
        widget.bind(
            '<Leave>',
            lambda _e: widget.configure(foreground=normal_color, font=font_normal),
        )

    def _is_viewed(self, req, model_selection, latest_completed_by_model: Dict[str, str]) -> bool:
        if req.seen:
            return True
        if model_selection is None:
            return False
        model_is_viewed = req.model in getattr(model_selection, 'models_viewed', set())
        is_latest = latest_completed_by_model.get(req.model) == req.request_id
        return model_is_viewed and is_latest

    def _compute_hash(self, requests: List, model_selection) -> str:
        parts: List[str] = [str(len(requests))]
        try:
            viewed_models = sorted(getattr(model_selection, 'models_viewed', set()))
            ticked_models = sorted(getattr(model_selection, 'models_with_ticks', set()))
        except Exception:
            viewed_models = []
            ticked_models = []
        parts.append('viewed:' + ','.join(viewed_models))
        parts.append('ticked:' + ','.join(ticked_models))
        for req in sorted(requests, key=lambda r: r.request_id):
            parts.append(f"{req.request_id}:{req.status.name}:{req.seen}")
        return '|'.join(parts)

    def update(self, requests: List, model_selection=None):
        current_hash = self._compute_hash(requests, model_selection)
        if current_hash == self._last_hash:
            return
        self._last_hash = current_hash

        bg = get_theme_color('queue_bg')
        self.configure(background=bg, highlightbackground=get_theme_color('border'))
        self.header_frame.configure(bg=bg)
        self.canvas.configure(bg=bg)
        self.items_frame.configure(bg=bg)

        for widget in self.header_frame.winfo_children():
            widget.destroy()
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self._thumbnail_images.clear()

        pending_count = sum(
            1 for r in requests
            if r.status in (RequestStatus.QUEUED, RequestStatus.PROCESSING)
        )
        title_text = f"Generations ({pending_count})" if pending_count else "Generations"
        tk.Label(
            self.header_frame,
            text=title_text,
            font=('Segoe UI', 9, 'bold'),
            background=bg,
            foreground=get_theme_color('text'),
        ).pack(side='left')

        nav_frame = tk.Frame(self.header_frame, bg=bg)
        nav_frame.pack(side='right', padx=(0, 8))
        self._add_link_button(nav_frame, 'Prev Unseen', self.on_prev_unseen)
        self._add_link_button(nav_frame, 'Next Unseen', self.on_next_unseen)

        btn_frame = tk.Frame(self.header_frame, bg=bg)
        btn_frame.pack(side='right')
        finished = [
            r for r in requests
            if r.status in (RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.CANCELLED)
        ]
        if finished:
            self._add_action_button(btn_frame, 'Clear All', self.on_clear_all)
            if any(r.seen for r in requests):
                self._add_action_button(btn_frame, 'Clear Seen', self.on_clear_seen)
        if any(r.status == RequestStatus.FAILED for r in requests):
            self._add_action_button(btn_frame, 'Clear Failed', self.on_clear_failed)

        sorted_items = sorted(requests, key=lambda r: r.created_at, reverse=True)
        latest_completed_by_model: Dict[str, str] = {}
        for req in sorted_items:
            if req.status == RequestStatus.COMPLETED and req.model not in latest_completed_by_model:
                latest_completed_by_model[req.model] = req.request_id

        if not sorted_items:
            empty_label = tk.Label(
                self.items_frame,
                text="No generations yet",
                font=('Segoe UI', 9),
                background=bg,
                foreground=get_theme_color('status_pending'),
            )
            empty_label.pack(side='left', padx=4, pady=4)
            self.tooltip_manager.add_tooltip(empty_label, 'Generated images will appear here')
            return

        for req in sorted_items:
            self._create_tile(req, model_selection, latest_completed_by_model, bg)

    def _create_tile(self, req, model_selection, latest_completed_by_model, bg):
        is_unseen_completed = (
            req.status == RequestStatus.COMPLETED
            and not self._is_viewed(req, model_selection, latest_completed_by_model)
        )
        border_color = get_theme_color('accent') if is_unseen_completed else get_theme_color('border')

        tile = tk.Frame(
            self.items_frame,
            bg=border_color,
            width=self.ITEM_SIZE + 4,
            height=self.ITEM_SIZE + 4,
        )
        tile.pack(side='left', padx=3, pady=2)
        tile.pack_propagate(False)

        inner = tk.Frame(tile, bg=bg, width=self.ITEM_SIZE, height=self.ITEM_SIZE)
        inner.place(relx=0.5, rely=0.5, anchor='center')
        inner.pack_propagate(False)

        tooltip_text = self._build_tooltip(req)
        tooltip_widgets = [tile, inner]

        if req.status in (RequestStatus.QUEUED, RequestStatus.PROCESSING):
            prompt_label = tk.Label(
                inner,
                text=self._truncate_prompt(req.prompt),
                font=('Segoe UI', 8),
                background=bg,
                foreground=get_theme_color('status_processing'),
                wraplength=self.ITEM_SIZE - 8,
                justify='center',
            )
            prompt_label.pack(expand=True, fill='both', padx=4, pady=4)
            tooltip_widgets.append(prompt_label)
        elif req.status == RequestStatus.COMPLETED:
            thumb_source = req.result_image
            if thumb_source:
                try:
                    thumb_img = thumb_source.copy()
                    thumb_img.thumbnail((self.ITEM_SIZE, self.ITEM_SIZE), Image.LANCZOS)
                    thumb_photo = ImageTk.PhotoImage(thumb_img)
                    self._thumbnail_images[req.request_id] = thumb_photo
                    thumb_label = tk.Label(
                        inner,
                        image=thumb_photo,
                        background=bg,
                        cursor='hand2',
                    )
                    thumb_label.pack(expand=True)
                    tooltip_widgets.append(thumb_label)
                    thumb_label.bind(
                        '<Button-1>',
                        lambda _e, rid=req.request_id: self.on_item_click(rid),
                    )
                    self._bind_tile_hover(inner, thumb_label, bg)
                except Exception:
                    self._create_fallback_label(inner, '✓', get_theme_color('status_success'), tooltip_widgets)
            else:
                self._create_fallback_label(inner, '✓', get_theme_color('status_success'), tooltip_widgets)
        elif req.status == RequestStatus.FAILED:
            self._create_fallback_label(inner, '✕', get_theme_color('status_error'), tooltip_widgets, font_size=22)
        elif req.status == RequestStatus.CANCELLED:
            self._create_fallback_label(inner, '⊘', get_theme_color('status_cancelled'), tooltip_widgets, font_size=18)
        else:
            self._create_fallback_label(inner, '?', get_theme_color('text'), tooltip_widgets)

        self.tooltip_manager.set_tooltip_region(tooltip_widgets, tooltip_text)

    def _create_fallback_label(self, parent, text, color, tooltip_widgets, font_size=16):
        label = tk.Label(
            parent,
            text=text,
            font=('Segoe UI', font_size, 'bold'),
            background=get_theme_color('queue_bg'),
            foreground=color,
        )
        label.pack(expand=True)
        tooltip_widgets.append(label)

    def _bind_tile_hover(self, inner, label, bg):
        highlight = get_theme_color('queue_highlight')

        def on_enter(_event):
            inner.configure(background=highlight)
            label.configure(background=highlight)

        def on_leave(_event):
            inner.configure(background=bg)
            label.configure(background=bg)

        label.bind('<Enter>', on_enter, add='+')
        label.bind('<Leave>', on_leave, add='+')

    def apply_theme(self):
        self._last_hash = ""


class TooltipManager:
    """Manages tooltip functionality for UI elements."""
    
    def __init__(self):
        """Initialize the tooltip manager."""
        self.active_tooltips = {}
    
    def add_tooltip(self, widget, text: str):
        """
        Add a tooltip to a widget.
        
        Args:
            widget: The tkinter widget to add tooltip to
            text: The tooltip text
        """
        self.set_tooltip(widget, text)

    def set_tooltip(self, widget, text: str):
        """Set or update tooltip text for a single widget."""
        self.set_tooltip_region([widget], text)

    def set_tooltip_region(self, widgets, text: str):
        """Set or update tooltip text for one or more widgets treated as a hover region."""
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
                background="#ffffe0",
                relief='solid',
                borderwidth=1,
                wraplength=400,
                justify='left',
            )
            label.pack()

            anchor.tooltip = tooltip

        def try_hide():
            pending_hide[0] = None
            if hover_count[0] <= 0:
                destroy_tooltip()

        def on_enter(event):
            hover_count[0] += 1
            cancel_pending_hide()
            show_tooltip()

        def on_leave(event):
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
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip
        widget.unbind('<Enter>')
        widget.unbind('<Leave>')
        widget._tooltip_bound = False
        if hasattr(widget, '_tooltip_text'):
            del widget._tooltip_text
