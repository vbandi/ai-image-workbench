"""
Settings Manager for the Image Generator application.
Handles persistence of window state including position, size, and splitter positions.
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

LOGGER = logging.getLogger(__name__)

# Default settings file location (in user's home directory)
SETTINGS_DIR = Path.home() / ".image_generator"
SETTINGS_FILE = SETTINGS_DIR / "window_state.json"


class WindowSettings:
    """Data class for window settings."""
    
    def __init__(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        main_splitter_position: Optional[int] = None,
        sidebar_splitter_position: Optional[int] = None,
        is_maximized: bool = False
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.main_splitter_position = main_splitter_position
        self.sidebar_splitter_position = sidebar_splitter_position
        self.is_maximized = is_maximized
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "main_splitter_position": self.main_splitter_position,
            "sidebar_splitter_position": self.sidebar_splitter_position,
            "is_maximized": self.is_maximized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WindowSettings":
        """Create settings from dictionary."""
        return cls(
            x=data.get("x"),
            y=data.get("y"),
            width=data.get("width"),
            height=data.get("height"),
            main_splitter_position=data.get("main_splitter_position"),
            sidebar_splitter_position=data.get("sidebar_splitter_position"),
            is_maximized=data.get("is_maximized", False)
        )
    
    def is_valid(self) -> bool:
        """Check if settings have valid window position/size."""
        return all([
            self.width is not None and self.width > 0,
            self.height is not None and self.height > 0
        ])


class ModelVisibilitySettings:
    """Data class for model visibility settings."""
    
    def __init__(self, hidden_models: Optional[set] = None):
        self.hidden_models = hidden_models or set()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "hidden_models": list(self.hidden_models)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelVisibilitySettings":
        """Create settings from dictionary."""
        return cls(
            hidden_models=set(data.get("hidden_models", []))
        )


class SettingsManager:
    """Manager for saving and loading application settings."""
    
    def __init__(self, settings_file: Optional[Path] = None):
        """Initialize the settings manager.
        
        Args:
            settings_file: Optional path to the settings file. 
                          Uses default location if not provided.
        """
        self.settings_file = settings_file or SETTINGS_FILE
        self._ensure_settings_dir()
    
    def _ensure_settings_dir(self):
        """Ensure the settings directory exists."""
        settings_dir = self.settings_file.parent
        if not settings_dir.exists():
            try:
                settings_dir.mkdir(parents=True, exist_ok=True)
                LOGGER.debug(f"Created settings directory: {settings_dir}")
            except Exception as e:
                LOGGER.warning(f"Failed to create settings directory: {e}")
    
    def load_window_settings(self) -> WindowSettings:
        """Load window settings from file.
        
        Returns:
            WindowSettings object with loaded values, or defaults if file doesn't exist.
        """
        if not self.settings_file.exists():
            LOGGER.debug("Settings file not found, using defaults")
            return WindowSettings()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            settings = WindowSettings.from_dict(data.get("window", {}))
            LOGGER.debug(f"Loaded window settings: {settings.to_dict()}")
            return settings
            
        except json.JSONDecodeError as e:
            LOGGER.warning(f"Invalid settings file, using defaults: {e}")
            return WindowSettings()
        except Exception as e:
            LOGGER.warning(f"Error loading settings: {e}")
            return WindowSettings()
    
    def save_window_settings(self, settings: WindowSettings) -> bool:
        """Save window settings to file.
        
        Args:
            settings: WindowSettings object to save.
            
        Returns:
            True if save was successful, False otherwise.
        """
        try:
            # Load existing settings to preserve other data
            existing_data = {}
            if self.settings_file.exists():
                try:
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception:
                    pass
            
            # Update window settings
            existing_data["window"] = settings.to_dict()
            
            # Save to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2)
            
            LOGGER.debug(f"Saved window settings: {settings.to_dict()}")
            return True
            
        except Exception as e:
            LOGGER.warning(f"Error saving settings: {e}")
            return False
    
    def load_model_visibility_settings(self) -> ModelVisibilitySettings:
        """Load model visibility settings from file.
        
        Returns:
            ModelVisibilitySettings object with loaded values, or defaults if file doesn't exist.
        """
        if not self.settings_file.exists():
            LOGGER.debug("Settings file not found, using defaults")
            return ModelVisibilitySettings()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            settings = ModelVisibilitySettings.from_dict(data.get("model_visibility", {}))
            LOGGER.debug(f"Loaded model visibility settings: {settings.to_dict()}")
            return settings
            
        except json.JSONDecodeError as e:
            LOGGER.warning(f"Invalid settings file, using defaults: {e}")
            return ModelVisibilitySettings()
        except Exception as e:
            LOGGER.warning(f"Error loading settings: {e}")
            return ModelVisibilitySettings()
    
    def save_model_visibility_settings(self, settings: ModelVisibilitySettings) -> bool:
        """Save model visibility settings to file.
        
        Args:
            settings: ModelVisibilitySettings object to save.
            
        Returns:
            True if save was successful, False otherwise.
        """
        try:
            # Load existing settings to preserve other data
            existing_data = {}
            if self.settings_file.exists():
                try:
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except Exception:
                    pass
            
            # Update model visibility settings
            existing_data["model_visibility"] = settings.to_dict()
            
            # Save to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2)
            
            LOGGER.debug(f"Saved model visibility settings: {settings.to_dict()}")
            return True
            
        except Exception as e:
            LOGGER.warning(f"Error saving settings: {e}")
            return False
