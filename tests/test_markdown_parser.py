"""Unit tests for Markdown AST Parser."""

import pytest
from docforge.engine.markdown_parser import MarkdownParser, ASTNode


def test_markdown_parser_headings():
    """Verify markdown parser extracts headings correctly."""
    parser = MarkdownParser()
    md = "# Main Title\n\n## Sub Heading\n\nSome paragraph body text."
    nodes = parser.parse(md)
    
    assert len(nodes) == 3
    assert nodes[0].type == "heading"
    assert nodes[0].level == 1
    assert parser.get_node_text(nodes[0]) == "Main Title"
    assert parser.extract_first_h1(nodes) == "Main Title"

    assert nodes[1].type == "heading"
    assert nodes[1].level == 2
    assert parser.get_node_text(nodes[1]) == "Sub Heading"


def test_markdown_parser_code_block():
    """Verify code blocks with language tags parse correctly."""
    parser = MarkdownParser()
    md = "```python\ndef hello():\n    print('world')\n```"
    nodes = parser.parse(md)
    
    assert len(nodes) == 1
    assert nodes[0].type == "block_code"
    assert nodes[0].info == "python"
    assert "def hello():" in nodes[0].raw


def test_markdown_parser_table():
    """Verify markdown tables parse into AST structure."""
    parser = MarkdownParser()
    md = "| Header 1 | Header 2 |\n| --- | --- |\n| Cell 1 | Cell 2 |"
    nodes = parser.parse(md)
    
    assert len(nodes) == 1
    assert nodes[0].type == "table"


def test_markdown_parser_lists():
    """Verify ordered and unordered lists parse with nested items."""
    parser = MarkdownParser()
    md = "- Item 1\n- Item 2\n\n1. First\n2. Second"
    nodes = parser.parse(md)
    
    assert len(nodes) == 2
    assert nodes[0].type == "list"
    assert nodes[0].ordered is False
    assert nodes[1].type == "list"
    assert nodes[1].ordered is True
