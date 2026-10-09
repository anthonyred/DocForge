"""Pandoc-backed Markdown to DOCX conversion using a reference document."""

import shutil
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional, Sequence

from docforge.engine.reference_analyzer import ReferenceDocxAnalyzer
from docforge.engine.reference_mapper import prepare_reference_docx


class PandocRenderer:
    """Convert Markdown with Pandoc while retaining the user's reference DOCX."""

    def __init__(self, executable: Optional[str] = None, timeout_seconds: int = 120) -> None:
        """Set an optional Pandoc executable and conversion timeout."""
        self.executable = executable
        self.timeout_seconds = timeout_seconds
        self.last_warnings = ""

    def render(
        self, markdown: str, reference_path: Path, output_path: Path, overwrite: bool = False,
        resource_paths: Optional[Sequence[Path]] = None,
    ) -> Path:
        """Run Pandoc safely, validating both source inputs and produced output."""
        ReferenceDocxAnalyzer._validate_docx(reference_path)
        executable = self.executable or shutil.which("pandoc")
        if not executable:
            raise FileNotFoundError("Pandoc was not found. Install Pandoc or add it to PATH.")
        if not markdown.strip():
            raise ValueError("Markdown content is empty.")
        output_path = output_path.resolve()
        if output_path == reference_path.resolve():
            raise ValueError("Output path must not overwrite the reference DOCX.")
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"Output file already exists: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return self._convert(executable, markdown, reference_path, output_path, resource_paths or ())

    def _convert(
        self, executable: str, markdown: str, reference_path: Path, output_path: Path,
        resource_paths: Sequence[Path],
    ) -> Path:
        """Use temporary Markdown input and preserve useful Pandoc diagnostics."""
        with tempfile.TemporaryDirectory(prefix="docforge-pandoc-", dir=output_path.parent) as temp_dir:
            input_path = Path(temp_dir) / "input.md"
            pandoc_reference = Path(temp_dir) / "reference.docx"
            staged_output = Path(temp_dir) / "generated.docx"
            input_path.write_text(markdown, encoding="utf-8")
            prepare_reference_docx(reference_path, pandoc_reference)
            command: Sequence[str] = [
                executable, "--from=markdown", "--to=docx",
                f"--reference-doc={pandoc_reference}",
                *([f"--resource-path={os.pathsep.join(str(path.resolve()) for path in resource_paths)}"] if resource_paths else []),
                str(input_path), "--output", str(staged_output),
            ]
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=self.timeout_seconds, check=False)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(f"Pandoc did not finish within {self.timeout_seconds} seconds.") from exc
            if result.returncode != 0:
                message = result.stderr.strip() or result.stdout.strip() or "Unknown Pandoc error."
                raise RuntimeError(f"Pandoc conversion failed: {message}")
            self.last_warnings = result.stderr.strip()
            if not staged_output.is_file() or staged_output.stat().st_size == 0:
                raise RuntimeError("Pandoc reported success but did not create a DOCX output.")
            ReferenceDocxAnalyzer._validate_docx(staged_output)
            staged_output.replace(output_path)
        if not output_path.is_file() or output_path.stat().st_size == 0:
            raise RuntimeError("Pandoc reported success but did not create a DOCX output.")
        return output_path
