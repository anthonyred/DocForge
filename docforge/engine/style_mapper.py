"""Maps profile formatting rules into python-docx style properties and OpenXML elements."""

from typing import Any, Optional
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from docforge.engine.profile import (
    BlockquotesConfig,
    BodyStyle,
    CodeBlockStyle,
    HeadingStyle,
    InlineCodeStyle,
    PageConfig,
    TablesConfig,
)


def hex_to_rgb(hex_str: str) -> RGBColor:
    """Convert hex string (e.g. '#1B365D' or '1B365D') to python-docx RGBColor."""
    clean_hex = hex_str.lstrip("#")
    if len(clean_hex) != 6:
        clean_hex = "000000"
    return RGBColor.from_string(clean_hex)


def parse_alignment(alignment_str: str) -> WD_ALIGN_PARAGRAPH:
    """Map alignment string to WD_ALIGN_PARAGRAPH enum."""
    align_map = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
    }
    return align_map.get(alignment_str.lower(), WD_ALIGN_PARAGRAPH.LEFT)


def apply_run_style(
    run: Run,
    font_name: Optional[str] = None,
    size_pt: Optional[float] = None,
    color_hex: Optional[str] = None,
    bold: Optional[bool] = None,
    italic: Optional[bool] = None,
) -> None:
    """Apply inline font parameters to a python-docx Run object."""
    if font_name:
        run.font.name = font_name
    if size_pt is not None:
        run.font.size = Pt(size_pt)
    if color_hex:
        run.font.color.rgb = hex_to_rgb(color_hex)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def apply_paragraph_body_style(p: Paragraph, body: BodyStyle) -> None:
    """Apply body text formatting rules to a paragraph."""
    p.paragraph_format.alignment = parse_alignment(body.alignment)
    p.paragraph_format.line_spacing = body.line_spacing
    p.paragraph_format.space_after = Pt(body.space_after_pt)
    for run in p.runs:
        apply_run_style(run, font_name=body.font_family, size_pt=body.size_pt, color_hex=body.color)


def apply_paragraph_heading_style(p: Paragraph, style: HeadingStyle) -> None:
    """Apply heading formatting rules to a paragraph."""
    p.paragraph_format.space_before = Pt(style.space_before_pt)
    p.paragraph_format.space_after = Pt(style.space_after_pt)
    for run in p.runs:
        apply_run_style(
            run,
            font_name=style.font_family,
            size_pt=style.size_pt,
            color_hex=style.color,
            bold=style.bold,
            italic=style.italic,
        )


def set_cell_background(cell: Any, hex_color: str) -> None:
    """Set table cell background shading color using OpenXML."""
    clean_hex = hex_color.lstrip("#")
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{clean_hex}"/>')
    tcPr.append(shd)


def apply_blockquote_style(p: Paragraph, config: BlockquotesConfig) -> None:
    """Apply blockquote background, left border, and indent styling using OpenXML."""
    p.paragraph_format.left_indent = Cm(config.indent_cm)
    p.paragraph_format.space_after = Pt(6.0)

    pPr = p._p.get_or_add_pPr()
    border_hex = config.left_border_color.lstrip("#")
    bg_hex = config.background_color.lstrip("#")

    # Add left border
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:left w:val="single" w:sz="24" w:space="12" w:color="{border_hex}"/></w:pBdr>')
    pPr.append(pBdr)

    # Add background shading
    if bg_hex:
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_hex}"/>')
        pPr.append(shd)

    for run in p.runs:
        apply_run_style(
            run,
            font_name=config.font_family,
            size_pt=config.size_pt,
            color_hex=config.color,
            italic=config.italic,
        )


def apply_code_block_paragraph_style(p: Paragraph, config: CodeBlockStyle) -> None:
    """Apply container background and border styling to code block paragraphs."""
    p.paragraph_format.space_before = Pt(config.space_before_pt)
    p.paragraph_format.space_after = Pt(config.space_after_pt)
    p.paragraph_format.left_indent = Cm(0.5)
    p.paragraph_format.right_indent = Cm(0.5)

    pPr = p._p.get_or_add_pPr()
    bg_hex = config.background_color.lstrip("#")
    border_hex = config.border_color.lstrip("#")

    # Shading
    if bg_hex:
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_hex}"/>')
        pPr.append(shd)

    # Box border
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="4" w:color="{border_hex}"/>'
        f'<w:left w:val="single" w:sz="4" w:space="4" w:color="{border_hex}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="4" w:color="{border_hex}"/>'
        f'<w:right w:val="single" w:sz="4" w:space="4" w:color="{border_hex}"/>'
        f'</w:pBdr>'
    )
    pPr.append(pBdr)

    for run in p.runs:
        apply_run_style(
            run,
            font_name=config.font_family,
            size_pt=config.size_pt,
            color_hex=config.color,
        )
