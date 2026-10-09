"""Code block syntax highlighting extension hook."""

from typing import List, Tuple


def highlight_code_tokens(code_text: str, language: str = "") -> List[Tuple[str, str]]:
    """Tokenize code text into (token_type, substring) pairs.

    Extension stub for Pygments syntax highlighting in docx code blocks.

    Args:
        code_text: Raw code string.
        language: Preserved language tag (e.g., 'python', 'json', 'sql').

    Returns:
        List[Tuple[str, str]]: List of (token_type, code_text) tuples.
    """
    # Default fallback: return full string as plain token
    return [("plain", code_text)]
