"""Path utilities for DocForge application data and settings."""

import os
import sys
from pathlib import Path


def get_app_data_dir() -> Path:
    """Return the root application data directory in %APPDATA%/DocForge."""
    app_data = os.getenv("APPDATA")
    if app_data:
        base_dir = Path(app_data) / "DocForge"
    else:
        base_dir = Path.home() / ".docforge"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def get_profiles_dir() -> Path:
    """Return the path to the user format profiles directory."""
    profiles_dir = get_app_data_dir() / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    return profiles_dir


def get_logs_dir() -> Path:
    """Return the path to the application log directory."""
    logs_dir = get_app_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_settings_file_path() -> Path:
    """Return the path to the settings JSON file."""
    return get_app_data_dir() / "settings.json"


def get_bundled_assets_dir() -> Path:
    """Return the root path for bundled application assets (themes, default profiles)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "docforge" / "assets"  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent / "assets"
