"""Small Markdown syntax highlighter for the paste editor."""

import re
from typing import List, Pattern, Tuple

from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import QPlainTextEdit


class MarkdownHighlighter(QSyntaxHighlighter):
    """Highlight common Markdown structures without changing source text."""

    def __init__(self, editor: QPlainTextEdit) -> None:
        """Attach highlighting rules to an existing plain-text editor."""
        super().__init__(editor.document())
        self._code_format = _format("#64748B", italic=True)
        self._fence_pattern = re.compile(r"^\s*```")
        self._rules: List[Tuple[Pattern[str], QTextCharFormat]] = [
            (re.compile(r"^\s{0,3}#{1,6}\s+.+$"), _format("#1B365D", bold=True)),
            (re.compile(r"^\s{0,3}>.*$"), _format("#3182CE", italic=True)),
            (re.compile(r"^\s{0,3}(?:[-+*]|\d+[.)])\s+.*$"), _format("#2D3748")),
            (re.compile(r"\*\*[^*]+\*\*|__[^_]+__"), _format("#111827", bold=True)),
            (re.compile(r"(?<!\*)\*[^*]+\*(?!\*)|(?<!_)_[^_]+_(?!_)"), _format("#4A5568", italic=True)),
            (re.compile(r"`[^`]+`"), _format("#B42318", family="Consolas")),
            (re.compile(r"\[[^\]]+\]\([^)]+\)"), _format("#2B6CB0", underline=True)),
        ]

    def highlightBlock(self, text: str) -> None:
        """Apply line-level and inline Markdown formats."""
        if self.previousBlockState() == 1:
            self.setFormat(0, len(text), self._code_format)
            if self._fence_pattern.match(text):
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(1)
            return
        if self._fence_pattern.match(text):
            self.setFormat(0, len(text), self._code_format)
            self.setCurrentBlockState(1)
            return
        self.setCurrentBlockState(0)
        for pattern, text_format in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), text_format)


def _format(color: str, bold: bool = False, italic: bool = False, underline: bool = False, family: str = "") -> QTextCharFormat:
    """Build a reusable Qt text format for one syntax category."""
    result = QTextCharFormat()
    result.setForeground(QColor(color))
    result.setFontWeight(700 if bold else 400)
    result.setFontItalic(italic)
    result.setFontUnderline(underline)
    if family:
        result.setFontFamilies([family])
    return result
