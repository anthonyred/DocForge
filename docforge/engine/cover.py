"""Profile-driven cover page builder module for python-docx documents."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from docx.document import Document as DocumentObject
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Cm, Pt

from docforge.app.config import AppSettings
from docforge.engine.profile import CoverConfig, FormatProfile
from docforge.engine.style_mapper import apply_run_style, parse_alignment, set_cell_background


class CoverPageBuilder:
    """Builds profile-driven cover pages according to profile layout specifications."""

    def build_cover_page(
        self,
        doc: DocumentObject,
        profile: FormatProfile,
        settings: AppSettings,
        markdown_title: Optional[str] = None,
    ) -> None:
        """Construct cover page in document according to profile configuration and settings.

        Args:
            doc: Target python-docx Document object.
            profile: Selected FormatProfile instance.
            settings: Current application settings containing author name and date format.
            markdown_title: Optional document title extracted from Markdown H1.
        """
        cover_config = profile.cover
        if not cover_config.enabled:
            return

        # Determine document title
        if cover_config.title_source == "markdown_h1" and markdown_title:
            title_text = markdown_title
        elif cover_config.custom_title:
            title_text = cover_config.custom_title
        elif markdown_title:
            title_text = markdown_title
        else:
            title_text = "Untitled Document"

        # Author and date resolution
        author_text = settings.author_name if settings.author_name else "Anthony Reddy"
        date_format = settings.date_format if settings.date_format else "%B %d, %Y"
        date_text = datetime.now().strftime(date_format)

        # Dispatch layout builder
        layout_name = cover_config.layout.lower()
        if layout_name == "accent_banner":
            self._build_accent_banner_layout(doc, cover_config, title_text, author_text, date_text)
        elif layout_name == "classic_centered":
            self._build_classic_centered_layout(doc, cover_config, title_text, author_text, date_text)
        elif layout_name == "minimal_left":
            self._build_minimal_left_layout(doc, cover_config, title_text, author_text, date_text)
        else:  # Default executive_modern
            self._build_executive_modern_layout(doc, cover_config, title_text, author_text, date_text)

        # Insert page break after cover
        doc.add_page_break()

    def _build_executive_modern_layout(
        self,
        doc: DocumentObject,
        config: CoverConfig,
        title: str,
        author: str,
        date_str: str,
    ) -> None:
        """Executive Modern Layout: Accent top bar, doc type tag, bold title, metadata block."""
        # Top space
        p_top = doc.add_paragraph()
        p_top.paragraph_format.space_before = Pt(36.0)

        # Optional Logo Image
        if config.logo_path and Path(config.logo_path).exists():
            try:
                p_logo = doc.add_paragraph()
                p_logo.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run_logo = p_logo.add_run()
                run_logo.add_picture(config.logo_path, width=Cm(4.0))
            except Exception:
                pass

        # Doc Type / Company pill tag
        p_tag = doc.add_paragraph()
        p_tag.paragraph_format.space_before = Pt(24.0)
        p_tag.paragraph_format.space_after = Pt(12.0)
        tag_text = f"{config.doc_type} | {config.company} {config.version}".strip(" |")
        run_tag = p_tag.add_run(tag_text.upper())
        apply_run_style(run_tag, font_name=config.title_font, size_pt=10.0, color_hex=config.accent_color, bold=True)

        # Main Title
        p_title = doc.add_paragraph()
        p_title.paragraph_format.space_before = Pt(12.0)
        p_title.paragraph_format.space_after = Pt(8.0)
        run_title = p_title.add_run(title)
        apply_run_style(
            run_title,
            font_name=config.title_font,
            size_pt=config.title_size,
            color_hex=config.title_color,
            bold=config.title_bold,
        )

        # Subtitle
        if config.subtitle:
            p_sub = doc.add_paragraph()
            p_sub.paragraph_format.space_after = Pt(48.0)
            run_sub = p_sub.add_run(config.subtitle)
            apply_run_style(run_sub, font_name=config.title_font, size_pt=14.0, color_hex="#718096", italic=True)

        # Horizontal accent rule
        p_rule = doc.add_paragraph()
        p_rule.paragraph_format.space_after = Pt(72.0)
        pPr = p_rule._p.get_or_add_pPr()
        accent_hex = config.accent_color.lstrip("#")
        pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="18" w:space="1" w:color="{accent_hex}"/></w:pBdr>')
        pPr.append(pBdr)

        # Author line
        p_author = doc.add_paragraph()
        p_author.paragraph_format.space_after = Pt(4.0)
        run_auth_label = p_author.add_run("Author: ")
        apply_run_style(run_auth_label, font_name=config.author_style.font, size_pt=config.author_style.size, color_hex="#718096", bold=True)
        run_auth_val = p_author.add_run(author)
        apply_run_style(
            run_auth_val,
            font_name=config.author_style.font,
            size_pt=config.author_style.size,
            color_hex=config.author_style.color,
            italic=config.author_style.italic,
        )

        # Date line
        p_date = doc.add_paragraph()
        run_date_label = p_date.add_run("Date: ")
        apply_run_style(run_date_label, font_name=config.date_style.font, size_pt=config.date_style.size, color_hex="#718096", bold=True)
        run_date_val = p_date.add_run(date_str)
        apply_run_style(
            run_date_val,
            font_name=config.date_style.font,
            size_pt=config.date_style.size,
            color_hex=config.date_style.color,
            italic=config.date_style.italic,
        )

    def _build_classic_centered_layout(
        self,
        doc: DocumentObject,
        config: CoverConfig,
        title: str,
        author: str,
        date_str: str,
    ) -> None:
        """Classic Centered Layout."""
        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(72.0)

        p_title = doc.add_paragraph()
        p_title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_after = Pt(12.0)
        run_title = p_title.add_run(title)
        apply_run_style(run_title, font_name=config.title_font, size_pt=config.title_size, color_hex=config.title_color, bold=True)

        if config.subtitle:
            p_sub = doc.add_paragraph()
            p_sub.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_sub.paragraph_format.space_after = Pt(96.0)
            run_sub = p_sub.add_run(config.subtitle)
            apply_run_style(run_sub, font_name=config.title_font, size_pt=13.0, color_hex="#4A5568", italic=True)

        p_auth = doc.add_paragraph()
        p_auth.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_auth.paragraph_format.space_after = Pt(4.0)
        run_auth = p_auth.add_run(author)
        apply_run_style(run_auth, font_name=config.author_style.font, size_pt=12.0, color_hex=config.author_style.color)

        p_date = doc.add_paragraph()
        p_date.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_date = p_date.add_run(date_str)
        apply_run_style(run_date, font_name=config.date_style.font, size_pt=11.0, color_hex=config.date_style.color, italic=True)

    def _build_accent_banner_layout(
        self,
        doc: DocumentObject,
        config: CoverConfig,
        title: str,
        author: str,
        date_str: str,
    ) -> None:
        """Accent Banner Layout: Colored header block banner."""
        table = doc.add_table(rows=1, cols=1)
        table.autofit = False
        cell = table.cell(0, 0)
        set_cell_background(cell, config.accent_color)

        p_banner = cell.paragraphs[0]
        p_banner.paragraph_format.space_before = Pt(24.0)
        p_banner.paragraph_format.space_after = Pt(24.0)
        p_banner.paragraph_format.left_indent = Cm(0.5)

        run_title = p_banner.add_run(title)
        apply_run_style(run_title, font_name=config.title_font, size_pt=config.title_size, color_hex="#FFFFFF", bold=True)

        p_meta = doc.add_paragraph()
        p_meta.paragraph_format.space_before = Pt(96.0)
        run_meta = p_meta.add_run(f"Prepared by: {author}\nDate: {date_str}")
        apply_run_style(run_meta, font_name=config.author_style.font, size_pt=11.0, color_hex="#4A5568")

    def _build_minimal_left_layout(
        self,
        doc: DocumentObject,
        config: CoverConfig,
        title: str,
        author: str,
        date_str: str,
    ) -> None:
        """Minimal Left Layout."""
        p_space = doc.add_paragraph()
        p_space.paragraph_format.space_before = Pt(48.0)

        p_title = doc.add_paragraph()
        p_title.paragraph_format.space_after = Pt(12.0)
        run_title = p_title.add_run(title)
        apply_run_style(run_title, font_name=config.title_font, size_pt=config.title_size, color_hex=config.title_color, bold=True)

        p_meta = doc.add_paragraph()
        p_meta.paragraph_format.space_before = Pt(48.0)
        run_meta = p_meta.add_run(f"{author}  |  {date_str}")
        apply_run_style(run_meta, font_name=config.author_style.font, size_pt=11.0, color_hex="#718096")
