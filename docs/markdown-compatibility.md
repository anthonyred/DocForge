# Markdown compatibility

DocForge uses Pandoc's `markdown` reader as the content contract when a reference DOCX is selected. The installed Pandoc release controls the enabled extensions; query the runtime with:

```powershell
pandoc --version
pandoc --list-extensions=markdown
```

The current development environment uses Pandoc 3.10. Its Markdown reader enables headings, emphasis, lists, pipe/grid/simple/multiline tables, block quotes, links, images, fenced code, citations, footnotes, definition lists, raw HTML, and several Pandoc-specific extensions by default. Syntax and extension defaults can vary between Pandoc releases. DocForge passes Markdown through as UTF-8 and relies on Pandoc to parse and convert it; it does not promise identical rendering for every extension.

Microsoft Learn documents its publishing dialect as CommonMark parsed by Markdig. That is a platform-specific contract and does not define Microsoft Word's Markdown import behavior. DocForge therefore does not claim Pandoc and Microsoft products implement the same dialect. Use Pandoc's extension list for the conversion behavior available on the installed machine. See [Microsoft Learn's Markdown reference](https://learn.microsoft.com/en-us/contribute/content/markdown-reference) and [Pandoc's User's Guide](https://pandoc.org/MANUAL.html).

`--reference-doc` supplies Word styles and document properties such as margins, page size, headers, and footers. It is not a full visual clone of a source document. DocForge reports observed properties and uncertain mappings before export. Floating objects and exact page layout can differ in Word and are not treated as verified matches.
