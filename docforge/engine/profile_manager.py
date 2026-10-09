"""Manager service for discovering, loading, creating, and exporting Format Profiles."""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from docforge.app.paths import get_bundled_assets_dir, get_profiles_dir
from docforge.engine.profile import FormatProfile


class ProfileManager:
    """Manages profile loading from user directory and bundled defaults."""

    def __init__(self, user_profiles_dir: Path = get_profiles_dir()) -> None:
        """Initialize ProfileManager with user profile storage path."""
        self.user_profiles_dir = user_profiles_dir
        self.ensure_default_profiles_exist()

    def ensure_default_profiles_exist(self) -> None:
        """Copy bundled default profile files to user profiles directory if not present."""
        bundled_dir = get_bundled_assets_dir() / "default_profiles"
        if not bundled_dir.exists():
            return

        self.user_profiles_dir.mkdir(parents=True, exist_ok=True)
        for bundled_file in bundled_dir.glob("*.json"):
            target_file = self.user_profiles_dir / bundled_file.name
            if not target_file.exists():
                try:
                    shutil.copy(bundled_file, target_file)
                except Exception:
                    pass

    def list_profiles(self) -> List[FormatProfile]:
        """Load and return all valid format profiles in user directory."""
        profiles: List[FormatProfile] = []
        if not self.user_profiles_dir.exists():
            return profiles

        for file_path in self.user_profiles_dir.glob("*.json"):
            try:
                profile = FormatProfile.load_from_file(file_path)
                profiles.append(profile)
            except Exception:
                continue
        return profiles

    def get_profile_by_name(self, name: str) -> Optional[FormatProfile]:
        """Fetch profile matching name, returning None if not found."""
        for profile in self.list_profiles():
            if profile.name.lower() == name.lower():
                return profile
        return None

    def save_profile(self, profile: FormatProfile) -> Path:
        """Save a profile to the user profiles directory."""
        safe_filename = "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in profile.name).strip().lower()
        file_path = self.user_profiles_dir / f"{safe_filename}.json"
        profile.save_to_file(file_path)
        return file_path

    def delete_profile(self, name: str) -> bool:
        """Delete profile file matching name from user profiles directory."""
        for file_path in self.user_profiles_dir.glob("*.json"):
            try:
                p = FormatProfile.load_from_file(file_path)
                if p.name.lower() == name.lower():
                    file_path.unlink()
                    return True
            except Exception:
                continue
        return False
