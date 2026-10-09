"""Common export Renderer interface and pluggable renderer registry."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Type

from docforge.app.config import AppSettings
from docforge.engine.markdown_parser import ASTNode
from docforge.engine.profile import FormatProfile


class BaseRenderer(ABC):
    """Abstract Base Class for all document renderers (DOCX, PDF, HTML)."""

    @abstractmethod
    def render(
        self,
        ast_nodes: List[ASTNode],
        profile: FormatProfile,
        settings: AppSettings,
        output_path: Path,
    ) -> Path:
        """Render parsed Markdown AST into target format file.

        Args:
            ast_nodes: Parsed Markdown abstract syntax tree nodes.
            profile: Target format profile.
            settings: Current application configuration settings.
            output_path: Target destination file path.

        Returns:
            Path: Absolute path to rendered document file.
        """
        pass


class RendererRegistry:
    """Plugin-style registry for document export renderers."""

    _renderers: Dict[str, Type[BaseRenderer]] = {}

    @classmethod
    def register(cls, format_key: str, renderer_cls: Type[BaseRenderer]) -> None:
        """Register a new format renderer plugin."""
        cls._renderers[format_key.lower()] = renderer_cls

    @classmethod
    def get_renderer(cls, format_key: str) -> BaseRenderer:
        """Instantiate and return renderer registered for specified format key."""
        key = format_key.lower()
        if key not in cls._renderers:
            raise ValueError(f"No document renderer registered for format '{format_key}'.")
        return cls._renderers[key]()


class PdfRendererStub(BaseRenderer):
    """Extension Stub: PDF export renderer hook."""

    def render(
        self,
        ast_nodes: List[ASTNode],
        profile: FormatProfile,
        settings: AppSettings,
        output_path: Path,
    ) -> Path:
        raise NotImplementedError("PDF export extension will be available in future releases.")


class HtmlRendererStub(BaseRenderer):
    """Extension Stub: HTML export renderer hook."""

    def render(
        self,
        ast_nodes: List[ASTNode],
        profile: FormatProfile,
        settings: AppSettings,
        output_path: Path,
    ) -> Path:
        raise NotImplementedError("HTML export extension will be available in future releases.")
