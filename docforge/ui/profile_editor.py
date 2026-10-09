"""Profile Editor PySide6 GUI component for customizing Format Profiles."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from docforge.app.strings import Strings
from docforge.engine.profile import FormatProfile
from docforge.engine.profile_manager import ProfileManager


class ProfileEditorView(QWidget):
    """View for editing, customizing, and saving format profiles."""

    profile_saved = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize ProfileEditorView."""
        super().__init__(parent)
        self.profile_manager = ProfileManager()
        self.current_profile = FormatProfile()

        self._init_ui()
        self.load_profile("Anthony's Reference Format")

    def _init_ui(self) -> None:
        """Build editor UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Top selector
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Select Profile to Edit:"))
        
        self.profile_select_combo = QComboBox()
        self.profile_select_combo.currentTextChanged.connect(self._on_profile_selected)
        top_layout.addWidget(self.profile_select_combo)
        top_layout.addStretch()

        self.btn_save = QPushButton(Strings.SAVE_PROFILE_BUTTON)
        self.btn_save.clicked.connect(self.save_current_profile)
        top_layout.addWidget(self.btn_save)

        main_layout.addLayout(top_layout)

        # Scrollable form container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Metadata Group
        meta_group = QGroupBox("Profile Metadata")
        meta_form = QFormLayout(meta_group)
        self.name_edit = QLineEdit()
        self.desc_edit = QLineEdit()
        meta_form.addRow("Profile Name:", self.name_edit)
        meta_form.addRow("Description:", self.desc_edit)
        scroll_layout.addWidget(meta_group)

        # Cover Page Group
        cover_group = QGroupBox("Cover Page Settings")
        cover_form = QFormLayout(cover_group)
        self.cover_enabled = QCheckBox("Enable Cover Page")
        self.cover_layout_combo = QComboBox()
        self.cover_layout_combo.addItems(["executive_modern", "classic_centered", "accent_banner", "minimal_left"])
        self.cover_subtitle_edit = QLineEdit()
        self.cover_doctype_edit = QLineEdit()
        self.cover_company_edit = QLineEdit()

        cover_form.addRow(self.cover_enabled)
        cover_form.addRow("Cover Layout:", self.cover_layout_combo)
        cover_form.addRow("Subtitle:", self.cover_subtitle_edit)
        cover_form.addRow("Doc Type:", self.cover_doctype_edit)
        cover_form.addRow("Company:", self.cover_company_edit)
        scroll_layout.addWidget(cover_group)

        # Body Text Group
        body_group = QGroupBox("Body Text Typography")
        body_form = QFormLayout(body_group)
        self.body_font_edit = QLineEdit("Segoe UI")
        self.body_size_spin = QDoubleSpinBox()
        self.body_size_spin.setRange(8.0, 36.0)
        self.body_size_spin.setValue(11.0)
        self.body_spacing_spin = QDoubleSpinBox()
        self.body_spacing_spin.setRange(1.0, 3.0)
        self.body_spacing_spin.setSingleStep(0.05)
        self.body_spacing_spin.setValue(1.15)

        body_form.addRow("Font Family:", self.body_font_edit)
        body_form.addRow("Font Size (pt):", self.body_size_spin)
        body_form.addRow("Line Spacing:", self.body_spacing_spin)
        scroll_layout.addWidget(body_group)

        # Page Setup Group
        page_group = QGroupBox("Page Setup & Margins")
        page_form = QFormLayout(page_group)
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["A4", "Letter"])
        self.margin_top_spin = QDoubleSpinBox()
        self.margin_top_spin.setRange(0.5, 10.0)
        self.margin_top_spin.setValue(2.5)
        self.margin_bottom_spin = QDoubleSpinBox()
        self.margin_bottom_spin.setRange(0.5, 10.0)
        self.margin_bottom_spin.setValue(2.5)
        self.header_text_edit = QLineEdit()

        page_form.addRow("Paper Size:", self.page_size_combo)
        page_form.addRow("Top Margin (cm):", self.margin_top_spin)
        page_form.addRow("Bottom Margin (cm):", self.margin_bottom_spin)
        page_form.addRow("Header Text:", self.header_text_edit)
        scroll_layout.addWidget(page_group)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.refresh_profile_list()

    def refresh_profile_list( me ) -> None:
        """Reload profile dropdown items."""
        me.profile_select_combo.blockSignals(True)
        me.profile_select_combo.clear()
        profiles = me.profile_manager.list_profiles()
        for p in profiles:
            me.profile_select_combo.addItem(p.name)
        me.profile_select_combo.blockSignals(False)

    def _on_profile_selected(self, name: str) -> None:
        """Load selected profile into form."""
        if name:
            self.load_profile(name)

    def load_profile(self, name: str) -> None:
        """Populate editor fields from profile object."""
        p = self.profile_manager.get_profile_by_name(name)
        if not p:
            p = FormatProfile()
        self.current_profile = p

        self.name_edit.setText(p.name)
        self.desc_edit.setText(p.description)

        # Cover
        self.cover_enabled.setChecked(p.cover.enabled)
        idx = self.cover_layout_combo.findText(p.cover.layout)
        if idx >= 0:
            self.cover_layout_combo.setCurrentIndex(idx)
        self.cover_subtitle_edit.setText(p.cover.subtitle)
        self.cover_doctype_edit.setText(p.cover.doc_type)
        self.cover_company_edit.setText(p.cover.company)

        # Body
        self.body_font_edit.setText(p.body.font_family)
        self.body_size_spin.setValue(p.body.size_pt)
        self.body_spacing_spin.setValue(p.body.line_spacing)

        # Page
        idx_pg = self.page_size_combo.findText(p.page.size)
        if idx_pg >= 0:
            self.page_size_combo.setCurrentIndex(idx_pg)
        self.margin_top_spin.setValue(p.page.margin_top_cm)
        self.margin_bottom_spin.setValue(p.page.margin_bottom_cm)
        self.header_text_edit.setText(p.page.header_text)

    def save_current_profile(self) -> None:
        """Extract field values and save profile to disk."""
        p = self.current_profile
        p.name = self.name_edit.text().strip() or "Custom Profile"
        p.description = self.desc_edit.text().strip()

        # Cover
        p.cover.enabled = self.cover_enabled.isChecked()
        p.cover.layout = self.cover_layout_combo.currentText()
        p.cover.subtitle = self.cover_subtitle_edit.text().strip()
        p.cover.doc_type = self.cover_doctype_edit.text().strip()
        p.cover.company = self.cover_company_edit.text().strip()

        # Body
        p.body.font_family = self.body_font_edit.text().strip() or "Segoe UI"
        p.body.size_pt = float(self.body_size_spin.value())
        p.body.line_spacing = float(self.body_spacing_spin.value())

        # Page
        p.page.size = self.page_size_combo.currentText()
        p.page.margin_top_cm = float(self.margin_top_spin.value())
        p.page.margin_bottom_cm = float(self.margin_bottom_spin.value())
        p.page.header_text = self.header_text_edit.text().strip()

        self.profile_manager.save_profile(p)
        QMessageBox.information(self, "Success", f"Profile '{p.name}' saved successfully.")
        self.refresh_profile_list()
        self.profile_saved.emit(p.name)
