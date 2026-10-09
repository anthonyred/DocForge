# Reference workflow acceptance fixture

## Purpose

This representative document checks Unicode, emphasis, and paragraph styling. It contains **bold emphasis**, *italic emphasis*, an identifier `DOCFORGE-482`, and Unicode text: café, naïve, 日本語, and —.

### Nested list content

1. First-level ordered item.
   - Nested bullet item.
     1. Nested ordered detail.
2. Second first-level item.

## Table content

| Component | Status | Notes |
|:--|:--:|--:|
| Markdown parser | Ready | Handles Unicode |
| DOCX renderer | Under review | Uses selected reference |

## Hyperlinks and citations

See the [Pandoc User's Guide](https://pandoc.org/MANUAL.html) for conversion details. Citation marker: [@doe2020].

## Fenced code block

```python
def render_reference(markdown: str) -> str:
    """Keep the source readable in Word."""
    return f"DocForge: {markdown}"
```
