"""Golden-file tests: rendering fixed markdown input with all 4 default format profiles."""

from pathlib import Path
from docx import Document
import pytest

from docforge.app.config import AppSettings
from docforge.engine.docx_renderer import DocxRenderer
from docforge.engine.markdown_parser import MarkdownParser
from docforge.engine.profile import FormatProfile
from docforge.engine.profile_manager import ProfileManager

GOLDEN_MARKDOWN = """# System Performance & Reliability Report

## Overview & Architecture

This document outlines the **core system architecture** and metrics for the *DocForge* engine.

### System Components

- High performance pure Python rendering engine
- Extensible format profiles JSON schema
- Robust error handling and fallback mechanisms

```python
def generate_document(markdown: str, profile_name: str) -> bool:
    print(f"Rendering with profile: {profile_name}")
    return True
```

> "Clean architecture, small footprint, and long-term extensibility."

| Component | Status | Target Metric |
| --- | --- | --- |
| Parser | Operational | AST tree walker |
| Renderer | Operational | < 100ms render |
| UI | Operational | PySide6 Qt |
"""


def test_golden_docx_rendering_all_profiles(tmp_path: Path):
    """Verify golden markdown renders deterministically for all 4 default profiles."""
    profile_manager = ProfileManager(user_profiles_dir=tmp_path / "profiles")
    profiles = profile_manager.list_profiles()

    assert len(profiles) >= 4

    parser = MarkdownParser()
    ast_nodes = parser.parse(GOLDEN_MARKDOWN)
    settings = AppSettings(author_name="Anthony Reddy", date_format="%B %d, %Y")
    renderer = DocxRenderer()

    profile_names = [p.name for p in profiles]
    assert "Anthony's Reference Format" in profile_names
    assert "Troubleshooting Doc" in profile_names
    assert "Code Review Doc" in profile_names
    assert "Issue Log" in profile_names

    for profile in profiles:
        output_file = tmp_path / f"golden_{profile.name.replace(' ', '_')}.docx"
        res_path = renderer.render(ast_nodes, profile, settings, output_file)

        assert res_path.exists()
        assert res_path.stat().st_size > 1000  # Non-trivial docx file size

        # Inspect generated docx contents
        doc = Document(res_path)
        full_text = "\n".join(p.text for p in doc.paragraphs)

        # Assert cover page content
        assert "System Performance & Reliability Report" in full_text
        assert "Anthony Reddy" in full_text

        # Assert body content present
        assert "Overview & Architecture" in full_text
        assert "High performance pure Python" in full_text
        assert "generate_document" in full_text
