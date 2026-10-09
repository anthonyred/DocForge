"""Inspect formatting properties exposed by an arbitrary reference DOCX."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List
from zipfile import BadZipFile, ZipFile

from docx import Document
from docx.document import Document as DocumentObject
from docx.enum.style import WD_STYLE_TYPE
from docx.shared import Inches
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


def _points(value: Any) -> str:
    """Return a paragraph spacing value in points or mark it inherited."""
    return f"{value.pt:g} pt" if value is not None else "inherited"


def _alignment_label(paragraph_format: Any) -> str:
    """Describe alignment values, including valid OOXML values unknown to python-docx."""
    element = paragraph_format._element
    properties = getattr(element, "pPr", None)
    if properties is None:
        properties = element
    justification = properties.find(qn("w:jc"))
    raw_value = justification.get(qn("w:val")) if justification is not None else None
    try:
        alignment = paragraph_format.alignment
    except ValueError:
        return raw_value or "inherited"
    return str(alignment) if alignment is not None else raw_value or "inherited"


def _content_paragraphs(document: DocumentObject) -> Iterator[Paragraph]:
    """Iterate document paragraphs, including paragraphs in nested tables."""
    yield from document.paragraphs
    for table in document.tables:
        yield from _table_paragraphs(table)


def _table_paragraphs(table: Table) -> Iterator[Paragraph]:
    """Recursively yield paragraph content from a table and nested tables."""
    for row in table.rows:
        for cell in row.cells:
            yield from cell.paragraphs
            for nested in cell.tables:
                yield from _table_paragraphs(nested)


@dataclass
class ReferenceAnalysis:
    """Detected reference properties and their reproduction limits."""

    path: Path
    properties: Dict[str, str]
    mapped_styles: Dict[str, str]
    uncertain: List[str]
    unsupported: List[str]
    strategy: str

    def summary(self) -> str:
        """Format a concise analysis report for display in the UI."""
        lines = [f"Reference: {self.path.name}", "Detected properties:"]
        lines.extend(f"  {key}: {value}" for key, value in self.properties.items())
        lines.append("Pandoc style mapping:")
        lines.extend(f"  {key} → {value}" for key, value in self.mapped_styles.items())
        lines.append(f"Strategy: {self.strategy}")
        if self.uncertain:
            lines.append("Needs review: " + "; ".join(self.uncertain))
        if self.unsupported:
            lines.append("Not mapped: " + "; ".join(self.unsupported))
        return "\n".join(lines)


class ReferenceDocxAnalyzer:
    """Extract page, paragraph, run, table, header, and footer properties."""

    def analyze(self, path: Path) -> ReferenceAnalysis:
        """Validate and inspect a DOCX without modifying it."""
        self._validate_docx(path)
        document = Document(str(path))
        props = self._page_properties(document)
        props.update(self._text_properties(document))
        props.update(self._table_properties(document))
        props.update(self._break_properties(document))
        mapped = self._mapped_styles(document)
        uncertain = self._uncertain_properties(document)
        unsupported = ["embedded floating objects", "exact Word page layout fidelity"]
        strategy = "Pass this DOCX to Pandoc as --reference-doc; inspect generated styles after conversion."
        return ReferenceAnalysis(path, props, mapped, uncertain, unsupported, strategy)

    def mapped_styles(self, document: DocumentObject) -> Dict[str, str]:
        """Expose detected source styles for reference preparation."""
        return self._mapped_styles(document)

    @staticmethod
    def _validate_docx(path: Path) -> None:
        """Raise actionable errors for missing, inaccessible, or invalid files."""
        if path.suffix.lower() != ".docx":
            raise ValueError("Reference file must use the .docx extension.")
        if not path.is_file():
            raise FileNotFoundError(f"Reference DOCX does not exist: {path}")
        try:
            with ZipFile(path) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise ValueError("The selected file is not a valid Word DOCX document.")
        except BadZipFile as exc:
            raise ValueError("The selected reference DOCX is corrupt or not a valid ZIP document.") from exc
        try:
            Document(str(path))
        except Exception as exc:
            raise ValueError(f"Could not read reference DOCX: {exc}") from exc

    @staticmethod
    def _page_properties(document: DocumentObject) -> Dict[str, str]:
        """Describe dimensions and margins for the first section."""
        section = document.sections[0]
        width, height = section.page_width, section.page_height
        orientation = "landscape" if width is not None and height is not None and width > height else "portrait"
        page = f"{width / Inches(1):.2f} × {height / Inches(1):.2f} in, {orientation}" if width and height else "dimensions unavailable"
        margins = [section.top_margin, section.bottom_margin, section.left_margin, section.right_margin]
        margin_text = ", ".join(f"{name} {value / Inches(1):.2f}" if value is not None else f"{name} unset" for name, value in zip(("top", "bottom", "left", "right"), margins))
        layouts = []
        for index, current in enumerate(document.sections, 1):
            current_width, current_height = current.page_width, current.page_height
            current_margins = [current.top_margin, current.bottom_margin, current.left_margin, current.right_margin]
            margin_summary = "/".join(f"{value / Inches(1):.2f}" if value is not None else "?" for value in current_margins)
            layouts.append(
                f"{index}: {current_width / Inches(1):.2f}x{current_height / Inches(1):.2f} in, margins T/B/L/R {margin_summary}"
                if current_width and current_height else f"{index}: dimensions unavailable"
            )
        return {
            "Page": page,
            "Margins": margin_text + " in",
            "Section layouts": "; ".join(layouts),
        }

    @staticmethod
    def _text_properties(document: DocumentObject) -> Dict[str, str]:
        """Read Normal and heading styles plus header/footer content."""
        result: Dict[str, str] = {}
        for name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3", "Heading 4", "Heading 5", "Heading 6"):
            style = next((item for item in document.styles if item.name == name), None)
            if style is not None:
                result[name] = ReferenceDocxAnalyzer._describe_style(style)
        char_styles = [style.name for style in document.styles if style.type == WD_STYLE_TYPE.CHARACTER]
        result["Character styles"] = ", ".join(char_styles[:12]) or "none"
        code_styles = [name for name in char_styles if "code" in name.lower() or "verbatim" in name.lower()]
        result["Code styles"] = ", ".join(code_styles) or "none detected"
        headers = [p.text for section in document.sections for p in section.header.paragraphs if p.text]
        footers = [p.text for section in document.sections for p in section.footer.paragraphs if p.text]
        result["Headers"] = " | ".join(headers) if headers else "none visible as text"
        result["Footers"] = " | ".join(footers) if footers else "none visible as text"
        alignments = [_alignment_label(p.paragraph_format) for s in document.sections for p in (*s.header.paragraphs, *s.footer.paragraphs)]
        result["Header/footer alignment"] = ", ".join(sorted(set(alignments))) if alignments else "inherited"
        result["Page number fields"] = str(sum("PAGE" in p._p.xml for s in document.sections for p in s.footer.paragraphs))
        result["Direct formatting"] = str(ReferenceDocxAnalyzer._direct_format_count(document)) + " paragraphs/runs detected"
        return result

    @staticmethod
    def _describe_style(style: Any) -> str:
        """Summarize observable font and paragraph properties of a style."""
        font = style.font
        paragraph = style.paragraph_format
        color = font.color.rgb or font.color.theme_color or "inherited"
        font_info = f"{font.name or 'inherited'} {font.size.pt:g} pt" if font.size else f"{font.name or 'inherited'} size inherited"
        emphasis = f"bold={font.bold}, italic={font.italic}, color={color}"
        spacing = f"before={_points(paragraph.space_before)}, after={_points(paragraph.space_after)}"
        line = paragraph.line_spacing if paragraph.line_spacing is not None else "inherited"
        indent = (
            f"left={_points(paragraph.left_indent)}, right={_points(paragraph.right_indent)}, "
            f"first={_points(paragraph.first_line_indent)}"
        )
        return f"{font_info}; {emphasis}; alignment={_alignment_label(paragraph)}; {spacing}; line={line}; indent={indent}"

    @staticmethod
    def _direct_format_count(document: DocumentObject) -> int:
        """Count content paragraphs or runs carrying direct font formatting."""
        count = 0
        for paragraph in _content_paragraphs(document):
            if paragraph.paragraph_format.space_after or paragraph.paragraph_format.left_indent:
                count += 1
            if any(run.font.name or run.font.size or run.font.color.rgb for run in paragraph.runs):
                count += 1
        return count

    @staticmethod
    def _break_properties(document: DocumentObject) -> Dict[str, str]:
        """Count page breaks, section breaks, and list paragraph styles."""
        page_breaks = sum(p._p.xml.count('w:type="page"') for p in document.paragraphs)
        section_breaks = max(0, len(document.sections) - 1)
        list_styles = sorted({p.style.name for p in document.paragraphs if p.style and "list" in p.style.name.lower()})
        return {
            "Page breaks": str(page_breaks),
            "Section breaks": str(section_breaks),
            "List styles": ", ".join(list_styles) or "none detected",
        }

    @staticmethod
    def _table_properties(document: DocumentObject) -> Dict[str, str]:
        """Report table count and styles without inferring semantics."""
        styles = sorted({table.style.name for table in document.tables if table.style})
        formatting = ReferenceDocxAnalyzer._first_table_format(document)
        return {
            "Tables": f"{len(document.tables)}; styles: {', '.join(styles) if styles else 'none'}",
            "First table formatting": formatting,
        }

    @staticmethod
    def _first_table_format(document: DocumentObject) -> str:
        """Inspect first table's border and cell-shading declarations."""
        if not document.tables:
            return "not available"
        table = document.tables[0]
        tbl_pr = table._tbl.tblPr
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        borders = tbl_pr.find(f"{ns}tblBorders")
        cell_props = table.cell(0, 0)._tc.tcPr
        shading = cell_props.find(f"{ns}shd") if cell_props is not None else None
        margins = tbl_pr.find(f"{ns}tblCellMar")
        border_text = ", ".join(f"{item.tag.rsplit('}', 1)[-1]}:{item.get(f'{ns}val', 'default')}" for item in borders) if borders is not None else "inherited"
        fill = shading.get(f"{ns}fill") if shading is not None else "inherited"
        padding = ", ".join(f"{item.tag.rsplit('}', 1)[-1]}:{item.get(f'{ns}w', 'default')}" for item in margins) if margins is not None else "inherited"
        return f"borders={border_text}; first-cell fill={fill}; cell margins={padding}"

    @staticmethod
    def _mapped_styles(document: DocumentObject) -> Dict[str, str]:
        """Map common Markdown structures to styles present in the document."""
        available = {style.name for style in document.styles}
        mapping: Dict[str, str] = {}
        for markdown, candidates in {
            "Markdown H1": ("Heading 1", "Title"),
            "Markdown H2": ("Heading 2", "Heading 1"),
            "Markdown H3": ("Heading 3", "Heading 2"),
            "Markdown body": ("Body Text", "Normal"),
            "Markdown code": ("Source Code", "Verbatim Char", "Normal"),
            "Markdown quote": ("Block Text", "Quote", "Normal"),
        }.items():
            outline_style = ReferenceDocxAnalyzer._outline_style(document, markdown)
            named_style = ReferenceDocxAnalyzer._named_style(document, markdown, available)
            mapping[markdown] = outline_style or named_style or next((name for name in candidates if name in available), "Normal (fallback)")
        return mapping

    @staticmethod
    def _named_style(document: DocumentObject, markdown: str, available: set[str]) -> str:
        """Find custom paragraph styles with explicit code or quote semantics."""
        keywords = {"Markdown code": ("code", "verbatim"), "Markdown quote": ("quote", "block")}.get(markdown, ())
        for style in document.styles:
            if style.type == WD_STYLE_TYPE.PARAGRAPH and style.name in available:
                if any(keyword in style.name.lower() for keyword in keywords):
                    return style.name
        return ""

    @staticmethod
    def _outline_style(document: DocumentObject, markdown: str) -> str:
        """Prefer custom paragraph styles with explicit Word outline levels."""
        level = int(markdown[-1]) if markdown.startswith("Markdown H") else 0
        for style in document.styles:
            if style.type != WD_STYLE_TYPE.PARAGRAPH or style._element.pPr is None:
                continue
            if style.name == f"Heading {level}":
                continue
            outline = style._element.pPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}outlineLvl")
            if outline is not None and int(outline.val) == level - 1 and level:
                return style.name
        return ""

    @staticmethod
    def _uncertain_properties(document: DocumentObject) -> List[str]:
        """Identify formatting details that cannot be inferred from styles alone."""
        uncertain: List[str] = []
        if any(run.font.name or run.font.size for paragraph in _content_paragraphs(document) for run in paragraph.runs):
            uncertain.append("some paragraphs use direct run formatting")
        if any(section.different_first_page_header_footer for section in document.sections):
            uncertain.append("first-page header/footer differs")
        if any("Code" in style.name or "Verbatim" in style.name for style in document.styles):
            return uncertain
        uncertain.append("no clearly named code style was found")
        return uncertain
