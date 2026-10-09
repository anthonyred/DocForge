"""DocForge Main Application Window PySide6 implementation."""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from docforge.app.config import ConfigManager
from docforge.app.paths import get_bundled_assets_dir
from docforge.app.strings import Strings
from docforge.ui.paste_view import PasteView
from docforge.ui.profile_editor import ProfileEditorView
from docforge.ui.profile_library import ProfileLibraryView
from docforge.ui.settings_view import SettingsView


class MainWindow(QMainWindow):
    """DocForge PySide6 QMainWindow container."""

    def __init__(self) -> None:
        """Initialize main window, widgets, tabs, and theme stylesheet."""
        super().__init__()
        self.setWindowTitle(f"{Strings.APP_NAME} - {Strings.APP_TAGLINE}")
        self.resize(1020, 720)

        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()

        self._init_ui()
        self.apply_theme(self.settings.theme)

    def _init_ui(self) -> None:
        """Construct central tab widget and views."""
        self.tabs = QTabWidget()

        # Instantiate view components
        self.paste_view = PasteView()
        self.profile_editor = ProfileEditorView()
        self.profile_library = ProfileLibraryView()
        self.settings_view = SettingsView()

        # Add tabs
        self.tabs.addTab(self.paste_view, Strings.TAB_PASTE)
        self.tabs.addTab(self.profile_editor, Strings.TAB_EDITOR)
        self.tabs.addTab(self.profile_library, Strings.TAB_LIBRARY)
        self.tabs.addTab(self.settings_view, Strings.TAB_SETTINGS)

        self.setCentralWidget(self.tabs)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Connect inter-view signals
        self.paste_view.document_generated.connect(
            lambda path: self.status_bar.showMessage(f"Generated: {path}", 10000)
        )
        self.profile_library.library_changed.connect(self._on_library_changed)
        self.profile_editor.profile_saved.connect(self._on_profile_saved)
        self.settings_view.settings_saved.connect(self.apply_theme)

    def _on_library_changed(self) -> None:
        """Refresh profile options in paste view and profile editor."""
        self.paste_view.refresh_profiles()
        self.profile_editor.refresh_profile_list()

    def _on_profile_saved(self, profile_name: str) -> None:
        """Refresh profile options in library and paste view."""
        self.paste_view.refresh_profiles()
        self.profile_library.refresh_library()
        self.status_bar.showMessage(f"Profile saved: {profile_name}", 5000)

    def apply_theme(self, theme_name: str) -> None:
        """Apply QSS light or dark stylesheet to entire Qt Application."""
        theme_file = get_bundled_assets_dir() / "themes" / f"{theme_name.lower()}.qss"
        if not theme_file.exists():
            theme_file = get_bundled_assets_dir() / "themes" / "light.qss"

        if theme_file.exists():
            try:
                with open(theme_file, "r", encoding="utf-8") as f:
                    qss = f.read()
                qapp = QApplication.instance()
                if qapp:
                    qapp.setStyleSheet(qss)  # type: ignore[attr-defined]
            except Exception:
                pass


def main() -> None:
    """Main application GUI entry point."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
