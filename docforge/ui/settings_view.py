"""Settings View PySide6 GUI component for author name, date format, and theme preferences."""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from docforge.app.config import AppSettings, ConfigManager
from docforge.app.strings import Strings
from docforge.engine.profile_manager import ProfileManager


class SettingsView(QWidget):
    """View for configuring user application preferences."""

    settings_saved = Signal(str)  # Emits theme name when saved

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize SettingsView."""
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.profile_manager = ProfileManager()
        self.settings = self.config_manager.load_settings()

        self._init_ui()
        self.load_settings()

    def _init_ui(self) -> None:
        """Build UI elements."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        group = QGroupBox("Application Preferences")
        form = QFormLayout(group)

        self.author_edit = QLineEdit()
        
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems([
            "%B %d, %Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d %B %Y",
        ])

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Dark", "dark")

        self.default_profile_combo = QComboBox()

        form.addRow(Strings.AUTHOR_LABEL, self.author_edit)
        form.addRow(Strings.DATE_FORMAT_LABEL, self.date_format_combo)
        form.addRow(Strings.THEME_LABEL, self.theme_combo)
        form.addRow("Default Profile:", self.default_profile_combo)

        layout.addWidget(group)

        # Save button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton(Strings.SAVE_SETTINGS_BUTTON)
        self.btn_save.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)
        layout.addStretch()

        self.refresh_profiles()

    def refresh_profiles(self) -> None:
        """Reload profile names into default profile combo box."""
        self.default_profile_combo.clear()
        profiles = self.profile_manager.list_profiles()
        for p in profiles:
            self.default_profile_combo.addItem(p.name)

    def load_settings(self) -> None:
        """Populate settings widgets from AppSettings instance."""
        self.settings = self.config_manager.load_settings()
        self.author_edit.setText(self.settings.author_name)

        idx_date = self.date_format_combo.findText(self.settings.date_format)
        if idx_date >= 0:
            self.date_format_combo.setCurrentIndex(idx_date)

        idx_theme = self.theme_combo.findData(self.settings.theme)
        if idx_theme >= 0:
            self.theme_combo.setCurrentIndex(idx_theme)

        idx_prof = self.default_profile_combo.findText(self.settings.default_profile_name)
        if idx_prof >= 0:
            self.default_profile_combo.setCurrentIndex(idx_prof)

    def save_settings(self) -> None:
        """Save user preferences to disk."""
        self.settings.author_name = self.author_edit.text().strip() or Strings.AUTHOR_DEFAULT
        self.settings.date_format = self.date_format_combo.currentText()
        self.settings.theme = str(self.theme_combo.currentData())
        self.settings.default_profile_name = self.default_profile_combo.currentText()

        self.config_manager.save_settings(self.settings)
        QMessageBox.information(self, "Success", Strings.SETTINGS_SAVED_MSG)
        self.settings_saved.emit(self.settings.theme)
