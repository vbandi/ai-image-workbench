"""
UI Components module for the Image Generator application.
Contains specialized UI components for model selection, controls, and prompt input.
"""

import tkinter as tk
from tkinter import ttk, simpledialog
from typing import Optional, Callable, Dict, Any
from config import (
    MODEL_CATEGORIES, MODEL_ABBREVIATIONS, SPINNER_FRAMES,
    BACKGROUND_COLOR, SELECTED_BUTTON_COLOR, HOVER_BUTTON_COLOR,
    ACTIVE_BUTTON_COLOR, BASE_FONT, BUTTON_FONT, BUTTON_BOLD_FONT
)


class ModelSelectionFrame(ttk.Frame):
    """Frame for model selection with categorized buttons."""
    
    def __init__(self, parent, on_model_select: Callable[[str, bool], None], default_model: str):
        """Initialize the model selection frame."""
        super().__init__(parent)
        self.on_model_select = on_model_select
        self.model_var = tk.StringVar(value=default_model)
        self.model_buttons: Dict[str, ttk.Button] = {}
        self.star_buttons: Dict[str, ttk.Button] = {}
        self.model_button_texts: Dict[str, str] = {}  # Store original button text
        self.models_with_ticks: set = set()  # Track which models have generated images
        self.models_generating: set = set()  # Track which models are currently generating (hourglass)
        self.starred_models: set = set()
        self.model_order = []  # Preserve insertion order for starred models retrieval
        self.tooltip_manager = TooltipManager()
        
        # Create the label frame
        self.labelframe = ttk.LabelFrame(parent, text="Model Selection", padding=(10, 5))
        self.labelframe.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        self.labelframe.grid_columnconfigure(0, weight=1)
        
        # Create model matrix frame
        self.model_matrix_frame = ttk.Frame(self.labelframe)
        self.model_matrix_frame.grid(row=0, column=0, sticky="ew")
        self.model_matrix_frame.grid_columnconfigure(0, weight=1)
        
        self.create_model_matrix()
        self.configure_styles()
    
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
        
        # Set default background for frames and labels to a light neutral color
        style.configure('TFrame', background=BACKGROUND_COLOR)
        style.configure('TLabel', background=BACKGROUND_COLOR)
        
        # Configure selected button style
        style.configure('Model.Selected.TButton',
                       background=SELECTED_BUTTON_COLOR,
                       foreground='black',
                       relief='sunken',
                       padding=(8, 4),
                       font=BUTTON_BOLD_FONT)
                       
        # Configure normal button style
        style.configure('Model.TButton',
                       padding=(8, 4),
                       relief='raised',
                       font=BUTTON_FONT)
                       
        # Configure hover effects
        style.map('Model.TButton',
                 background=[('active', HOVER_BUTTON_COLOR), ('!active', '#F0F0F0')])
        style.map('Model.Selected.TButton',
                 background=[('active', ACTIVE_BUTTON_COLOR), ('!active', SELECTED_BUTTON_COLOR)],
                 foreground=[('!disabled', 'black')])

        # Configure star toggle buttons
        style.configure('Star.TButton',
                padding=(4, 2),
                width=2,
                font=BUTTON_FONT)
        style.configure('Star.Selected.TButton',
                padding=(4, 2),
                width=2,
                font=BUTTON_BOLD_FONT,
                foreground='#c58b00')
        style.map('Star.TButton',
              background=[('active', HOVER_BUTTON_COLOR), ('!active', '#F0F0F0')])
        style.map('Star.Selected.TButton',
              background=[('active', ACTIVE_BUTTON_COLOR), ('!active', '#FBE7B2')])
    
    def create_model_matrix(self):
        """Create a vertical list of model selection buttons organized by category."""
        row = 0
        for category, models in MODEL_CATEGORIES.items():
            # Create category label
            category_label = ttk.Label(
                self.model_matrix_frame,
                text=category,
                font=('Arial', 10, 'bold'),
                background=BACKGROUND_COLOR
            )
            category_label.grid(row=row, column=0, sticky="w", padx=2, pady=(10, 2))
            row += 1
            
            # Create buttons for each model in this category, stacked vertically
            for model in models:
                # Create a shorter display name for the button
                display_name = model.replace("fal-ai/", "").replace("/", " ").title()

                # Use abbreviation if available, otherwise use the cleaned-up name
                display_name = MODEL_ABBREVIATIONS.get(display_name, display_name)

                # Track order for deterministic starred model retrieval
                self.model_order.append(model)

                # Store the original text for this model
                self.model_button_texts[model] = display_name

                # Create a container row for star toggle and model button
                row_frame = ttk.Frame(self.model_matrix_frame)
                row_frame.grid(row=row, column=0, padx=2, pady=2, sticky="ew")
                row_frame.grid_columnconfigure(1, weight=1)

                # Star toggle button sits on the left
                star_btn = ttk.Button(
                    row_frame,
                    command=lambda m=model: self.toggle_star(m),
                    style='Star.TButton'
                )
                star_btn.grid(row=0, column=0, padx=(0, 4))
                self.tooltip_manager.add_tooltip(star_btn, "Star model for parallel generation")
                self.star_buttons[model] = star_btn

                # Model selection button
                btn = ttk.Button(
                    row_frame,
                    text=display_name,
                    command=lambda m=model: self.select_model(m),
                    style='Model.TButton'
                )
                btn.grid(row=0, column=1, sticky="ew")

                # Add tooltip with full model name
                full_name = model.replace("fal-ai/", "").replace("/", " ").title()
                self.tooltip_manager.add_tooltip(btn, full_name)

                self.model_buttons[model] = btn

                # Configure button style based on selection
                if model == self.model_var.get():
                    btn.configure(style='Model.Selected.TButton')

                # Initialize the star button state
                self._update_star_button(model)

                row += 1
        
        # Configure column weights for responsive layout
        self.model_matrix_frame.grid_columnconfigure(0, weight=1)
    
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
        if model not in self.models_with_ticks:
            self.models_with_ticks.add(model)
        self._update_button_text(model)
    
    def clear_all_ticks(self):
        """Clear all tick marks from model buttons."""
        self.models_with_ticks.clear()
        for model in self.model_buttons:
            self._update_button_text(model)
    
    def set_model_generating(self, model: str):
        """Mark a model as currently generating (show hourglass, remove tick)."""
        # When generating, ensure no tick is shown for this model
        if model in self.models_with_ticks:
            self.models_with_ticks.discard(model)
        self.models_generating.add(model)
        self._update_button_text(model)
    
    def clear_model_generating(self, model: str):
        """Clear generating indicator (hourglass) for a model."""
        if model in self.models_generating:
            self.models_generating.discard(model)
            self._update_button_text(model)
    
    def clear_all_generating(self):
        """Clear all generating indicators (hourglasses)."""
        if self.models_generating:
            self.models_generating.clear()
            for model in self.model_buttons:
                self._update_button_text(model)
    
    def _update_button_text(self, model: str):
        """Update button text to show/hide tick mark."""
        if model in self.model_buttons:
            base_text = self.model_button_texts.get(model, "")
            # Priority: generating hourglass over tick
            if model in self.models_generating:
                # Hourglass to indicate in-progress
                new_text = f"⏳ {base_text}"
            elif model in self.models_with_ticks:
                # Add checkmark/tick
                new_text = f"✓ {base_text}"
            else:
                new_text = base_text
            self.model_buttons[model].configure(text=new_text)

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


class ControlPanel(ttk.Frame):
    """Control panel with generate button, auto-generate checkbox, and progress bar."""
    
    def __init__(self, parent, on_generate: Callable[[], None], on_auto_generate_change: Callable[[bool], None]):
        """Initialize the control panel."""
        super().__init__(parent)
        self.on_generate = on_generate
        self.on_auto_generate_change = on_auto_generate_change
        self.auto_generate = tk.BooleanVar(value=True)
        
        # Create controls labelframe
        self.labelframe = ttk.LabelFrame(parent, text="Controls", padding=(10, 5))
        self.labelframe.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        
        # Create controls frame
        self.controls_frame = ttk.Frame(self.labelframe)
        self.controls_frame.grid(row=0, column=0, sticky="ew")
        
        # Create Generate button
        self.generate_button = ttk.Button(
            self.controls_frame, 
            text="Generate", 
            command=self.on_generate
        )
        self.generate_button.grid(row=0, column=0, padx=(0, 8))
        
        # Create auto-generate checkbox
        self.auto_checkbox = ttk.Checkbutton(
            self.controls_frame, 
            text="Auto-generate", 
            variable=self.auto_generate,
            command=self._on_auto_generate_toggle
        )
        self.auto_checkbox.grid(row=0, column=1, padx=(0, 5))
        
        # Create progress bar for loading state
        self.progress_bar = ttk.Progressbar(self.controls_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=2, padx=(8, 0), sticky="ew")
        
        # Configure grid weights
        self.controls_frame.grid_columnconfigure(2, weight=1)
    
    def _on_auto_generate_toggle(self):
        """Handle auto-generate checkbox toggle."""
        self.on_auto_generate_change(self.auto_generate.get())
    
    def set_auto_generate_enabled(self, enabled: bool):
        """Enable or disable auto-generate functionality."""
        if enabled:
            self.auto_checkbox.state(['!disabled'])
        else:
            self.auto_generate.set(False)
            self.auto_checkbox.state(['disabled'])
    
    def is_auto_generate_enabled(self) -> bool:
        """Check if auto-generate is enabled."""
        return self.auto_generate.get()
    
    def start_progress(self):
        """Start the progress bar animation."""
        self.progress_bar.start(10)
    
    def stop_progress(self):
        """Stop the progress bar animation."""
        self.progress_bar.stop()


class PromptInputFrame(ttk.Frame):
    """Frame for prompt input with auto-resizing text widget."""
    
    def __init__(self, parent, on_text_change: Callable[[tk.Event], None], on_enter: Callable[[tk.Event], Any],
                 on_enhance: Callable[[], None], on_enhance_with_directions: Callable[[], None],
                 on_generate: Callable[[], None], on_parallel_generate: Callable[[], None],
                 on_save: Callable[[], None], on_copy: Callable[[], None]):
        """Initialize the prompt input frame."""
        super().__init__(parent)
        self.on_text_change = on_text_change
        self.on_enter = on_enter
        self.on_enhance = on_enhance
        self.on_enhance_with_directions = on_enhance_with_directions
        self.on_generate = on_generate
        self.on_parallel_generate = on_parallel_generate
        self.on_save = on_save
        self.on_copy = on_copy
        
        # Create prompt labelframe
        self.labelframe = ttk.LabelFrame(parent, text="Prompt", padding=(10, 5))
        self.labelframe.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        self.labelframe.grid_columnconfigure(0, weight=1)
        
        # Create input frame for textbox
        self.input_frame = ttk.Frame(self.labelframe)
        self.input_frame.grid(row=0, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        
        # Create and place the text input using Text widget
        self.text_input = tk.Text(
            self.input_frame,
            height=2,
            font=('Arial', 12),
            wrap='word'
        )
        self.text_input.grid(row=0, column=0, sticky="ew", pady=(3, 3))
        
        # Create a frame for the buttons below the text area
        self.button_frame = ttk.Frame(self.labelframe)
        self.button_frame.grid(row=1, column=0, sticky="ew", pady=(0, 3))
        
        # Create buttons
        self._create_buttons()
        
        # Bind text changes and events
        self.text_input.bind('<KeyRelease>', self.on_text_change)
        self.text_input.bind('<<Modified>>', self._on_text_modified)
        self.text_input.bind('<Return>', self.on_enter)
        self.text_input.bind('<Configure>', lambda e: self.after_idle(self.adjust_text_height))
        
        # Initialize auto-expanding text widget
        self.adjust_text_height()
    
    def _create_buttons(self):
        """Create all buttons in the button frame in a horizontal layout."""
        # Configure columns to distribute buttons evenly
        for i in range(7):
            self.button_frame.grid_columnconfigure(i, weight=1)
        
        # --- Enhance Frame with button and checkbox ---
        self.enhance_frame = ttk.Frame(self.button_frame)
        self.enhance_frame.grid(row=0, column=0, sticky="ew", padx=(0, 3))
        
        self.enhance_button = ttk.Button(
            self.enhance_frame,
            text="Enhance",
            command=self.on_enhance
        )
        self.enhance_button.pack(side="left", fill="x", expand=True)
        
        self.autogenerate_after_enhance = tk.BooleanVar(value=True)
        self.autogenerate_checkbox = ttk.Checkbutton(
            self.enhance_frame,
            text="Auto",
            variable=self.autogenerate_after_enhance
        )
        self.autogenerate_checkbox.pack(side="left", padx=(3, 0))
        # --- End Enhance Frame ---
        
        # Create Enhance with directions button
        self.enhance_with_directions_button = ttk.Button(
            self.button_frame,
            text="Enhance...",
            command=self.on_enhance_with_directions
        )
        self.enhance_with_directions_button.grid(row=0, column=1, sticky="ew", padx=3)
        
        # Create Generate button
        self.generate_button = ttk.Button(
            self.button_frame,
            text="Generate",
            command=self.on_generate
        )
        self.generate_button.grid(row=0, column=2, sticky="ew", padx=3)

        # Create Parallel Generate button
        self.parallel_generate_button = ttk.Button(
            self.button_frame,
            text="Generate ★",
            command=self.on_parallel_generate
        )
        self.parallel_generate_button.grid(row=0, column=3, sticky="ew", padx=3)
        
        # --- Auto-generate Frame with checkbox ---
        self.auto_frame = ttk.Frame(self.button_frame)
        self.auto_frame.grid(row=0, column=4, sticky="ew", padx=3)
        
        self.auto_generate = tk.BooleanVar(value=True)
        self.auto_generate_checkbox = ttk.Checkbutton(
            self.auto_frame,
            text="Auto-generate",
            variable=self.auto_generate
        )
        self.auto_generate_checkbox.pack(fill="x", expand=True)
        # --- End Auto-generate Frame ---
        
        # Create Save button
        self.save_button = ttk.Button(
            self.button_frame,
            text="Save",
            command=self.on_save
        )
        self.save_button.grid(row=0, column=5, sticky="ew", padx=3)
        
        # Create Copy button
        self.copy_button = ttk.Button(
            self.button_frame,
            text="Copy",
            command=self.on_copy
        )
        self.copy_button.grid(row=0, column=6, sticky="ew", padx=(3, 0))
    
    def set_auto_generate_enabled(self, enabled: bool):
        """Enable or disable auto-generate functionality."""
        if enabled:
            self.auto_generate_checkbox.state(['!disabled'])
        else:
            self.auto_generate.set(False)
            self.auto_generate_checkbox.state(['disabled'])
    
    def is_auto_generate_enabled(self) -> bool:
        """Check if auto-generate is enabled."""
        return self.auto_generate.get()
    
    def should_autogenerate_after_enhance(self) -> bool:
        """Check if auto-generate after enhance is enabled."""
        return self.autogenerate_after_enhance.get()
    
    def _on_text_modified(self, event):
        """Handle text modification events."""
        # Reset the modified flag
        self.text_input.edit_modified(False)
        # Adjust text height
        self.adjust_text_height()
    
    def adjust_text_height(self):
        """Automatically adjust the height of the text widget based on content."""
        try:
            # Get the text content
            text_content = self.text_input.get("1.0", tk.END)
            
            # Count actual newlines in the text
            actual_lines = text_content.count('\n') + 1
            
            # Get the current width of the text widget in pixels
            widget_width = self.text_input.winfo_width()
            
            if widget_width > 1:  # Make sure widget is rendered
                # Create a temporary text widget to measure line count with wrapping
                temp_text = tk.Text(self.input_frame, font=('Arial', 12), wrap='word', width=self.text_input.cget('width'))
                temp_text.insert("1.0", text_content)
                
                # Get the number of display lines (accounting for word wrap)
                display_lines = int(temp_text.index('end-1c').split('.')[0])
                
                # Clean up temp widget
                temp_text.destroy()
                
                # Use the maximum of actual lines and display lines
                num_lines = max(actual_lines, display_lines)
            else:
                # Fallback to simple line counting if widget not yet rendered
                num_lines = actual_lines
            
            # Set minimum height (in lines)
            min_height = 2
            
            # Calculate final height (without maximum limit)
            new_height = max(min_height, num_lines)
            
            # Only update if height has changed
            current_height = int(self.text_input.cget('height'))
            if new_height != current_height:
                self.text_input.configure(height=new_height)
                # Update the frame layout
                self.input_frame.update_idletasks()
                
        except Exception as e:
            # Fallback to simple line counting if measurement fails
            actual_lines = self.text_input.get("1.0", tk.END).count('\n') + 1
            min_height = 2
            new_height = max(min_height, actual_lines)
            
            current_height = int(self.text_input.cget('height'))
            if new_height != current_height:
                self.text_input.configure(height=new_height)
    
    def get_text(self) -> str:
        """Get the current text content."""
        return self.text_input.get("1.0", tk.END).strip()
    
    def set_text(self, text: str):
        """Set the text content."""
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert("1.0", text)
    
    def clear_text(self):
        """Clear all text."""
        self.text_input.delete("1.0", tk.END)


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
        def show_tooltip(event):
            # Calculate tooltip position
            try:
                x, y, _, _ = widget.bbox("insert")
                x += widget.winfo_rootx() + 25
                y += widget.winfo_rooty() + 25
            except:
                # Fallback for widgets that don't support bbox
                x = widget.winfo_rootx() + 25
                y = widget.winfo_rooty() + 25
            
            # Create tooltip window
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            # Create label with tooltip text
            label = tk.Label(tooltip, text=text, background="#ffffe0", relief='solid', borderwidth=1)
            label.pack()
            
            # Store reference to tooltip
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        # Bind mouse events
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def remove_tooltip(self, widget):
        """Remove tooltip from a widget."""
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip
        widget.unbind('<Enter>')
        widget.unbind('<Leave>')