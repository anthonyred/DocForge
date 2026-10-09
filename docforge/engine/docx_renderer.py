"""Pure Python Word (.docx) Document Renderer driven by Format Profiles."""

from pathlib import Path
from typing import Any, List, Optional

import docx
from docx import Document
from docx.document import Document as DocumentObject
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

from docforge.app.config import AppSettings
from docforge.engine.cover import CoverPageBuilder
from docforge.engine.export_interface import BaseRenderer, RendererRegistry
from docforge.engine.markdown_parser import ASTNode, MarkdownParser
from docforge.engine.profile import FormatProfile, HeadingStyle
from docforge.engine.style_mapper import (
    apply_blockquote_style,
    apply_code_block_paragraph_style,
    apply_paragraph_body_style,
    apply_paragraph_heading_style,
    apply_run_style,
    hex_to_rgb,
    parse_alignment,
    set_cell_background,
)


class DocxRenderer(BaseRenderer):
    """AST to .docx Document Renderer engine."""

    def __init__(self) -> None:
        """Initialize renderer instance."""
        self.cover_builder = CoverPageBuilder()
        self.parser_helper = MarkdownParser()
        self.heading_counters = [0, 0, 0, 0]

    def render(
        self,
        ast_nodes: List[ASTNode],
        profile: FormatProfile,
        settings: AppSettings,
        output_path: Path,
    ) -> Path:
        """Render Markdown AST into styled .docx document file.

        Args:
            ast_nodes: Parsed Markdown AST nodes.
            profile: Selected format profile rules.
            settings: User settings (author name, date format).
            output_path: Target .docx destination path.

        Returns:
            Path: Path to created .docx file.
        """
        doc: DocumentObject = Document()
        self.heading_counters = [0, 0, 0, 0]

        # Setup Page Geometry
        self._configure_page_setup(doc, profile)

        # Extract markdown title for cover page
        markdown_title = self.parser_helper.extract_first_h1(ast_nodes)

        # Render Cover Page
        self.cover_builder.build_cover_page(doc, profile, settings, markdown_title)

        # Configure Header and Footer on body section
        self._configure_header_footer(doc, profile)

        # Render Body AST Nodes
        for node in ast_nodes:
            self._render_node(doc, node, profile)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))
        return output_path

    def _configure_page_setup(self, doc: DocumentObject, profile: FormatProfile) -> None:
        """Apply page size, orientation, and cm margins to document sections."""
        section = doc.sections[0]
        pg_cfg = profile.page

        # Margins (cm)
        section.top_margin = Cm(pg_cfg.margin_top_cm)
        section.bottom_margin = Cm(pg_cfg.margin_bottom_cm)
        section.left_margin = Cm(pg_cfg.margin_left_cm)
        section.right_margin = Cm(pg_cfg.margin_right_cm)

        # Paper Size
        if pg_cfg.size.upper() == "LETTER":
            width, height = Cm(21.59), Cm(27.94)
        else:  # A4
            width, height = Cm(21.0), Cm(29.7)

        if pg_cfg.orientation.lower() == "landscape":
            section.orientation = WD_ORIENT.LANDSCAPE
            section.page_width, section.page_height = height, width
        else:
            section.orientation = WD_ORIENT.PORTRAIT
            section.page_width, section.page_height = width, height

    def _configure_header_footer(self, doc: DocumentObject, profile: FormatProfile) -> None:
        """Configure different first page header/footer and page numbering on body section."""
        section = doc.sections[0]
        section.different_first_page_header_footer = True
        pg_cfg = profile.page

        # Header on body pages
        if pg_cfg.header_text:
            header_p = section.header.paragraphs[0]
            header_p.text = pg_cfg.header_text
            header_p.paragraph_format.alignment = parse_alignment(pg_cfg.header_alignment)
            for run in header_p.runs:
                apply_run_style(run, font_name=profile.body.font_family, size_pt=9.0, color_hex="#718096", italic=True)

        # Footer on body pages
        if pg_cfg.footer_show_page_number or pg_cfg.footer_text:
            footer_p = section.footer.paragraphs[0]
            footer_p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            footer_p.text = ""

            run_text = footer_p.add_run("Page ")
            apply_run_style(run_text, font_name=profile.body.font_family, size_pt=9.0, color_hex="#718096")

            # Add PAGE field XML
            fld_xml = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls("w"))
            footer_p._p.append(fld_xml)

    def _render_node(self, doc: DocumentObject, node: ASTNode, profile: FormatProfile) -> None:
        """Recursively dispatch rendering for an AST Node."""
        ntype = node.type.lower()

        if ntype == "heading":
            self._render_heading(doc, node, profile)
        elif ntype == "paragraph":
            self._render_paragraph(doc, node, profile)
        elif ntype in ("block_code", "code_block"):
            self._render_code_block(doc, node, profile)
        elif ntype == "list":
            self._render_list(doc, node, profile)
        elif ntype == "table":
            self._render_table(doc, node, profile)
        elif ntype in ("block_quote", "blockquote"):
            self._render_blockquote(doc, node, profile)
        elif ntype == "thematic_break":
            self._render_horizontal_rule(doc, profile)
        else:
            # Fallback for unknown markdown constructs
            self._render_paragraph(doc, node, profile)

    def _render_heading(self, doc: DocumentObject, node: ASTNode, profile: FormatProfile) -> None:
        """Render heading node H1-H4 styled by profile."""
        lvl = min(max(node.level, 1), 4)
        h_config_map = {
            1: profile.headings.h1,
            2: profile.headings.h2,
            3: profile.headings.h3,
            4: profile.headings.h4,
        }
        h_style: HeadingStyle = h_config_map[lvl]

        p = doc.add_paragraph()
        
        # Heading numbering prefix if configured
        prefix = ""
        if h_style.numbering == "1.":
            self.heading_counters[lvl - 1] += 1
            prefix = f"{self.heading_counters[0]}. "
        elif h_style.numbering == "1.1":
            self.heading_counters[lvl - 1] += 1
            if lvl == 1:
                prefix = f"{self.heading_counters[0]}. "
            elif lvl == 2:
                prefix = f"{self.heading_counters[0]}.{self.heading_counters[1]} "
            elif lvl == 3:
                prefix = f"{self.heading_counters[0]}.{self.heading_counters[1]}.{self.heading_counters[2]} "

        if prefix:
            run_pfx = p.add_run(prefix)
            apply_run_style(run_pfx, font_name=h_style.font_family, size_pt=h_style.size_pt, color_hex=h_style.color, bold=h_style.bold)

        self._render_inline_children(p, node.children, profile, override_font=h_style.font_family, override_size=h_style.size_pt, override_color=h_style.color, override_bold=h_style.bold)
        apply_paragraph_heading_style(p, h_style)

    def _render_paragraph(self, doc: DocumentObject, node: ASTNode, profile: FormatProfile) -> None:
        """Render body text paragraph."""
        p = doc.add_paragraph()
        self._render_inline_children(p, node.children, profile)
        apply_paragraph_body_style(p, profile.body)

    def _render_inline_children(
        self,
        p: Paragraph,
        children: List[ASTNode],
        profile: FormatProfile,
        override_font: Optional[str] = None,
        override_size: Optional[float] = None,
        override_color: Optional[str] = None,
        override_bold: Optional[bool] = None,
        override_italic: Optional[bool] = None,
    ) -> None:
        """Recursively render inline AST nodes (text, strong, emphasis, codespan, link, image)."""
        font = override_font or profile.body.font_family
        size = override_size or profile.body.size_pt
        color = override_color or profile.body.color

        for child in children:
            ctype = child.type.lower()

            if ctype == "text":
                run = p.add_run(child.raw)
                apply_run_style(run, font_name=font, size_pt=size, color_hex=color, bold=override_bold, italic=override_italic)

            elif ctype == "strong":
                self._render_inline_children(p, child.children, profile, override_font=font, override_size=size, override_color=color, override_bold=True, override_italic=override_italic)

            elif ctype in ("emphasis", "em"):
                self._render_inline_children(p, child.children, profile, override_font=font, override_size=size, override_color=color, override_bold=override_bold, override_italic=True)

            elif ctype == "codespan":
                ic = profile.inline_code
                run = p.add_run(child.raw)
                apply_run_style(run, font_name=ic.font_family, size_pt=ic.size_pt, color_hex=ic.color)

            elif ctype == "link":
                link_text = self.parser_helper.get_node_text(child)
                run = p.add_run(link_text)
                apply_run_style(run, font_name=font, size_pt=size, color_hex="#2B6CB0", italic=False)
                run.font.underline = True

            elif ctype == "image":
                img_url = child.attrs.get("url", "")
                if img_url and Path(img_url).exists():
                    try:
                        run = p.add_run()
                        run.add_picture(img_url, width=Cm(12.0))
                    except Exception:
                        run = p.add_run(f"[Image: {img_url}]")
                        apply_run_style(run, font_name=font, size_pt=size, color_hex=color, italic=True)
                else:
                    run = p.add_run(f"[Image: {img_url if img_url else 'embedded'}]")
                    apply_run_style(run, font_name=font, size_pt=size, color_hex=color, italic=True)

            else:
                if child.raw:
                    run = p.add_run(child.raw)
                    apply_run_style(run, font_name=font, size_pt=size, color_hex=color, bold=override_bold, italic=override_italic)
                elif child.children:
                    self._render_inline_children(p, child.children, profile, override_font=font, override_size=size, override_color=color, override_bold=override_bold, override_italic=override_italic)

    def _render_code_block(self, doc: DocumentObject, node: ASTNode, profile: FormatProfile) -> None:
        """Render code block AST node with background box, border, and preserved language tag."""
        cfg = profile.code_block
        lines = node.raw.rstrip().split("\n")

        for line in lines:
            p = doc.add_paragraph()
            run = p.add_run(line if line else " ")
            apply_run_style(run, font_name=cfg.font_family, size_pt=cfg.size_pt, color_hex=cfg.color)
            apply_code_block_paragraph_style(p, cfg)

    def _render_list(self, doc: DocumentObject, node: ASTNode, profile: FormatProfile, indent_level: int = 0) -> None:
        """Render ordered or unordered list node."""
        is_ordered = node.ordered
        idx = 1
        for item_node in node.children:
            if item_node.type == "list_item":
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(profile.lists.indent_cm * (indent_level + 1))
                p.paragraph_format.space_after = Pt(profile.lists.space_after_pt)

                prefix = f"{idx}. " if is_ordered else "• "
                run_pfx = p.add_run(prefix)
                apply_run_style(run_pfx, font_name=profile.body.font_family, size_pt=profile.body.size_pt, color_hex=profile.body.color, bold=True)

                for child in item_node.children:
                    if child.type == "list":
                        self._render_list(doc, child, profile, indent_level=indent_level + 1)
                    elif child.type == "paragraph":
                        self._render_inline_children(p, child.children, profile)
                    else:
                        self._render_inline_children(p, [child], profile)
                idx += 1

    def _render_table(self, doc: DocumentObject, node: ASTNode, profile: FormatProfile) -> None:
        """Render table node with header styling and alternate row shading."""
        tbl_cfg = profile.tables
        rows_nodes = []
        for child in node.children:
            if child.type in ("table_head", "table_body"):
                for row_child in child.children:
                    if row_child.type == "table_row":
                        rows_nodes.append((child.type == "table_head", row_child))

        if not rows_nodes:
            return

        cols_count = max(len(row.children) for is_head, row in rows_nodes)
        table = doc.add_table(rows=len(rows_nodes), cols=cols_count)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for row_idx, (is_header, row_node) in enumerate(rows_nodes):
            row = table.rows[row_idx]
            for col_idx, cell_node in enumerate(row_node.children):
                if col_idx < len(row.cells):
                    cell = row.cells[col_idx]
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_after = Pt(2.0)

                    if is_header:
                        set_cell_background(cell, tbl_cfg.header_background_color)
                        self._render_inline_children(p, cell_node.children, profile, override_bold=tbl_cfg.header_font_bold, override_color=tbl_cfg.header_font_color)
                    else:
                        if row_idx % 2 == 1:
                            set_cell_background(cell, tbl_cfg.row_alternate_background_color)
                        self._render_inline_children(p, cell_node.children, profile)

    def _render_blockquote(self, doc: DocumentObject, node: ASTNode, profile: FormatProfile) -> None:
        """Render blockquote paragraph with left border and italic formatting."""
        p = doc.add_paragraph()
        self._render_inline_children(p, node.children, profile)
        apply_blockquote_style(p, profile.blockquotes)

    def _render_horizontal_rule(self, doc: DocumentObject, profile: FormatProfile) -> None:
        """Render horizontal rule paragraph."""
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12.0)
        p.paragraph_format.space_after = Pt(12.0)
        pPr = p._p.get_or_add_pPr()
        pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" w:color="CBD5E0"/></w:pBdr>')
        pPr.append(pBdr)


# Register DocxRenderer in global registry
RendererRegistry.register("docx", DocxRenderer)
