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
    
    def get_image_from_clipboard(self) -> Image.Image | None:
        """
        Get a PIL Image from the system clipboard.
        
        Returns:
            PIL Image if successful, None otherwise
        """
        try:
            if sys.platform.startswith('win'):
                return self._get_from_clipboard_windows()
            else:
                return None
        except Exception as e:
            print(f"Error getting image from clipboard: {e}")
            return None
    
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
    
    def _get_from_clipboard_windows(self) -> Image.Image | None:
        """
        Get a PIL Image from the Windows clipboard.
        Supports CF_DIB format.
        """
        CF_DIB = 8
        CF_BITMAP = 2
        
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        gdi32 = ctypes.windll.gdi32
        
        # Define arg/restypes
        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.GetClipboardData.argtypes = [wintypes.UINT]
        user32.GetClipboardData.restype = wintypes.HANDLE
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = wintypes.BOOL
        
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL
        kernel32.GlobalSize.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalSize.restype = ctypes.c_size_t
        
        # Try to open clipboard
        for _ in range(5):
            if user32.OpenClipboard(None):
                break
            time.sleep(0.01)
        else:
            raise RuntimeError('OpenClipboard failed')
        
        try:
            # Try CF_DIB first
            h_data = user32.GetClipboardData(CF_DIB)
            if h_data:
                p_data = kernel32.GlobalLock(h_data)
                if p_data:
                    try:
                        size = kernel32.GlobalSize(h_data)
                        dib_data = ctypes.string_at(p_data, size)
                        # Convert DIB to BMP by adding BMP header
                        bmp_header = b'BM' + (len(dib_data) + 14).to_bytes(4, 'little') + b'\x00\x00\x00\x00\x36\x00\x00\x00'
                        bmp_data = bmp_header + dib_data
                        return Image.open(io.BytesIO(bmp_data))
                    finally:
                        kernel32.GlobalUnlock(h_data)
            
            # If no DIB, try CF_BITMAP
            h_bitmap = user32.GetClipboardData(CF_BITMAP)
            if h_bitmap:
                # This is more complex, would need to convert HBITMAP to DIB
                # For now, return None if DIB not available
                pass
                
            return None
        finally:
            user32.CloseClipboard()
    
    def is_clipboard_supported(self) -> bool:
        """
        Check if clipboard operations are supported on the current platform.
        
        Returns:
            bool: True if clipboard operations are supported
        """
        return sys.platform.startswith('win')