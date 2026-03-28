import tkinter as tk
from tkinter import ttk, simpledialog, filedialog
from PIL import Image, ImageTk
import io
import sys
import ctypes
from ctypes import wintypes
import threading
import queue
import time
from typing import Optional

from ai_api import enhance_prompt
from image_gen_api import generate_image, MODELS


class ImageGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Image Workbench")
        
        # Available models
        self.models = MODELS
        
        # Categorize models by type
        self.model_categories = {
            "Flux": [
                "fal-ai/flux/schnell",
                "fal-ai/flux-1/srpo",
                "fal-ai/flux-pro/v1.1",
                "fal-ai/flux-pro/v1.1-ultra"
            ],
            "HiDream": [
                "fal-ai/hidream-i1-fast",
                "fal-ai/hidream-i1-dev",
                "fal-ai/hidream-i1-full"
            ],
            "Imagen": [
                "fal-ai/imagen4/preview",
                "fal-ai/imagen4/preview/fast",
                "fal-ai/imagen4/preview/ultra"
            ],
            "Other": [
                "fal-ai/stable-diffusion-v35-large",
                "fal-ai/stable-diffusion-v35-medium",
                "fal-ai/ideogram/v2",
                "fal-ai/recraft-20b",
                "fal-ai/sana",
                "fal-ai/luma-photon",
                "fal-ai/bytedance/seedream/v3/text-to-image",
                "fal-ai/bytedance/seedream/v4/text-to-image",
                "fal-ai/wan/v2.2-5b/text-to-image",
                "fal-ai/gemini-25-flash-image"
            ]
        }
        
        # Spinner animation frames
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0
        self.spinner_after_id = None
        
        # Set minimum window size
        self.root.minsize(1000, 600)
        
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        self.main_frame = ttk.Frame(root)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(4, weight=1)  # Make image row expandable
        
        # --- Controls Section ---
        controls_labelframe = ttk.LabelFrame(self.main_frame, text="Controls", padding=(10, 5))
        controls_labelframe.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        
        # Create controls frame
        self.controls_frame = ttk.Frame(controls_labelframe)
        self.controls_frame.grid(row=0, column=0, sticky="ew")
        
        # --- Model Selection Section ---
        model_labelframe = ttk.LabelFrame(self.main_frame, text="Model Selection", padding=(10, 5))
        model_labelframe.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        model_labelframe.grid_columnconfigure(0, weight=1)
        
        # Create model matrix frame
        self.model_matrix_frame = ttk.Frame(model_labelframe)
        self.model_matrix_frame.grid(row=0, column=0, sticky="ew")
        self.model_matrix_frame.grid_columnconfigure(0, weight=1)
        
        # Create model selection variable and button matrix
        self.model_var = tk.StringVar(value="fal-ai/flux/schnell")  # Default to Flux Schnell
        self.model_buttons = {}
        self.create_model_matrix()
        
        # Add a separator
        ttk.Separator(self.main_frame, orient='horizontal').grid(row=2, column=0, sticky="ew", padx=8, pady=5)
        
        # --- Prompt Section ---
        prompt_labelframe = ttk.LabelFrame(self.main_frame, text="Prompt", padding=(10, 5))
        prompt_labelframe.grid(row=3, column=0, sticky="ew", padx=8, pady=4)
        prompt_labelframe.grid_columnconfigure(0, weight=1)
        
        # Create Generate button in controls frame
        self.controls_generate_button = ttk.Button(self.controls_frame, text="Generate", command=self.manual_generate)
        self.controls_generate_button.grid(row=0, column=0, padx=(0, 8))
        
        # Create auto-generate checkbox
        self.auto_generate = tk.BooleanVar(value=True)
        self.auto_checkbox = ttk.Checkbutton(self.controls_frame, text="Auto-generate", variable=self.auto_generate)
        self.auto_checkbox.grid(row=0, column=1, padx=(0, 5))
        
        # Create progress bar for loading state
        self.progress_bar = ttk.Progressbar(self.controls_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=2, padx=(8, 0), sticky="ew")
        
        # --- Prompt Section ---
        prompt_labelframe = ttk.LabelFrame(self.main_frame, text="Prompt", padding=(10, 5))
        prompt_labelframe.grid(row=3, column=0, sticky="ew", padx=8, pady=4)
        prompt_labelframe.grid_columnconfigure(0, weight=1)
        
        # Create Generate button in controls frame
        self.controls_generate_button = ttk.Button(self.controls_frame, text="Generate", command=self.manual_generate)
        self.controls_generate_button.grid(row=0, column=0, padx=(0, 8))
        
        # Create auto-generate checkbox
        self.auto_generate = tk.BooleanVar(value=True)
        self.auto_checkbox = ttk.Checkbutton(self.controls_frame, text="Auto-generate", variable=self.auto_generate)
        self.auto_checkbox.grid(row=0, column=1, padx=(0, 5))
        
        # Create progress bar for loading state
        self.progress_bar = ttk.Progressbar(self.controls_frame, mode='indeterminate')
        self.progress_bar.grid(row=0, column=2, padx=(8, 0), sticky="ew")
        
        # Create input frame for textbox and Generate button
        self.input_frame = ttk.Frame(prompt_labelframe)
        self.input_frame.grid(row=0, column=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        # Configure row weights to allow vertical expansion
        self.input_frame.grid_rowconfigure(0, weight=1)
        
        # Create and place the text input using Text widget
        self.text_input = tk.Text(self.input_frame, height=2, font=('Arial', 12), wrap='word')
        self.text_input.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=3)
        
        # Create a frame for the buttons
        self.button_frame = ttk.Frame(self.input_frame)
        self.button_frame.grid(row=0, column=1, sticky="ns", pady=3)
        
        # Bind text changes to auto-adjust height
        self.text_input.bind('<KeyRelease>', self.on_text_change)
        self.text_input.bind('<<Modified>>', self.on_text_modified)
        # Bind to window resize to recalculate text height
        self.text_input.bind('<Configure>', lambda e: self.root.after_idle(self.adjust_text_height))

        # --- Enhance Frame ---
        self.enhance_frame = ttk.Frame(self.button_frame)
        self.enhance_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
        
        self.enhance_button = ttk.Button(self.enhance_frame, text="Enhance", command=self.enhance_prompt)
        self.enhance_button.pack(side="left", fill="x", expand=True)

        self.autogenerate_after_enhance = tk.BooleanVar(value=True)
        self.autogenerate_checkbox = ttk.Checkbutton(self.enhance_frame, text="Auto", variable=self.autogenerate_after_enhance)
        self.autogenerate_checkbox.pack(side="left", padx=(3,0))
        # --- End Enhance Frame ---

        # Create Enhance Prompt with directions button
        self.enhance_with_directions_button = ttk.Button(self.button_frame, text="Enhance...", command=self.enhance_prompt_with_directions)
        self.enhance_with_directions_button.grid(row=1, column=0, sticky="ew", pady=(0, 3))

        # Create Generate button
        self.generate_button = ttk.Button(self.button_frame, text="Generate", command=self.manual_generate)
        self.generate_button.grid(row=2, column=0, sticky="ew")
        
        # Create Save button
        self.save_button = ttk.Button(self.button_frame, text="Save", command=self.save_image)
        self.save_button.grid(row=3, column=0, sticky="ew", pady=(3, 0))

        # Create Copy button
        self.copy_button = ttk.Button(self.button_frame, text="Copy", command=self.copy_image_to_clipboard)
        self.copy_button.grid(row=4, column=0, sticky="ew", pady=(3, 0))
        
        # Create frame for image to enable proper centering and expansion
        self.image_frame = ttk.Frame(self.main_frame)
        self.image_frame.grid(row=4, column=0, sticky="nsew", padx=8, pady=8)
        self.image_frame.grid_columnconfigure(0, weight=1)
        self.image_frame.grid_rowconfigure(0, weight=1)
        
        # Create label for image display
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.grid(row=0, column=0, sticky="nsew")
        
        # --- Footer / Status Bar ---
        self.footer_frame = ttk.Frame(self.main_frame, style='Footer.TFrame')
        self.footer_frame.grid(row=5, column=0, sticky="ew")
        self.footer_frame.grid_columnconfigure(0, weight=1)
        
        # Create status label
        self.status_label = ttk.Label(self.footer_frame, text="Ready", style='Footer.TLabel')
        self.status_label.grid(row=0, column=0, padx=8, pady=3, sticky="w")
        
        # Bind key events and window resize
        self.text_input.bind('<KeyRelease>', self.on_key_release)
        self.text_input.bind('<Return>', self.on_enter)
        self.root.bind('<Configure>', self.on_window_resize)
        # Bind Ctrl+C to copy image (but respect text widgets)
        self.root.bind_all('<Control-c>', self.on_copy_shortcut)
        self.root.bind_all('<Control-C>', self.on_copy_shortcut)
        
        # Initialize auto-expanding text widget
        self.adjust_text_height()
        
        # Initialize state variables
        self.is_generating = False
        self.prompt_queue = queue.Queue()
        self.current_thread: Optional[threading.Thread] = None
        self.current_image: Optional[Image.Image] = None
        
        # Zoom and pan state
        self.zoom_level = 1.0
        self.view_offset_x = 0
        self.view_offset_y = 0
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.update_job = None
        self.update_queue = queue.Queue()
        self.display_queue = queue.Queue()
        self.update_thread = None

        # Bind mouse events for zoom and pan
        self.image_label.bind("<MouseWheel>", self.zoom_image)  # For Windows and MacOS
        self.image_label.bind("<Button-4>", self.zoom_image)    # For Linux (scroll up)
        self.image_label.bind("<Button-5>", self.zoom_image)    # For Linux (scroll down)
        self.image_label.bind("<ButtonPress-1>", self.start_pan)
        self.image_label.bind("<B1-Motion>", self.pan_image)

        # Configure custom button styles
        self.configure_styles()
        
        self.start_update_thread()
        self.check_display_queue()
    
    def add_tooltip(self, widget, text):
        """Add a tooltip to a widget"""
        def show_tooltip(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # Create tooltip window
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            # Create label with tooltip text
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief='solid', borderwidth=1)
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
    
    def configure_styles(self):
        """Configure custom styles for model selection buttons and overall theme."""
        style = ttk.Style()
        # Use a modern theme (clam) for a consistent look across platforms
        try:
            style.theme_use('clam')
        except Exception:
            # Fallback if theme not available
            pass
        # Set base font for all ttk widgets
        base_font = ('Arial', 10)
        style.configure('.', font=base_font)
        # Set default background for frames and labels to a light neutral color
        style.configure('TFrame', background='#f5f5f5')
        style.configure('TLabel', background='#f5f5f5')
        
        # --- Footer Style ---
        style.configure('Footer.TFrame', background='#e0e0e0')
        style.configure('Footer.TLabel', background='#e0e0e0')
        
        # Configure selected button style
        style.configure('Model.Selected.TButton',
                       background='#C7E0F4',  # Light blue
                       foreground='black',
                       relief='sunken',
                       padding=(8, 4),
                       font=('Arial', 9, 'bold'))
        # Configure normal button style
        style.configure('Model.TButton',
                       padding=(8, 4),
                       relief='raised',
                       font=('Arial', 9))
        # Configure hover effects
        style.map('Model.TButton',
                 background=[('active', '#E6F3FF'), ('!active', '#F0F0F0')])
        style.map('Model.Selected.TButton',
                 background=[('active', '#A9D0F5'), ('!active', '#C7E0F4')],
                 foreground=[('!disabled', 'black')])

    def start_update_thread(self):
        self.update_thread = threading.Thread(target=self.process_updates, daemon=True)
        self.update_thread.start()

    def process_updates(self):
        while True:
            try:
                # Wait for the latest update request
                update_params = self.update_queue.get()
                while not self.update_queue.empty():
                    update_params = self.update_queue.get()

                photo = self.create_photo_image(update_params)
                if photo:
                    self.display_queue.put(photo)
            except Exception as e:
                print(f"Error in update thread: {e}")

    def check_display_queue(self):
        try:
            while not self.display_queue.empty():
                photo = self.display_queue.get_nowait()
                self.image_label.configure(image=photo)
                self.image_label.image = photo  # type: ignore
        finally:
            self.root.after(30, self.check_display_queue)

    def enhance_prompt(self, directions: Optional[str] = None):
        """Enhance the prompt using AI API."""
        current_prompt = self.text_input.get("1.0", tk.END).strip()
        if not current_prompt:
            self.status_label.config(text="Please enter a prompt to enhance.")
            return

        try:
            self.status_label.config(text="Enhancing prompt with AI...")
            enhanced_prompt = enhance_prompt(current_prompt, directions=directions)
            
            self.text_input.delete("1.0", tk.END)
            self.text_input.insert("1.0", enhanced_prompt)
            self.status_label.config(text="Prompt enhanced successfully.")

            if self.autogenerate_after_enhance.get():
                self.manual_generate()
        except Exception as e:
            self.status_label.config(text=f"Error enhancing prompt: {e}")

    def enhance_prompt_with_directions(self):
        """Ask for directions and then enhance the prompt."""
        directions = simpledialog.askstring("Enhancement Directions", "Enter directions for the enhancement:", parent=self.root)
        if directions:
            self.enhance_prompt(directions=directions)
        
    def update_spinner(self):
        if self.is_generating:
            self.progress_bar.start(10) # Start indeterminate progress bar
        else:
            self.progress_bar.stop() # Stop progress bar
            
    def create_model_matrix(self):
        """Create a responsive matrix of model selection buttons organized by category."""
        row = 0
        for category, models in self.model_categories.items():
            # Create button frame for this category with better layout
            button_frame = ttk.Frame(self.model_matrix_frame)
            button_frame.grid(row=row, column=0, sticky="ew", padx=2, pady=2)
            
            # Configure grid columns to distribute space evenly
            for i in range(len(models)):
                button_frame.grid_columnconfigure(i, weight=1, uniform="model_button")
            
            # Create buttons for each model in this category
            for i, model in enumerate(models):
                # Create a shorter display name for the button
                display_name = model.replace("fal-ai/", "").replace("/", " ").title()
                
                # Comprehensive abbreviation system
                abbreviations = {
                    # Flux Models
                    "Flux Schnell": "Flux Schnell",
                    "Flux 1 Srpo": "Flux SRPO",
                    "Flux Pro V1.1": "Flux Pro",
                    "Flux Pro V1.1 Ultra": "Flux Pro Ultra",
                    # Imagen Models
                    "Imagen4 Preview": "Imagen4",
                    "Imagen4 Preview Fast": "Imagen4 Fast",
                    "Imagen4 Preview Ultra": "Imagen4 Ultra",
                    # HiDream Models
                    "Hidream I1 Fast": "HiDream Fast",
                    "Hidream I1 Dev": "HiDream Dev",
                    "Hidream I1 Full": "HiDream Full",
                    # Stable Diffusion Models
                    "Stable Diffusion V35 Large": "SD35 Large",
                    "Stable Diffusion V35 Medium": "SD35 Medium",
                    # Other Models
                    "Luma Photon": "Luma Photon",
                    "Ideogram V2": "Ideogram v2",
                    "Recraft 20B": "Recraft",
                    "Sana": "Sana",
                    "Bytedance Seedream V3 Text To Image": "Seedream v3",
                    "Bytedance Seedream V4 Text To Image": "Seedream v4",
                    "Wan V2.2-5B Text To Image": "WAN v2.2",
                    "Gemini 25 Flash Image": "Gemini Flash"
                }
                
                # Use abbreviation if available, otherwise use the cleaned-up name
                display_name = abbreviations.get(display_name, display_name)
                
                btn = ttk.Button(
                    button_frame,
                    text=display_name,
                    command=lambda m=model: self.select_model(m),
                    style='Model.TButton'
                )
                btn.grid(row=0, column=i, padx=2, pady=2, sticky="ew")
                
                # Add tooltip with full model name
                self.add_tooltip(btn, model.replace("fal-ai/", "").replace("/", " ").title())
                
                self.model_buttons[model] = btn
                
                # Configure button style based on selection
                if model == self.model_var.get():
                    btn.configure(style='Model.Selected.TButton')
            
            row += 1
        
        # Configure column weights for responsive layout
        self.model_matrix_frame.grid_columnconfigure(0, weight=1)
    
    def select_model(self, model):
        """Select a model and update button states, then regenerate if there's a prompt."""
        self.model_var.set(model)
        
        # Update button appearances
        for m, btn in self.model_buttons.items():
            if m == model:
                btn.configure(style='Model.Selected.TButton')
            else:
                btn.configure(style='Model.TButton')
        
        # Update auto-generate settings based on model
        self.on_model_change()
        
        # Regenerate with the new model if there's a current prompt
        current_prompt = self.text_input.get("1.0", tk.END).strip()
        if current_prompt:
            self.manual_generate()
    
    def on_model_change(self):
        """Handle model selection change."""
        selected_model = self.model_var.get()
        # Enable auto-generate for Flux models (schnell and srpo)
        if selected_model in ["fal-ai/flux/schnell", "fal-ai/flux-1/srpo"]:
            self.auto_checkbox.state(['!disabled'])
        else:
            self.auto_generate.set(False)
            self.auto_checkbox.state(['disabled'])
            
    def create_img(self, prompt):
        start_time = time.time()  # Start timing
        try:
            self.status_label.config(text="Generating image...")
            self.is_generating = True
            self.update_spinner()  # Start progress bar animation
            selected_model = self.model_var.get()
            
            # Use the image generation API
            self.current_image = generate_image(selected_model, prompt)
            
            # Calculate generation time
            generation_time = time.time() - start_time
            
            # Reset zoom/pan state
            self.zoom_level = 1.0
            self.view_offset_x = 0
            self.view_offset_y = 0
            
            # Update the image in the main thread
            self.root.after(0, self.update_image)
            
            # Update status with generation time
            self.root.after(0, lambda: self.status_label.config(text=f"Ready (Generated in {generation_time:.1f}s)"))
            
        except Exception as e:
            self.root.after(0, self.status_label.config, {"text": f"Error: {str(e)}"})
        finally:
            self.is_generating = False
            self.update_spinner() # Stop progress bar
            self.check_queue()
    
    def save_image(self):
        if not self.current_image:
            self.status_label.config(text="No image to save.")
            return

        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")]
            )

            if not filepath:
                return # User cancelled

            # Save the image
            self.current_image.save(filepath, "jpeg")
            self.status_label.config(text=f"Image saved to {filepath}")
        except Exception as e:
            self.status_label.config(text=f"Error saving image: {e}")

    def on_copy_shortcut(self, event):
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

    def copy_image_to_clipboard(self):
        if not self.current_image:
            self.status_label.config(text="No image to copy.")
            return

        try:
            if sys.platform.startswith('win'):
                self._copy_to_clipboard_windows(self.current_image)
                self.status_label.config(text="Image copied to clipboard.")
            else:
                self.status_label.config(text="Copy not supported on this OS.")
        except Exception as e:
            self.status_label.config(text=f"Error copying image: {e}")

    def _copy_to_clipboard_windows(self, image: Image.Image):
        """Copy a PIL Image to the Windows clipboard as CF_DIB (100% scale)."""
        # Ensure RGB (no alpha) for broad compatibility
        img = image.convert('RGB')

        # Convert to DIB bytes (BMP without the 14-byte file header)
        with io.BytesIO() as output:
            img.save(output, format='BMP')
            bmp_data = output.getvalue()
        dib_data = bmp_data[14:]

        CF_DIB = 8
        GMEM_MOVEABLE = 0x0002

        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32

        # Define arg/restypes for 64-bit safety
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL
        kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalFree.restype = wintypes.HGLOBAL

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.EmptyClipboard.argtypes = []
        user32.EmptyClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = wintypes.BOOL

        h_global = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(dib_data))
        if not h_global:
            raise RuntimeError('GlobalAlloc failed')

        try:
            p_global = kernel32.GlobalLock(h_global)
            if not p_global:
                raise RuntimeError('GlobalLock failed')
            try:
                ctypes.memmove(p_global, dib_data, len(dib_data))
            finally:
                kernel32.GlobalUnlock(h_global)

            # Try to open clipboard, retry briefly if busy
            for _ in range(5):
                if user32.OpenClipboard(None):
                    break
                time.sleep(0.01)
            else:
                raise RuntimeError('OpenClipboard failed')

            try:
                if not user32.EmptyClipboard():
                    raise RuntimeError('EmptyClipboard failed')
                if not user32.SetClipboardData(CF_DIB, h_global):
                    raise RuntimeError('SetClipboardData failed')
                # After successful SetClipboardData, the system owns h_global.
                h_global = None
            finally:
                user32.CloseClipboard()
        finally:
            if h_global:
                kernel32.GlobalFree(h_global)

    def update_image(self):
        if not self.current_image:
            return

        # This method now only schedules an update in the background thread
        self.schedule_update()

    def create_photo_image(self, params):
        if not self.current_image:
            return None

        zoom_level = params["zoom"]
        offset_x = params["offset_x"]
        offset_y = params["offset_y"]
        frame_width = params["frame_width"]
        frame_height = params["frame_height"]

        if frame_width <= 1 or frame_height <= 1:
            return None

        image_ratio = self.current_image.width / self.current_image.height
        frame_ratio = frame_width / frame_height

        if frame_ratio > image_ratio:
            base_height = frame_height
            base_width = int(base_height * image_ratio)
        else:
            base_width = frame_width
            base_height = int(base_width / image_ratio)

        zoomed_width = int(base_width * zoom_level)
        zoomed_height = int(base_height * zoom_level)

        if zoomed_width < 1 or zoomed_height < 1:
            return None

        resized_image = self.current_image.resize((zoomed_width, zoomed_height), Image.Resampling.BICUBIC)
        final_image = Image.new('RGB', (frame_width, frame_height))
        paste_x = (frame_width - zoomed_width) // 2 - offset_x
        paste_y = (frame_height - zoomed_height) // 2 - offset_y
        final_image.paste(resized_image, (paste_x, paste_y))

        return ImageTk.PhotoImage(final_image)
    
    def on_window_resize(self, event):
        # Only handle main window resize events
        if event.widget == self.root:
            self.update_image()
    
    def zoom_image(self, event):
        if not self.current_image:
            return

        # Determine zoom direction
        if event.num == 5 or event.delta < 0:  # Scroll down (zoom out)
            zoom_factor = 0.9
        else:  # Scroll up (zoom in)
            zoom_factor = 1.1
        
        new_zoom_level = self.zoom_level * zoom_factor
        new_zoom_level = max(0.1, min(new_zoom_level, 10.0)) # Clamp zoom

        # --- Calculate new offset to zoom towards cursor ---
        frame_width = self.image_frame.winfo_width()
        frame_height = self.image_frame.winfo_height()
        image_ratio = self.current_image.width / self.current_image.height
        frame_ratio = frame_width / frame_height

        if frame_ratio > image_ratio:
            base_height = frame_height
            base_width = int(base_height * image_ratio)
        else:
            base_width = frame_width
            base_height = int(base_width / image_ratio)

        # Position of cursor relative to the center of the frame
        cursor_relative_x = event.x - frame_width / 2
        cursor_relative_y = event.y - frame_height / 2

        # How much the pan offset should change
        dx = cursor_relative_x * (zoom_factor - 1)
        dy = cursor_relative_y * (zoom_factor - 1)

        self.view_offset_x += int(dx)
        self.view_offset_y += int(dy)
        self.zoom_level = new_zoom_level
        
        self.schedule_update()

    def schedule_update(self):
        # Put the current state into the queue for the worker thread
        params = {
            "zoom": self.zoom_level,
            "offset_x": self.view_offset_x,
            "offset_y": self.view_offset_y,
            "frame_width": self.image_frame.winfo_width(),
            "frame_height": self.image_frame.winfo_height(),
        }
        self.update_queue.put(params)

    def start_pan(self, event):
        self.pan_start_x = event.x
        self.pan_start_y = event.y

    def pan_image(self, event):
        if not self.current_image:
            return
        dx = event.x - self.pan_start_x
        dy = event.y - self.pan_start_y
        
        self.view_offset_x -= dx
        self.view_offset_y -= dy
        
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        
        self.schedule_update()
    
    def check_queue(self):
        """Check if there's a pending prompt to process"""
        if not self.prompt_queue.empty():
            prompt = self.prompt_queue.get()
            self.start_generation(prompt)
    
    def start_generation(self, prompt):
        """Start the image generation in a new thread"""
        self.is_generating = True
        self.current_thread = threading.Thread(target=self.create_img, args=(prompt,))
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def on_key_release(self, event):
        if not self.auto_generate.get() or event.keysym == 'Return':
            return
                
        current_prompt = self.text_input.get("1.0", tk.END).strip()
        if len(current_prompt) > 0:
            if self.is_generating:
                # If currently generating, update the queue with the latest prompt
                while not self.prompt_queue.empty():
                    self.prompt_queue.get()  # Clear old prompts
                self.prompt_queue.put(current_prompt)
            else:
                # If not generating, start generation
                self.start_generation(current_prompt)
                
    def on_enter(self, event):
        if not self.auto_generate.get():
            current_prompt = self.text_input.get("1.0", tk.END).strip()
            if len(current_prompt) > 0:
                if self.is_generating:
                    while not self.prompt_queue.empty():
                        self.prompt_queue.get()
                    self.prompt_queue.put(current_prompt)
                else:
                    self.start_generation(current_prompt)
        return 'break'  # Prevents the default behavior of adding a newline
    
    def adjust_text_height(self):
        """Automatically adjust the height of the text widget based on content"""
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
    
    def on_text_change(self, event):
        """Handle text changes for auto-generation"""
        # Call the original key release handler
        self.on_key_release(event)
        # Adjust text height
        self.root.after(10, self.adjust_text_height)
    
    def on_text_modified(self, event):
        """Handle text modification events"""
        # Reset the modified flag
        self.text_input.edit_modified(False)
        # Adjust text height
        self.adjust_text_height()
    
    def manual_generate(self):
        """Generate image when Generate button is clicked"""
        current_prompt = self.text_input.get("1.0", tk.END).strip()
        if len(current_prompt) > 0:
            if self.is_generating:
                while not self.prompt_queue.empty():
                    self.prompt_queue.get()
                self.prompt_queue.put(current_prompt)
            else:
                self.start_generation(current_prompt)


def main():
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
