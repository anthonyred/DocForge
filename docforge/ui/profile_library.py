"""Profile Library PySide6 GUI component for listing, creating, importing, exporting, and deleting format profiles."""

import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from docforge.app.strings import Strings
from docforge.engine.profile import FormatProfile
from docforge.engine.profile_manager import ProfileManager


class ProfileLibraryView(QWidget):
    """View for managing format profiles catalog (CRUD, import/export)."""

    library_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize ProfileLibraryView."""
        super().__init__(parent)
        self.profile_manager = ProfileManager()

        self._init_ui()
        self.refresh_library()

    def _init_ui(self) -> None:
        """Build UI elements."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Left list widget
        self.profile_list_widget = QListWidget()
        layout.addWidget(self.profile_list_widget, stretch=3)

        # Right action sidebar
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_new = QPushButton(Strings.NEW_PROFILE_BUTTON)
        self.btn_new.clicked.connect(self._create_new_profile)

        self.btn_import = QPushButton(Strings.IMPORT_PROFILE_BUTTON)
        self.btn_import.setObjectName("secondary_btn")
        self.btn_import.clicked.connect(self._import_profile)

        self.btn_export = QPushButton(Strings.EXPORT_PROFILE_BUTTON)
        self.btn_export.setObjectName("secondary_btn")
        self.btn_export.clicked.connect(self._export_profile)

        self.btn_duplicate = QPushButton(Strings.DUPLICATE_PROFILE_BUTTON)
        self.btn_duplicate.setObjectName("secondary_btn")
        self.btn_duplicate.clicked.connect(self._duplicate_profile)

        self.btn_delete = QPushButton(Strings.DELETE_PROFILE_BUTTON)
        self.btn_delete.setStyleSheet("background-color: #DC2626; color: white;")
        self.btn_delete.clicked.connect(self._delete_profile)

        btn_layout.addWidget(self.btn_new)
        btn_layout.addWidget(self.btn_import)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_duplicate)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()

        layout.addLayout(btn_layout, stretch=1)

    def refresh_library(self) -> None:
        """Reload profile items in list widget."""
        self.profile_list_widget.clear()
        profiles = self.profile_manager.list_profiles()
        for p in profiles:
            item_text = f"{p.name}\n  Layout: {p.cover.layout} | Font: {p.body.font_family} ({p.body.size_pt}pt)\n  {p.description}"
            item = QListWidgetItem(item_text)
            item.setData(100, p.name)
            self.profile_list_widget.addItem(item)

    def _get_selected_profile_name(self) -> Optional[str]:
        """Return name of currently selected profile in list widget."""
        curr = self.profile_list_widget.currentItem()
        if curr:
            return str(curr.data(100))
        return None

    def _create_new_profile(self) -> None:
        """Create a new default format profile."""
        new_profile = FormatProfile(name="New Format Profile", description="Custom user format profile.")
        self.profile_manager.save_profile(new_profile)
        self.refresh_library()
        self.library_changed.emit()

    def _import_profile(self) -> None:
        """Import profile JSON file into user profiles catalog."""
        file_path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Import Format Profile",
            "",
            "JSON Profile (*.json)",
        )
        if file_path_str:
            try:
                profile = FormatProfile.load_from_file(Path(file_path_str))
                self.profile_manager.save_profile(profile)
                self.refresh_library()
                self.library_changed.emit()
                QMessageBox.information(self, "Success", f"Successfully imported profile '{profile.name}'.")
            except Exception as err:
                QMessageBox.critical(self, Strings.ERROR_TITLE, Strings.ERROR_INVALID_PROFILE.format(error=err))

    def _export_profile(self) -> None:
        """Export selected format profile to JSON file."""
        name = self._get_selected_profile_name()
        if not name:
            QMessageBox.warning(self, Strings.ERROR_TITLE, "Please select a profile to export.")
            return

        profile = self.profile_manager.get_profile_by_name(name)
        if not profile:
            return

        default_filename = f"{name.lower().replace(' ', '_')}.json"
        save_path_str, _ = QFileDialog.getSaveFileName(
            self,
            "Export Format Profile",
            default_filename,
            "JSON Profile (*.json)",
        )
        if save_path_str:
            profile.save_to_file(Path(save_path_str))
            QMessageBox.information(self, "Success", f"Profile exported to: {save_path_str}")

    def _duplicate_profile(self) -> None:
        """Duplicate currently selected profile."""
        name = self._get_selected_profile_name()
        if not name:
            return

        profile = self.profile_manager.get_profile_by_name(name)
        if profile:
            profile.name = f"{profile.name} (Copy)"
            self.profile_manager.save_profile(profile)
            self.refresh_library()
            self.library_changed.emit()

    def _delete_profile(self) -> None:
        """Delete currently selected profile."""
        name = self._get_selected_profile_name()
        if not name:
            return

        reply = QMessageBox.question(
            self,
            Strings.CONFIRM_DELETE_TITLE,
            Strings.CONFIRM_DELETE_MSG.format(name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.profile_manager.delete_profile(name)
            self.refresh_library()
            self.library_changed.emit()
