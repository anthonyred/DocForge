"""Markdown AST parser module built on mistune 3.x AST walker."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import mistune
from mistune.plugins.table import table


@dataclass
class ASTNode:
    """Standardized Markdown AST Node representation."""

    type: str
    children: List["ASTNode"] = field(default_factory=list)
    raw: str = ""
    attrs: Dict[str, Any] = field(default_factory=dict)
    info: str = ""  # Code block language tag
    level: int = 1  # Heading level (1-6)
    ordered: bool = False  # List type
    start: int = 1


class MarkdownParser:
    """Parses raw Markdown string into structured AST node hierarchy."""

    def __init__(self) -> None:
        """Initialize mistune AST parser instance with plugins."""
        self._md = mistune.create_markdown(renderer="ast", plugins=[table])

    def parse(self, markdown_text: str) -> List[ASTNode]:
        """Parse raw markdown text into list of top-level ASTNode objects.

        Args:
            markdown_text: Raw markdown content string.

        Returns:
            List[ASTNode]: Parsed abstract syntax tree nodes.
        """
        if not markdown_text or not markdown_text.strip():
            return []

        try:
            raw_ast = self._md(markdown_text)
            nodes: List[ASTNode] = []
            if isinstance(raw_ast, list):
                for item in raw_ast:
                    if isinstance(item, dict):
                        if item.get("type") == "blank_line":
                            continue
                        nodes.append(self._convert_node(item))
            return nodes
        except Exception:
            # Graceful degradation fallback: treat entire text as single paragraph
            return [ASTNode(type="paragraph", children=[ASTNode(type="text", raw=markdown_text)])]

    def extract_first_h1(self, nodes: List[ASTNode]) -> Optional[str]:
        """Extract plain text of the first H1 heading in the AST, if any."""
        for node in nodes:
            if node.type == "heading" and node.level == 1:
                return self.get_node_text(node)
        return None

    def get_node_text(self, node: ASTNode) -> str:
        """Recursively collect plain text content from an ASTNode and its children."""
        if node.raw:
            return node.raw
        text_parts = [self.get_node_text(child) for child in node.children]
        return "".join(text_parts)

    def _convert_node(self, item: Dict[str, Any]) -> ASTNode:
        """Convert a mistune dict AST item into a typed ASTNode recursively."""
        node_type = str(item.get("type", "paragraph"))
        children_raw = item.get("children", [])
        
        children: List[ASTNode] = []
        if isinstance(children_raw, list):
            for child in children_raw:
                if isinstance(child, dict):
                    if child.get("type") == "blank_line":
                        continue
                    children.append(self._convert_node(child))
                elif isinstance(child, str):
                    children.append(ASTNode(type="text", raw=child))

        raw_text = str(item.get("raw", ""))
        attrs_raw = item.get("attrs", {})
        attrs: Dict[str, Any] = attrs_raw if isinstance(attrs_raw, dict) else {}
        
        # Extract attributes from attrs dict or top-level item dict
        info = str(attrs.get("info", item.get("info", "")))
        level = int(attrs.get("level", item.get("level", 1)))
        ordered = bool(attrs.get("ordered", item.get("ordered", False)))
        start = int(attrs.get("start", item.get("start", 1)))

        return ASTNode(
            type=node_type,
            children=children,
            raw=raw_text,
            attrs=attrs,
            info=info,
            level=level,
            ordered=ordered,
            start=start,
        )
