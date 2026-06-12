"""
Generation Manager module.
Handles the unified queueing and execution of image generation requests.
"""

import time
import uuid
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Callable
from PIL import Image

from image_gen_api import generate_image

LOGGER = logging.getLogger("image_generator.manager")


class RequestStatus(Enum):
    """Status of a generation request."""
    QUEUED = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class GenerationRequest:
    """Represents a single image generation request."""
    request_id: str
    model: str
    prompt: str
    status: RequestStatus = RequestStatus.QUEUED
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result_image: Optional[Image.Image] = None
    result_image: Optional[Image.Image] = None
    error_message: Optional[str] = None
    seen: bool = False
    
    @property
    def duration(self) -> float:
        """Calculate duration of the request."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0


class GenerationManager:
    """
    Manages asynchronous image generation requests.
    Uses a thread pool to handle multiple concurrent generations.
    """
    
    def __init__(self, max_workers: int = 20):
        """
        Initialize the generation manager.
        
        Args:
            max_workers: Maximum number of concurrent generation threads.
                         Set high (e.g. 20) as the heavy lifting is done by the cloud API.
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="GenWorker")
        # Store all requests: id -> request
        self._requests: Dict[str, GenerationRequest] = {}
        # Keep track of active futures to allow cancellation (best effort)
        self._futures: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
        # Callback for when any request state changes (useful for UI updates)
        self.on_state_change: Optional[Callable[[str], None]] = None
        
    def submit_request(self, model: str, prompt: str) -> str:
        """
        Submit a new generation request.
        
        Args:
            model: The model identifier.
            prompt: The prompt text.
            
        Returns:
            The unique request ID.
        """
        request_id = str(uuid.uuid4())
        request = GenerationRequest(
            request_id=request_id,
            model=model,
            prompt=prompt
        )
        
        with self._lock:
            self._requests[request_id] = request
            # Submit to thread pool
            future = self.executor.submit(self._execute_generation, request_id)
            self._futures[request_id] = future
            
        LOGGER.info(f"Submitted generation request {request_id} for model {model}")
        self._notify_change(request_id)
        return request_id
    
    def cancel_request(self, request_id: str) -> bool:
        """
        Attempt to cancel a request.
        
        Args:
            request_id: The ID of the request to cancel.
            
        Returns:
            True if cancelled, False otherwise.
        """
        with self._lock:
            if request_id not in self._requests:
                return False
                
            request = self._requests[request_id]
            
            # If already finished, can't cancel
            if request.status in (RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.CANCELLED):
                return False
            
            # Update status
            request.status = RequestStatus.CANCELLED
            request.completed_at = time.time()
            request.error_message = "Cancelled by user"
            
            # Try to cancel the future if it hasn't started
            if request_id in self._futures:
                self._futures[request_id].cancel()
                # We don't remove the future immediately, let it finish naturally or be cleaned up
        
        LOGGER.info(f"Cancelled request {request_id}")
        self._notify_change(request_id)
        return True

    def get_request(self, request_id: str) -> Optional[GenerationRequest]:
        """Get a request by ID."""
        with self._lock:
            return self._requests.get(request_id)
            
    def get_all_requests(self) -> List[GenerationRequest]:
        """Get all requests sorted by creation time (newest first)."""
        with self._lock:
            requests = list(self._requests.values())
        return sorted(requests, key=lambda r: r.created_at, reverse=True)
    
    def get_active_requests(self) -> List[GenerationRequest]:
        """Get currently queued or processing requests."""
        with self._lock:
            return [
                r for r in self._requests.values() 
                if r.status in (RequestStatus.QUEUED, RequestStatus.PROCESSING)
            ]
            
    def clear_completed(self):
        """Clear completed/failed/cancelled requests from memory."""
        with self._lock:
            ids_to_remove = [
                rid for rid, r in self._requests.items()
                if r.status in (RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.CANCELLED)
            ]
            for rid in ids_to_remove:
                del self._requests[rid]
                if rid in self._futures:
                    del self._futures[rid]

    def mark_seen(self, request_id: str):
        """Mark a request as seen."""
        with self._lock:
            if request_id in self._requests:
                self._requests[request_id].seen = True
                self._notify_change(request_id)

    def clear_seen(self):
        """Clear requests that are completed and seen."""
        with self._lock:
            ids_to_remove = [
                rid for rid, r in self._requests.items()
                # Must be finished AND seen to be cleared by this method
                if r.status in (RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.CANCELLED) 
                and r.seen
            ]
            for rid in ids_to_remove:
                del self._requests[rid]
                if rid in self._futures:
                    del self._futures[rid]

    def clear_failed(self):
        """Clear failed requests from memory."""
        with self._lock:
            ids_to_remove = [
                rid for rid, r in self._requests.items()
                if r.status == RequestStatus.FAILED
            ]
            for rid in ids_to_remove:
                del self._requests[rid]
                if rid in self._futures:
                    del self._futures[rid]
    
    def _execute_generation(self, request_id: str):
        """
        Worker method to execute the generation.
        """
        # 1. Retrieve request
        with self._lock:
            if request_id not in self._requests:
                return
            request = self._requests[request_id]
            if request.status == RequestStatus.CANCELLED:
                return
            
            request.status = RequestStatus.PROCESSING
            request.started_at = time.time()
        
        self._notify_change(request_id)
        
        try:
            # 2. Call API (Blocking)
            LOGGER.debug(f"Starting API call for {request_id}")
            image = generate_image(request.model, request.prompt)
            
            # 3. Handle Success
            with self._lock:
                # Check cancellation again before saving result
                if request.status == RequestStatus.CANCELLED:
                    return
                
                request.result_image = image
                request.status = RequestStatus.COMPLETED
                request.completed_at = time.time()
                
            LOGGER.info(f"Request {request_id} completed successfully")
            
        except Exception as e:
            # 4. Handle Failure
            LOGGER.error(f"Request {request_id} failed: {e}")
            with self._lock:
                if request.status != RequestStatus.CANCELLED:
                    request.status = RequestStatus.FAILED
                    request.error_message = str(e)
                    request.completed_at = time.time()
                    
        finally:
            # 5. Cleanup future reference
            with self._lock:
                if request_id in self._futures:
                    del self._futures[request_id]
            
            self._notify_change(request_id)

    def _notify_change(self, request_id: str):
        """Notify listener of state change."""
        if self.on_state_change:
            try:
                self.on_state_change(request_id)
            except Exception:
                LOGGER.exception("Error in state change callback")
