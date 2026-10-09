"""Unit tests for format profile schema, serialization, validation, and profile manager."""

import json
from pathlib import Path
import pytest
from docforge.engine.profile import FormatProfile, BodyStyle, HeadingsConfig
from docforge.engine.profile_manager import ProfileManager


def test_default_profile_instantiation():
    """Verify default profile instantiates with valid v1 schema defaults."""
    profile = FormatProfile()
    assert profile.profile_version == 1
    assert profile.name == "Default Profile"
    assert profile.cover.enabled is True
    assert profile.body.font_family == "Segoe UI"
    assert profile.headings.h1.size_pt == 22.0
    assert profile.page.size == "A4"


def test_profile_dict_roundtrip():
    """Verify profile serializes to dict and deserializes accurately."""
    profile = FormatProfile(name="Custom Test Profile")
    profile.body.size_pt = 12.5
    profile.headings.h1.color = "#FF0000"
    
    d = profile.to_dict()
    reconstructed = FormatProfile.from_dict(d)
    
    assert reconstructed.name == "Custom Test Profile"
    assert reconstructed.body.size_pt == 12.5
    assert reconstructed.headings.h1.color == "#FF0000"


def test_profile_file_io(tmp_path: Path):
    """Verify profile saves to and loads from JSON file on disk."""
    json_path = tmp_path / "test_profile.json"
    profile = FormatProfile(name="Disk Profile")
    profile.save_to_file(json_path)
    
    assert json_path.exists()
    loaded = FormatProfile.load_from_file(json_path)
    assert loaded.name == "Disk Profile"


def test_profile_manager_lifecycle(tmp_path: Path):
    """Verify profile manager can list, save, fetch, and delete profiles."""
    manager = ProfileManager(user_profiles_dir=tmp_path)
    
    p = FormatProfile(name="Manager Test Profile")
    manager.save_profile(p)
    
    fetched = manager.get_profile_by_name("Manager Test Profile")
    assert fetched is not None
    assert fetched.name == "Manager Test Profile"
    
    deleted = manager.delete_profile("Manager Test Profile")
    assert deleted is True
    assert manager.get_profile_by_name("Manager Test Profile") is None
