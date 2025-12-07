"""
Threading utilities for managing background operations and update queues.
Handles image processing threads and display queue management.
"""

import threading
import queue
import time
from typing import Optional, Dict, Any, Callable, List


class UpdateThreadManager:
    """Manages background threads for image processing and display updates."""
    
    def __init__(self):
        """Initialize the update thread manager."""
        self.update_queue = queue.Queue()
        self.display_queue = queue.Queue()
        self.update_thread: Optional[threading.Thread] = None
        self.is_running = False
        
    def start_update_thread(self):
        """Start the background update thread."""
        if self.update_thread and self.update_thread.is_alive():
            return
            
        self.is_running = True
        self.update_thread = threading.Thread(target=self._process_updates, daemon=True)
        self.update_thread.start()
    
    def stop_update_thread(self):
        """Stop the background update thread."""
        self.is_running = False
        if self.update_thread:
            # Add a sentinel value to wake up the thread
            self.update_queue.put(None)
    
    def _process_updates(self):
        """Process update requests in the background thread."""
        while self.is_running:
            try:
                # Wait for the latest update request
                update_params = self.update_queue.get(timeout=0.1)
                
                # If we got a sentinel value, exit
                if update_params is None:
                    break
                
                # Clear any older pending updates
                while not self.update_queue.empty():
                    try:
                        newer_params = self.update_queue.get_nowait()
                        if newer_params is None:
                            break
                        update_params = newer_params
                    except queue.Empty:
                        break
                
                # Process the update
                if update_params and hasattr(self, 'create_photo_callback'):
                    photo = self.create_photo_callback(update_params)
                    if photo:
                        self.display_queue.put(photo)
                        
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in update thread: {e}")
    
    def schedule_update(self, params: Dict[str, Any]):
        """
        Schedule an image update with the given parameters.
        
        Args:
            params: Dictionary containing zoom, offset, and frame dimensions
        """
        if self.is_running:
            self.update_queue.put(params)
    
    def get_display_update(self) -> Optional[Any]:
        """
        Get the next display update from the queue.
        
        Returns:
            The photo image object if available, None otherwise
        """
        try:
            return self.display_queue.get_nowait()
        except queue.Empty:
            return None
    
    def has_pending_display_updates(self) -> bool:
        """Check if there are pending display updates."""
        return not self.display_queue.empty()
    
    def set_create_photo_callback(self, callback):
        """
        Set the callback function for creating photo images.
        
        Args:
            callback: Function that takes params and returns a PhotoImage
        """
        self.create_photo_callback = callback


class SpinnerAnimator:
    """Handles spinner animation for progress indication."""
    
    def __init__(self, spinner_frames=None):
        """Initialize the spinner animator."""
        self.spinner_frames = spinner_frames or ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_index = 0
        
    def get_next_frame(self) -> str:
        """Get the next spinner frame."""
        frame = self.spinner_frames[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.spinner_frames)
        return frame
    
    def reset(self):
        """Reset the spinner to the beginning."""
        self.current_index = 0
    
    def set_frames(self, frames):
        """Set custom spinner frames."""
        self.spinner_frames = frames
        self.current_index = 0