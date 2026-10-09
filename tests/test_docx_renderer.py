"""Unit tests for DocxRenderer AST rendering."""

from pathlib import Path
from docx import Document
import pytest

from docforge.app.config import AppSettings
from docforge.engine.docx_renderer import DocxRenderer
from docforge.engine.markdown_parser import MarkdownParser
from docforge.engine.profile import FormatProfile


def test_docx_renderer_basic(tmp_path: Path):
    """Verify DocxRenderer produces valid .docx file from markdown input."""
    md_text = """# Executive Summary

This is a **bold** paragraph with `inline code` and a link.

## Key Features

- Feature 1
- Feature 2

```python
def test():
    return True
```
"""
    parser = MarkdownParser()
    ast_nodes = parser.parse(md_text)
    
    profile = FormatProfile()
    settings = AppSettings()
    
    output_docx = tmp_path / "output.docx"
    renderer = DocxRenderer()
    res_path = renderer.render(ast_nodes, profile, settings, output_docx)

    assert res_path.exists()
    assert res_path.stat().st_size > 0

    # Read back generated document with docx library
    doc = Document(res_path)
    full_text = "\n".join(p.text for p in doc.paragraphs)
    assert "Executive Summary" in full_text
    assert "Feature 1" in full_text
    assert "def test():" in full_text
