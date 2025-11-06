"""
Clipboard management module for cross-platform clipboard operations.
Handles copying images to clipboard with platform-specific implementations.
"""

import io
import sys
import ctypes
from ctypes import wintypes
import time
from PIL import Image


class ClipboardManager:
    """Manages clipboard operations across different platforms."""
    
    def __init__(self):
        """Initialize the clipboard manager."""
        pass
    
    def copy_image_to_clipboard(self, image: Image.Image) -> bool:
        """
        Copy a PIL Image to the system clipboard.
        
        Args:
            image: PIL Image to copy
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not image:
            return False
            
        try:
            if sys.platform.startswith('win'):
                self._copy_to_clipboard_windows(image)
                return True
            else:
                # For other platforms, you could implement additional methods
                # For now, return False to indicate unsupported
                return False
        except Exception as e:
            print(f"Error copying image to clipboard: {e}")
            return False
    
    def _copy_to_clipboard_windows(self, image: Image.Image):
        """
        Copy a PIL Image to the Windows clipboard as CF_DIB (100% scale).
        Uses Windows API calls for direct clipboard manipulation.
        """
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
    
    def is_clipboard_supported(self) -> bool:
        """
        Check if clipboard operations are supported on the current platform.
        
        Returns:
            bool: True if clipboard operations are supported
        """
        return sys.platform.startswith('win')