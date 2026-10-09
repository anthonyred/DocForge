"""User configuration and persistent settings manager for DocForge."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

from docforge.app.paths import get_settings_file_path
from docforge.app.strings import Strings


@dataclass
class AppSettings:
    """Application settings schema."""

    author_name: str = Strings.AUTHOR_DEFAULT
    date_format: str = Strings.DATE_FORMAT_DEFAULT
    theme: str = "light"  # light or dark
    default_profile_name: str = "Anthony's Reference Format"
    last_profile_used: str = "Anthony's Reference Format"

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        """Construct AppSettings instance from dictionary with fallback defaults."""
        return cls(
            author_name=str(data.get("author_name", Strings.AUTHOR_DEFAULT)),
            date_format=str(data.get("date_format", Strings.DATE_FORMAT_DEFAULT)),
            theme=str(data.get("theme", "light")),
            default_profile_name=str(data.get("default_profile_name", "Anthony's Reference Format")),
            last_profile_used=str(data.get("last_profile_used", "Anthony's Reference Format")),
        )


class ConfigManager:
    """Manages reading and writing application configuration to disk."""

    def __init__(self, file_path: Path = get_settings_file_path()) -> None:
        """Initialize ConfigManager with file path."""
        self.file_path = file_path

    def load_settings(self) -> AppSettings:
        """Load settings from disk or return default settings if missing/corrupt."""
        if not self.file_path.exists():
            settings = AppSettings()
            self.save_settings(settings)
            return settings

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AppSettings.from_dict(data)
        except Exception:
            return AppSettings()

    def save_settings(self, settings: AppSettings) -> None:
        """Save settings instance to disk."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(settings.to_dict(), f, indent=2)
