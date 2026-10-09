"""Prepare a private Pandoc reference copy for custom Word style names."""

from pathlib import Path
from typing import Any

from docx import Document
from docx.document import Document as DocumentObject
from docx.enum.style import WD_STYLE_TYPE

from docforge.engine.reference_analyzer import ReferenceDocxAnalyzer


def prepare_reference_docx(source_path: Path, prepared_path: Path) -> Path:
    """Copy observed custom heading styles onto Pandoc's standard heading styles."""
    document: DocumentObject = Document(str(source_path))
    mappings = ReferenceDocxAnalyzer().mapped_styles(document)
    for markdown_style, source_name in mappings.items():
        if source_name.startswith("Normal"):
            continue
        target_name = _target_style_name(markdown_style)
        if not target_name or source_name == target_name:
            continue
        source = document.styles[source_name]
        target = next((style for style in document.styles if style.name == target_name), None)
        if target is None:
            target = document.styles.add_style(target_name, WD_STYLE_TYPE.PARAGRAPH)
        _copy_style(source, target)
    _ensure_pandoc_styles(document)
    document.save(str(prepared_path))
    return prepared_path


def _ensure_pandoc_styles(document: DocumentObject) -> None:
    """Supply Pandoc's compact paragraph and table styles when the reference lacks them."""
    available = {style.name for style in document.styles}
    if "Compact" not in available:
        compact = document.styles.add_style("Compact", WD_STYLE_TYPE.PARAGRAPH)
        compact.base_style = document.styles["Normal"]
        compact.paragraph_format.space_after = 0
    if "Table" not in available:
        table_base = next(
            (document.styles[name] for name in ("Light Shading", "Table Grid", "Normal Table") if name in available),
            None,
        )
        table_style = document.styles.add_style("Table", WD_STYLE_TYPE.TABLE)
        if table_base is not None:
            table_style.base_style = table_base


def _target_style_name(markdown_style: str) -> str:
    """Translate Markdown structures into Pandoc's recognized style names."""
    if markdown_style.startswith("Markdown H"):
        return f"Heading {markdown_style[-1]}"
    return {
        "Markdown body": "Normal",
        "Markdown code": "Source Code",
        "Markdown quote": "Block Text",
    }.get(markdown_style, "")


def _copy_style(source: Any, target: Any) -> None:
    """Copy observable font and paragraph properties between Word styles."""
    source_font = source.font
    target_font = target.font
    for attribute in ("name", "size", "bold", "italic", "underline"):
        value = getattr(source_font, attribute)
        if value is not None:
            setattr(target_font, attribute, value)
    _copy_font_color(source_font.color, target_font.color)
    if source.type != WD_STYLE_TYPE.PARAGRAPH:
        return
    source_paragraph = source.paragraph_format
    target_paragraph = target.paragraph_format
    for attribute in (
        "alignment", "left_indent", "right_indent", "first_line_indent", "space_before",
        "space_after", "line_spacing", "keep_with_next", "keep_together", "page_break_before",
    ):
        value = getattr(source_paragraph, attribute)
        if value is not None:
            setattr(target_paragraph, attribute, value)


def _copy_font_color(source: Any, target: Any) -> None:
    """Copy an explicit color while retaining target values for inherited colors."""
    if source.rgb is not None:
        target.rgb = source.rgb
    elif source.theme_color is not None:
        target.theme_color = source.theme_color
