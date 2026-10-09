"""Composition root launcher for DocForge desktop application."""

import sys
from docforge.app.logging_config import setup_logging
from docforge.ui.main_window import main as run_gui


def main() -> None:
    """Initialize logging and run main PySide6 GUI loop."""
    logger = setup_logging()
    logger.info("Starting DocForge application...")
    run_gui()


if __name__ == "__main__":
    main()
