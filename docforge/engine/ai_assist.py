"""AI-assist post-processing hook for Markdown text enhancement."""

from typing import Callable, Optional


def default_ai_post_processor(markdown_text: str) -> str:
    """Default pass-through AI post-processor function."""
    return markdown_text


class AIAssistService:
    """Pluggable AI-assist post-processing transformer."""

    def __init__(self, processor_func: Optional[Callable[[str], str]] = None) -> None:
        """Initialize AI assist service with pluggable function."""
        self._processor = processor_func or default_ai_post_processor

    def process(self, markdown_text: str) -> str:
        """Execute post-processing transformation on raw markdown text."""
        try:
            return self._processor(markdown_text)
        except Exception:
            return markdown_text
