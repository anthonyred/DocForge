"""Format profile schema, validation, serialization, and migration logic."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class CoverAuthorStyle:
    """Styling for author line on cover page."""

    font: str = "Segoe UI"
    size: float = 12.0
    color: str = "#4A5568"
    italic: bool = False


@dataclass
class CoverDateStyle:
    """Styling for date line on cover page."""

    font: str = "Segoe UI"
    size: float = 11.0
    color: str = "#718096"
    italic: bool = True


@dataclass
class CoverConfig:
    """Cover page layout and content configuration."""

    enabled: bool = True
    title_source: str = "markdown_h1"  # "markdown_h1" or "profile_defined"
    custom_title: str = ""
    subtitle: str = "Technical Document"
    doc_type: str = "SPECIFICATION"
    version: str = "v1.0"
    company: str = "DocForge"
    logo_path: str = ""
    layout: str = "executive_modern"  # "executive_modern", "classic_centered", "accent_banner", "minimal_left"
    accent_color: str = "#1B365D"
    title_font: str = "Segoe UI"
    title_size: float = 30.0
    title_bold: bool = True
    title_color: str = "#1B365D"
    author_style: CoverAuthorStyle = field(default_factory=CoverAuthorStyle)
    date_style: CoverDateStyle = field(default_factory=CoverDateStyle)


@dataclass
class BodyStyle:
    """Body text paragraph styling configuration."""

    font_family: str = "Segoe UI"
    size_pt: float = 11.0
    color: str = "#2D3748"
    line_spacing: float = 1.15
    space_after_pt: float = 6.0
    alignment: str = "left"  # left, center, right, justify


@dataclass
class HeadingStyle:
    """Heading level styling configuration."""

    font_family: str = "Segoe UI Semibold"
    size_pt: float = 18.0
    bold: bool = True
    italic: bool = False
    color: str = "#1B365D"
    space_before_pt: float = 12.0
    space_after_pt: float = 6.0
    numbering: str = "none"  # "none", "1.", "1.1"


@dataclass
class HeadingsConfig:
    """Headings collection configuration (H1 to H4)."""

    h1: HeadingStyle = field(
        default_factory=lambda: HeadingStyle(
            font_family="Segoe UI Semibold", size_pt=22.0, bold=True, color="#1B365D", space_before_pt=18.0, space_after_pt=8.0
        )
    )
    h2: HeadingStyle = field(
        default_factory=lambda: HeadingStyle(
            font_family="Segoe UI Semibold", size_pt=16.0, bold=True, color="#2B6CB0", space_before_pt=14.0, space_after_pt=6.0
        )
    )
    h3: HeadingStyle = field(
        default_factory=lambda: HeadingStyle(
            font_family="Segoe UI", size_pt=13.0, bold=True, color="#2D3748", space_before_pt=10.0, space_after_pt=4.0
        )
    )
    h4: HeadingStyle = field(
        default_factory=lambda: HeadingStyle(
            font_family="Segoe UI", size_pt=11.0, bold=True, italic=True, color="#4A5568", space_before_pt=8.0, space_after_pt=4.0
        )
    )


@dataclass
class CodeBlockStyle:
    """Code block container styling configuration."""

    font_family: str = "Consolas"
    size_pt: float = 9.5
    color: str = "#24292E"
    background_color: str = "#F6F8FA"
    border_color: str = "#E1E4E8"
    border_size_pt: float = 0.5
    space_before_pt: float = 6.0
    space_after_pt: float = 6.0


@dataclass
class InlineCodeStyle:
    """Inline code span styling configuration."""

    font_family: str = "Consolas"
    size_pt: float = 10.0
    color: str = "#D73A49"
    background_color: str = "#F0F3F6"


@dataclass
class ListsConfig:
    """Bullet and ordered list styling configuration."""

    bullet_style: str = "disc"
    space_after_pt: float = 3.0
    indent_cm: float = 0.63


@dataclass
class TablesConfig:
    """Table structure and header styling configuration."""

    header_font_bold: bool = True
    header_font_color: str = "#FFFFFF"
    header_background_color: str = "#1B365D"
    row_alternate_background_color: str = "#F8FAFC"
    border_color: str = "#CBD5E0"
    border_size_pt: float = 0.5
    cell_padding_cm: float = 0.2


@dataclass
class BlockquotesConfig:
    """Blockquote styling configuration."""

    font_family: str = "Segoe UI"
    size_pt: float = 10.5
    italic: bool = True
    color: str = "#4A5568"
    left_border_color: str = "#3182CE"
    left_border_size_pt: float = 3.0
    indent_cm: float = 0.8
    background_color: str = "#EBF8FF"


@dataclass
class PageConfig:
    """Page layout, margins, headers, and footers configuration."""

    size: str = "A4"  # A4 or Letter
    orientation: str = "portrait"  # portrait or landscape
    margin_top_cm: float = 2.5
    margin_bottom_cm: float = 2.5
    margin_left_cm: float = 2.5
    margin_right_cm: float = 2.5
    header_text: str = ""
    header_alignment: str = "right"
    footer_show_page_number: bool = True
    footer_text: str = "Page {page}"


@dataclass
class FormatProfile:
    """Root format profile schema container."""

    name: str = "Default Profile"
    description: str = "Default document formatting profile."
    profile_version: int = 1
    cover: CoverConfig = field(default_factory=CoverConfig)
    body: BodyStyle = field(default_factory=BodyStyle)
    headings: HeadingsConfig = field(default_factory=HeadingsConfig)
    code_block: CodeBlockStyle = field(default_factory=CodeBlockStyle)
    inline_code: InlineCodeStyle = field(default_factory=InlineCodeStyle)
    lists: ListsConfig = field(default_factory=ListsConfig)
    tables: TablesConfig = field(default_factory=TablesConfig)
    blockquotes: BlockquotesConfig = field(default_factory=BlockquotesConfig)
    page: PageConfig = field(default_factory=PageConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize profile instance to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormatProfile":
        """Construct FormatProfile from dictionary with validation and schema migration."""
        data = migrate_profile_data(data)
        
        cover_data = data.get("cover", {})
        author_data = cover_data.get("author_style", {})
        date_data = cover_data.get("date_style", {})
        
        cover = CoverConfig(
            enabled=cover_data.get("enabled", True),
            title_source=cover_data.get("title_source", "markdown_h1"),
            custom_title=cover_data.get("custom_title", ""),
            subtitle=cover_data.get("subtitle", "Technical Document"),
            doc_type=cover_data.get("doc_type", "SPECIFICATION"),
            version=cover_data.get("version", "v1.0"),
            company=cover_data.get("company", "DocForge"),
            logo_path=cover_data.get("logo_path", ""),
            layout=cover_data.get("layout", "executive_modern"),
            accent_color=cover_data.get("accent_color", "#1B365D"),
            title_font=cover_data.get("title_font", "Segoe UI"),
            title_size=float(cover_data.get("title_size", 30.0)),
            title_bold=cover_data.get("title_bold", True),
            title_color=cover_data.get("title_color", "#1B365D"),
            author_style=CoverAuthorStyle(
                font=author_data.get("font", "Segoe UI"),
                size=float(author_data.get("size", 12.0)),
                color=author_data.get("color", "#4A5568"),
                italic=author_data.get("italic", False),
            ),
            date_style=CoverDateStyle(
                font=date_data.get("font", "Segoe UI"),
                size=float(date_data.get("size", 11.0)),
                color=date_data.get("color", "#718096"),
                italic=date_data.get("italic", True),
            ),
        )

        headings_data = data.get("headings", {})
        headings = HeadingsConfig(
            h1=_parse_heading(headings_data.get("h1", {}), default_size=22.0, default_color="#1B365D"),
            h2=_parse_heading(headings_data.get("h2", {}), default_size=16.0, default_color="#2B6CB0"),
            h3=_parse_heading(headings_data.get("h3", {}), default_size=13.0, default_color="#2D3748"),
            h4=_parse_heading(headings_data.get("h4", {}), default_size=11.0, default_color="#4A5568", default_italic=True),
        )

        body_data = data.get("body", {})
        body = BodyStyle(
            font_family=body_data.get("font_family", "Segoe UI"),
            size_pt=float(body_data.get("size_pt", 11.0)),
            color=body_data.get("color", "#2D3748"),
            line_spacing=float(body_data.get("line_spacing", 1.15)),
            space_after_pt=float(body_data.get("space_after_pt", 6.0)),
            alignment=body_data.get("alignment", "left"),
        )

        code_data = data.get("code_block", {})
        code_block = CodeBlockStyle(
            font_family=code_data.get("font_family", "Consolas"),
            size_pt=float(code_data.get("size_pt", 9.5)),
            color=code_data.get("color", "#24292E"),
            background_color=code_data.get("background_color", "#F6F8FA"),
            border_color=code_data.get("border_color", "#E1E4E8"),
            border_size_pt=float(code_data.get("border_size_pt", 0.5)),
            space_before_pt=float(code_data.get("space_before_pt", 6.0)),
            space_after_pt=float(code_data.get("space_after_pt", 6.0)),
        )

        inline_data = data.get("inline_code", {})
        inline_code = InlineCodeStyle(
            font_family=inline_data.get("font_family", "Consolas"),
            size_pt=float(inline_data.get("size_pt", 10.0)),
            color=inline_data.get("color", "#D73A49"),
            background_color=inline_data.get("background_color", "#F0F3F6"),
        )

        list_data = data.get("lists", {})
        lists = ListsConfig(
            bullet_style=list_data.get("bullet_style", "disc"),
            space_after_pt=float(list_data.get("space_after_pt", 3.0)),
            indent_cm=float(list_data.get("indent_cm", 0.63)),
        )

        tbl_data = data.get("tables", {})
        tables = TablesConfig(
            header_font_bold=tbl_data.get("header_font_bold", True),
            header_font_color=tbl_data.get("header_font_color", "#FFFFFF"),
            header_background_color=tbl_data.get("header_background_color", "#1B365D"),
            row_alternate_background_color=tbl_data.get("row_alternate_background_color", "#F8FAFC"),
            border_color=tbl_data.get("border_color", "#CBD5E0"),
            border_size_pt=float(tbl_data.get("border_size_pt", 0.5)),
            cell_padding_cm=float(tbl_data.get("cell_padding_cm", 0.2)),
        )

        bq_data = data.get("blockquotes", {})
        blockquotes = BlockquotesConfig(
            font_family=bq_data.get("font_family", "Segoe UI"),
            size_pt=float(bq_data.get("size_pt", 10.5)),
            italic=bq_data.get("italic", True),
            color=bq_data.get("color", "#4A5568"),
            left_border_color=bq_data.get("left_border_color", "#3182CE"),
            left_border_size_pt=float(bq_data.get("left_border_size_pt", 3.0)),
            indent_cm=float(bq_data.get("indent_cm", 0.8)),
            background_color=bq_data.get("background_color", "#EBF8FF"),
        )

        pg_data = data.get("page", {})
        page = PageConfig(
            size=pg_data.get("size", "A4"),
            orientation=pg_data.get("orientation", "portrait"),
            margin_top_cm=float(pg_data.get("margin_top_cm", 2.5)),
            margin_bottom_cm=float(pg_data.get("margin_bottom_cm", 2.5)),
            margin_left_cm=float(pg_data.get("margin_left_cm", 2.5)),
            margin_right_cm=float(pg_data.get("margin_right_cm", 2.5)),
            header_text=pg_data.get("header_text", ""),
            header_alignment=pg_data.get("header_alignment", "right"),
            footer_show_page_number=pg_data.get("footer_show_page_number", True),
            footer_text=pg_data.get("footer_text", "Page {page}"),
        )

        return cls(
            name=data.get("name", "Unnamed Profile"),
            description=data.get("description", ""),
            profile_version=data.get("profile_version", 1),
            cover=cover,
            body=body,
            headings=headings,
            code_block=code_block,
            inline_code=inline_code,
            lists=lists,
            tables=tables,
            blockquotes=blockquotes,
            page=page,
        )

    def save_to_file(self, file_path: Path) -> None:
        """Save format profile to JSON file."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, file_path: Path) -> "FormatProfile":
        """Load format profile from JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)


def _parse_heading(data: Dict[str, Any], default_size: float, default_color: str, default_italic: bool = False) -> HeadingStyle:
    """Helper function to parse heading dictionary with robust defaults."""
    return HeadingStyle(
        font_family=data.get("font_family", "Segoe UI Semibold"),
        size_pt=float(data.get("size_pt", default_size)),
        bold=data.get("bold", True),
        italic=data.get("italic", default_italic),
        color=data.get("color", default_color),
        space_before_pt=float(data.get("space_before_pt", 12.0)),
        space_after_pt=float(data.get("space_after_pt", 6.0)),
        numbering=data.get("numbering", "none"),
    )


def migrate_profile_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Extensibility migration hook to upgrade older JSON profile versions to current schema."""
    version = data.get("profile_version", 0)
    if version < 1:
        data["profile_version"] = 1
    return data
