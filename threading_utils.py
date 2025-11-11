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


class GenerationQueueManager:
    """Manages the queue for image generation requests."""
    
    def __init__(self):
        """Initialize the generation queue manager."""
        self.prompt_queue = queue.Queue()
        self.threads: List[threading.Thread] = []
        self.lock = threading.Lock()
        # Parallel generation state
        self.parallel_threads: List[threading.Thread] = []
        self.parallel_results: "queue.Queue[Dict[str, Any]]" = queue.Queue()
        self.parallel_active = False
        self.parallel_total = 0
        self.parallel_finished = 0
        self.parallel_first_success_reported = False
        self.parallel_lock = threading.Lock()
    
    def queue_prompt(self, prompt: str):
        """
        Add a prompt to the generation queue.
        
        Args:
            prompt: The text prompt for image generation
        """
        # Clear old prompts and add the new one
        while not self.prompt_queue.empty():
            self.prompt_queue.get()
        self.prompt_queue.put(prompt)
    
    def get_next_prompt(self) -> Optional[str]:
        """
        Get the next prompt from the queue.
        
        Returns:
            The prompt string if available, None otherwise
        """
        try:
            return self.prompt_queue.get_nowait()
        except queue.Empty:
            return None
    
    def has_pending_prompts(self) -> bool:
        """Check if there are pending prompts in the queue."""
        return not self.prompt_queue.empty()
    
    def start_generation_thread(self, target_function, args=()):
        """
        Start a new generation thread.
        
        Args:
            target_function: The function to run in the thread
            args: Arguments to pass to the function
        """
        with self.lock:
            thread = threading.Thread(target=target_function, args=args, daemon=True)
            self.threads.append(thread)
            thread.start()
        return True
    
    def finish_generation(self):
        """Mark the current generation as finished."""
        with self.lock:
            self.threads = [t for t in self.threads if t.is_alive()]
    
    def is_currently_generating(self) -> bool:
        """Check if currently generating an image."""
        with self.lock:
            return any(t.is_alive() for t in self.threads)
    
    def wait_for_completion(self, timeout: Optional[float] = None):
        """
        Wait for the current generation to complete.
        
        Args:
            timeout: Maximum time to wait in seconds
        """
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(timeout=timeout)

    def start_parallel_generation(self, models: List[str], prompt: str,
                                  worker_function: Callable[[str, str], Any]) -> bool:
        """Start parallel generation threads for the provided models."""
        if not models:
            return False

        with self.parallel_lock:
            if self.parallel_active:
                return False

            self.parallel_active = True
            self.parallel_total = len(models)
            self.parallel_finished = 0
            self.parallel_first_success_reported = False
            self.parallel_results = queue.Queue()
            self.parallel_threads = []

        for model in models:
            worker_thread = threading.Thread(
                target=self._run_parallel_job,
                args=(model, prompt, worker_function),
                daemon=True
            )
            worker_thread.start()
            self.parallel_threads.append(worker_thread)

        return True

    def _run_parallel_job(self, model: str, prompt: str, worker_function: Callable[[str, str], Any]):
        """Execute a single model generation job within a parallel run."""
        start_time = time.time()
        result_payload: Dict[str, Any] = {"model": model}
        try:
            result = worker_function(model, prompt)
            result_payload["result"] = result
        except Exception as exc:
            result_payload["error"] = str(exc)
        finally:
            result_payload["time"] = time.time() - start_time
            self.parallel_results.put(result_payload)
            with self.parallel_lock:
                self.parallel_finished += 1
                if self.parallel_finished >= self.parallel_total:
                    self.parallel_active = False

    def has_parallel_results(self) -> bool:
        """Determine whether any parallel generation results are waiting."""
        return not self.parallel_results.empty()

    def get_parallel_result(self) -> Optional[Dict[str, Any]]:
        """Retrieve the next available parallel generation result."""
        try:
            result = self.parallel_results.get_nowait()
        except queue.Empty:
            return None

        with self.parallel_lock:
            if "error" not in result and not self.parallel_first_success_reported:
                result["first"] = True
                self.parallel_first_success_reported = True
            else:
                result["first"] = False

        return result

    def is_parallel_active(self) -> bool:
        """Check if parallel generation threads are still running."""
        with self.parallel_lock:
            return self.parallel_active


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