"""CLI entry point (docforge-cli) for testing engine rendering without UI dependencies."""

import argparse
import sys
from pathlib import Path

from docforge.app.config import ConfigManager
from docforge.app.logging_config import setup_logging
from docforge.engine.docx_renderer import DocxRenderer
from docforge.engine.markdown_parser import MarkdownParser
from docforge.engine.pandoc_renderer import PandocRenderer
from docforge.engine.profile import FormatProfile
from docforge.engine.profile_manager import ProfileManager


def main() -> None:
    """Execute command-line markdown-to-docx conversion."""
    parser = argparse.ArgumentParser(description="DocForge CLI - Convert Markdown text to styled .docx documents.")
    parser.add_argument("input_md", type=str, help="Path to input Markdown file.")
    parser.add_argument("-o", "--output", type=str, default="", help="Path to output .docx file.")
    parser.add_argument("-p", "--profile", type=str, default="Anthony's Reference Format", help="Format profile name or JSON file path.")
    parser.add_argument("--reference-doc", type=Path, help="Use this DOCX as Pandoc's reference style document.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing output when using --reference-doc.")
    
    args = parser.parse_args()
    logger = setup_logging("cli.log")

    input_path = Path(args.input_md)
    if not input_path.exists():
        logger.error("Input Markdown file does not exist: %s", input_path)
        print(f"Error: Input Markdown file does not exist: {input_path}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".docx")

    # Load profile
    profile_manager = ProfileManager()
    profile: FormatProfile

    if Path(args.profile).exists() and Path(args.profile).suffix.lower() == ".json":
        profile = FormatProfile.load_from_file(Path(args.profile))
    else:
        found = profile_manager.get_profile_by_name(args.profile)
        if found:
            profile = found
        else:
            print(f"Warning: Profile '{args.profile}' not found. Using default profile.")
            profile = FormatProfile()

    # Load settings
    config_mgr = ConfigManager()
    settings = config_mgr.load_settings()

    # Read Markdown
    with open(input_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    if args.reference_doc:
        try:
            result_path = PandocRenderer().render(
                md_content, args.reference_doc, output_path,
                overwrite=args.overwrite, resource_paths=[input_path.parent],
            )
        except Exception as error:
            logger.error("Reference DOCX conversion failed: %s", error)
            print(f"Error: {error}")
            sys.exit(1)
        print(f"Successfully generated document: {result_path}")
        logger.info("Generated document at %s using reference '%s'", result_path, args.reference_doc)
        return

    # Parse AST and Render DOCX with a saved format profile
    md_parser = MarkdownParser()
    ast_nodes = md_parser.parse(md_content)

    renderer = DocxRenderer()
    result_path = renderer.render(ast_nodes, profile, settings, output_path)

    print(f"Successfully generated document: {result_path}")
    logger.info("Generated document at %s using profile '%s'", result_path, profile.name)


if __name__ == "__main__":
    main()
