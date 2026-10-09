"""Paste view component for Markdown input, profile selection, and rendering."""

import os
from pathlib import Path
from typing import Optional, Sequence

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QInputDialog,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from docforge.app.config import AppSettings, ConfigManager
from docforge.app.paths import get_app_data_dir
from docforge.app.strings import Strings
from docforge.engine.docx_renderer import DocxRenderer
from docforge.engine.markdown_parser import MarkdownParser
from docforge.engine.pandoc_renderer import PandocRenderer
from docforge.engine.profile import FormatProfile
from docforge.engine.profile_manager import ProfileManager
from docforge.engine.reference_analyzer import ReferenceDocxAnalyzer
from docforge.engine.reference_profile_store import ReferenceProfileStore
from docforge.ui.markdown_highlighter import MarkdownHighlighter


class _PandocWorker(QThread):
    """Run potentially slow Pandoc conversion away from the UI thread."""

    completed = Signal(str, str)
    failed = Signal(str)

    def __init__(
        self, markdown: str, reference: Path, output: Path, overwrite: bool, resource_paths: Sequence[Path]
    ) -> None:
        """Capture immutable conversion inputs for the worker."""
        super().__init__()
        self.markdown = markdown
        self.reference = reference
        self.output = output
        self.overwrite = overwrite
        self.resource_paths = resource_paths

    def run(self) -> None:
        """Convert Markdown and return result through Qt signals."""
        try:
            renderer = PandocRenderer()
            path = renderer.render(
                self.markdown, self.reference, self.output, overwrite=self.overwrite,
                resource_paths=self.resource_paths,
            )
            self.completed.emit(str(path), renderer.last_warnings)
        except Exception as error:
            self.failed.emit(str(error))


class PasteView(QWidget):
    """Main Markdown input and document generation view."""

    document_generated = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize PasteView components."""
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.profile_manager = ProfileManager()
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()
        self.reference_path: Optional[Path] = None
        self.markdown_base_dir: Optional[Path] = None
        self.analyzed_reference_path: Optional[Path] = None
        self._pandoc_worker: Optional[_PandocWorker] = None

        self._init_ui()
        self.refresh_profiles()

    def _init_ui(self) -> None:
        """Build UI layout and widget elements."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header controls
        ctrl_layout = QHBoxLayout()
        profile_label = QLabel(Strings.PROFILE_SELECT_LABEL)
        profile_label.setStyleSheet("font-weight: 600;")
        
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(260)
        self.profile_combo.currentTextChanged.connect(self._on_profile_changed)

        ctrl_layout.addWidget(profile_label)
        ctrl_layout.addWidget(self.profile_combo)
        self.btn_open_markdown = QPushButton(Strings.OPEN_MARKDOWN_BUTTON)
        self.btn_open_markdown.clicked.connect(self._open_markdown)
        ctrl_layout.addWidget(self.btn_open_markdown)
        ctrl_layout.addStretch()

        layout.addLayout(ctrl_layout)

        # Markdown Input Text Box
        input_label = QLabel(Strings.MARKDOWN_INPUT_LABEL)
        input_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(input_label)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(Strings.MARKDOWN_PLACEHOLDER)
        self._markdown_highlighter = MarkdownHighlighter(self.editor)
        self.editor.textChanged.connect(self._update_stats)
        layout.addWidget(self.editor)
        self._init_reference_ui(layout)

        # Footer stats & buttons
        bottom_layout = QHBoxLayout()
        self.stats_label = QLabel("0 characters | 0 words")
        self.stats_label.setStyleSheet("color: #64748B;")
        self.btn_generate = QPushButton(Strings.GENERATE_BUTTON)
        self.btn_generate.clicked.connect(lambda: self.generate_document(open_word=False))
        self.btn_generate_open = QPushButton(Strings.GENERATE_AND_OPEN_BUTTON)
        self.btn_generate_open.setObjectName("secondary_btn")
        self.btn_generate_open.clicked.connect(lambda: self.generate_document(open_word=True))
        bottom_layout.addWidget(self.stats_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_generate_open)
        bottom_layout.addWidget(self.btn_generate)
        layout.addLayout(bottom_layout)

    def _init_reference_ui(self, layout: QVBoxLayout) -> None:
        """Create reference selection, saved-profile, and analysis controls."""
        reference_layout = QHBoxLayout()
        self.btn_select_reference = QPushButton(Strings.SELECT_REFERENCE_BUTTON)
        self.btn_select_reference.clicked.connect(self._select_reference)
        self.btn_clear_reference = QPushButton(Strings.CLEAR_REFERENCE_BUTTON)
        self.btn_clear_reference.clicked.connect(self._clear_reference)
        self.btn_analyze_reference = QPushButton(Strings.ANALYZE_REFERENCE_BUTTON)
        self.btn_analyze_reference.clicked.connect(self._analyze_reference)
        self.btn_save_reference_profile = QPushButton(Strings.SAVE_REFERENCE_PROFILE_BUTTON)
        self.btn_save_reference_profile.clicked.connect(self._save_reference_profile)
        self.saved_reference_combo = QComboBox()
        self.saved_reference_combo.setMinimumWidth(160)
        self.saved_reference_combo.setPlaceholderText(Strings.SAVED_REFERENCE_PLACEHOLDER)
        self.btn_use_saved_reference = QPushButton(Strings.USE_SAVED_REFERENCE_BUTTON)
        self.btn_use_saved_reference.clicked.connect(self._use_saved_reference)
        self.reference_label = QLabel(Strings.REFERENCE_NOT_SELECTED)
        self.reference_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        reference_layout.addWidget(self.btn_select_reference)
        reference_layout.addWidget(self.btn_clear_reference)
        reference_layout.addWidget(self.btn_analyze_reference)
        reference_layout.addWidget(self.btn_save_reference_profile)
        reference_layout.addWidget(self.saved_reference_combo)
        reference_layout.addWidget(self.btn_use_saved_reference)
        reference_layout.addWidget(self.reference_label, 1)
        layout.addLayout(reference_layout)

        self.analysis_label = QLabel(Strings.REFERENCE_ANALYSIS_LABEL)
        self.analysis_report = QPlainTextEdit()
        self.analysis_report.setReadOnly(True)
        self.analysis_report.setMaximumHeight(150)
        layout.addWidget(self.analysis_label)
        layout.addWidget(self.analysis_report)
        self._refresh_saved_reference_profiles()

    def refresh_profiles(self) -> None:
        """Reload profiles into combo box."""
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        profiles = self.profile_manager.list_profiles()
        
        selected_idx = 0
        for idx, p in enumerate(profiles):
            self.profile_combo.addItem(p.name)
            if p.name == self.settings.last_profile_used:
                selected_idx = idx

        if self.profile_combo.count() > 0:
            self.profile_combo.setCurrentIndex(selected_idx)
        self.profile_combo.blockSignals(False)

    def _on_profile_changed(self, profile_name: str) -> None:
        """Handle user changing format profile."""
        if profile_name:
            self.settings.last_profile_used = profile_name
            self.config_manager.save_settings(self.settings)

    def _update_stats(self) -> None:
        """Update live character and word count in footer."""
        text = self.editor.toPlainText()
        char_count = len(text)
        word_count = len(text.split()) if text.strip() else 0
        self.stats_label.setText(f"{char_count:,} characters | {word_count:,} words")

    def _open_markdown(self) -> None:
        """Load Markdown content from a file selected by the user."""
        path, _ = QFileDialog.getOpenFileName(self, Strings.OPEN_MARKDOWN_BUTTON, "", Strings.MARKDOWN_FILE_FILTER)
        if path:
            self._load_markdown_file(Path(path))

    def _load_markdown_file(self, path: Path) -> None:
        """Read a Markdown file into the editor with actionable errors."""
        try:
            self.editor.setPlainText(path.read_text(encoding="utf-8"))
            self.markdown_base_dir = path.parent
        except (OSError, UnicodeError) as error:
            QMessageBox.warning(self, Strings.ERROR_TITLE, f"Failed to read Markdown file: {error}")

    def _select_reference(self) -> None:
        """Let the user choose the reference DOCX for this workflow."""
        path, _ = QFileDialog.getOpenFileName(self, Strings.SELECT_REFERENCE_BUTTON, "", Strings.REFERENCE_FILE_FILTER)
        if path:
            self.reference_path = Path(path)
            self.analyzed_reference_path = None
            self.profile_combo.setEnabled(False)
            self.reference_label.setText(str(self.reference_path))
            self.analysis_report.clear()

    def _clear_reference(self) -> None:
        """Return the view to its existing saved-profile conversion mode."""
        self.reference_path = None
        self.analyzed_reference_path = None
        self.profile_combo.setEnabled(True)
        self.reference_label.setText(Strings.REFERENCE_NOT_SELECTED)
        self.analysis_report.clear()

    def _analyze_reference(self) -> bool:
        """Analyze the selected reference and show a compact report."""
        if not self.reference_path:
            QMessageBox.information(self, Strings.APP_NAME, Strings.REFERENCE_NOT_SELECTED)
            return False
        try:
            report = ReferenceDocxAnalyzer().analyze(self.reference_path)
            self.analysis_report.setPlainText(report.summary())
            self.analyzed_reference_path = self.reference_path.resolve()
            return True
        except Exception as error:
            QMessageBox.warning(self, Strings.ERROR_TITLE, Strings.REFERENCE_ANALYSIS_FAILED.format(error=error))
            return False

    def _save_reference_profile(self) -> None:
        """Save the analyzed reference as a reusable, self-contained package."""
        if not self.reference_path or self.analyzed_reference_path != self.reference_path.resolve():
            QMessageBox.information(self, Strings.APP_NAME, Strings.REFERENCE_REVIEW_REQUIRED)
            return
        name, accepted = QInputDialog.getText(self, Strings.SAVE_REFERENCE_PROFILE_BUTTON, Strings.REFERENCE_PROFILE_NAME_PROMPT)
        if not accepted or not name.strip():
            return
        try:
            analysis = ReferenceDocxAnalyzer().analyze(self.reference_path)
            target = get_app_data_dir() / "reference_profiles"
            profile_path = ReferenceProfileStore(target).save(name, analysis)
            self._refresh_saved_reference_profiles()
            saved_index = self.saved_reference_combo.findText(name.strip())
            if saved_index >= 0:
                self.saved_reference_combo.setCurrentIndex(saved_index)
            QMessageBox.information(self, Strings.APP_NAME, Strings.REFERENCE_PROFILE_SAVED.format(path=profile_path))
        except Exception as error:
            QMessageBox.warning(self, Strings.ERROR_TITLE, Strings.REFERENCE_PROFILE_SAVE_FAILED.format(error=error))

    def _refresh_saved_reference_profiles(self) -> None:
        """Reload saved reference names and embedded DOCX paths."""
        root = get_app_data_dir() / "reference_profiles"
        profiles = ReferenceProfileStore(root).list_profiles()
        self.saved_reference_combo.clear()
        for name, path in profiles:
            self.saved_reference_combo.addItem(name, str(path))

    def _use_saved_reference(self) -> None:
        """Select a saved reference package for the current conversion."""
        path = self.saved_reference_combo.currentData()
        if not path:
            QMessageBox.information(self, Strings.APP_NAME, Strings.SAVED_REFERENCE_PLACEHOLDER)
            return
        self.reference_path = Path(str(path))
        self.analyzed_reference_path = None
        self.profile_combo.setEnabled(False)
        self.reference_label.setText(str(self.reference_path))
        self.analysis_report.clear()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event for .md files."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith((".md", ".txt", ".markdown")) for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle file drop event to load markdown file content."""
        urls = event.mimeData().urls()
        for url in urls:
            file_path = Path(url.toLocalFile())
            if file_path.exists() and file_path.suffix.lower() in (".md", ".txt", ".markdown"):
                self._load_markdown_file(file_path)
                break

    def generate_document(self, open_word: bool = False) -> Optional[Path]:
        """Start reference-based conversion or the existing profile renderer."""
        text = self.editor.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, Strings.ERROR_TITLE, "Please paste or type Markdown content before generating.")
            return None
        if not self._reference_is_reviewed():
            return None
        output_path = self._select_output_path()
        if output_path is None:
            return None
        if self.reference_path is not None:
            overwrite = self._confirm_output_overwrite(output_path)
            if overwrite is not None:
                self._start_pandoc_generation(text, self.reference_path, output_path, open_word, overwrite)
            return None
        return self._generate_profile_document(text, output_path, open_word)

    def _reference_is_reviewed(self) -> bool:
        """Require inspection of the currently selected reference before export."""
        if not self.reference_path or self.analyzed_reference_path == self.reference_path.resolve():
            return True
        if self._analyze_reference():
            QMessageBox.information(self, Strings.APP_NAME, Strings.REFERENCE_REVIEW_REQUIRED)
        return False

    def _select_output_path(self) -> Optional[Path]:
        """Show the output picker and return a DOCX path when selected."""
        value, _ = QFileDialog.getSaveFileName(
            self, "Save Generated Document", "Generated_Document.docx", Strings.REFERENCE_FILE_FILTER
        )
        return Path(value) if value else None

    def _generate_profile_document(self, text: str, output_path: Path, open_word: bool) -> Optional[Path]:
        """Render using the existing JSON profile path and report errors."""
        profile = self.profile_manager.get_profile_by_name(self.profile_combo.currentText()) or FormatProfile()
        try:
            ast_nodes = MarkdownParser().parse(text)
            result = DocxRenderer().render(ast_nodes, profile, self.settings, output_path)
            QMessageBox.information(self, Strings.CONVERSION_SUCCESS_TITLE, Strings.CONVERSION_SUCCESS_MSG.format(path=result))
            self.document_generated.emit(str(result))
            if open_word:
                self._open_generated_document(result)
            return result
        except Exception as error:
            QMessageBox.critical(self, Strings.ERROR_TITLE, Strings.ERROR_RENDER_FAILED.format(error=error))
            return None

    def _open_generated_document(self, path: Path) -> None:
        """Open a generated DOCX in the system's associated Word application."""
        try:
            os.startfile(str(path))
        except OSError as error:
            QMessageBox.warning(self, Strings.ERROR_TITLE, f"Could not launch file in Word: {error}")

    def _start_pandoc_generation(
        self, markdown: str, reference: Path, output: Path, open_word: bool, overwrite: bool
    ) -> None:
        """Start reference-based conversion without blocking the Qt event loop."""
        markdown_base_dir = self.markdown_base_dir
        resource_paths = [markdown_base_dir] if markdown_base_dir else []
        worker = _PandocWorker(markdown, reference, output, overwrite, resource_paths)
        self._pandoc_worker = worker
        worker.completed.connect(lambda path, warnings: self._pandoc_completed(path, warnings, open_word))
        worker.failed.connect(self._pandoc_failed)
        worker.finished.connect(lambda: self._pandoc_worker_finished(worker))
        worker.finished.connect(worker.deleteLater)
        self.btn_generate.setEnabled(False)
        self.btn_generate_open.setEnabled(False)
        worker.start()

    def _confirm_output_overwrite(self, output: Path) -> Optional[bool]:
        """Ask before replacing an existing output; return None on cancellation."""
        if self.reference_path and output.resolve() == self.reference_path.resolve():
            QMessageBox.warning(self, Strings.ERROR_TITLE, Strings.ERROR_RENDER_FAILED.format(error="Output must not overwrite the reference DOCX."))
            return None
        if not output.exists():
            return False
        result = QMessageBox.question(
            self, Strings.APP_NAME, Strings.OVERWRITE_OUTPUT_CONFIRM.format(path=output),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return True if result == QMessageBox.StandardButton.Yes else None

    def _pandoc_completed(self, path: str, warnings: str, open_word: bool) -> None:
        """Report successful conversion and optionally open the generated file."""
        self.btn_generate.setEnabled(True)
        self.btn_generate_open.setEnabled(True)
        self.document_generated.emit(path)
        QMessageBox.information(self, Strings.CONVERSION_SUCCESS_TITLE, Strings.CONVERSION_SUCCESS_MSG.format(path=path))
        if warnings:
            QMessageBox.warning(self, Strings.APP_NAME, Strings.CONVERSION_WARNINGS.format(warnings=warnings))
        if open_word:
            try:
                os.startfile(path)
            except OSError as error:
                QMessageBox.warning(self, Strings.ERROR_TITLE, f"Could not launch file in Word: {error}")

    def _pandoc_failed(self, error: str) -> None:
        """Restore controls and display a failed conversion message."""
        self.btn_generate.setEnabled(True)
        self.btn_generate_open.setEnabled(True)
        QMessageBox.critical(self, Strings.ERROR_TITLE, Strings.ERROR_RENDER_FAILED.format(error=error))

    def _pandoc_worker_finished(self, worker: _PandocWorker) -> None:
        """Release the thread reference only after the worker has stopped."""
        if self._pandoc_worker is worker:
            self._pandoc_worker = None
