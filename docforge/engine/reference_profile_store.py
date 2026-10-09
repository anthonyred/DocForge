"""Persist reusable reference DOCX analysis packages outside format profiles."""

import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Tuple

from docforge.engine.reference_analyzer import ReferenceAnalysis


class ReferenceProfileStore:
    """Save versioned reference metadata and a private DOCX copy."""

    def __init__(self, root: Path) -> None:
        """Set the dedicated reference-profile storage directory."""
        self.root = root

    def save(self, name: str, analysis: ReferenceAnalysis) -> Path:
        """Store the analyzed reference and report without changing its source."""
        slug = re.sub(r"[^a-z0-9_-]+", "-", name.strip().lower()).strip("-_")
        if not slug:
            raise ValueError("Profile name must contain a letter or number.")
        target = self.root / slug
        target.mkdir(parents=True, exist_ok=False)
        reference_copy = target / "reference.docx"
        shutil.copy2(analysis.path, reference_copy)
        metadata: Dict[str, Any] = {
            "profile_version": 1,
            "name": name.strip(),
            "source_filename": analysis.path.name,
            "reference_file": reference_copy.name,
            "detected_properties": analysis.properties,
            "mapped_styles": analysis.mapped_styles,
            "uncertain_properties": analysis.uncertain,
            "unsupported_properties": analysis.unsupported,
            "strategy": analysis.strategy,
        }
        (target / "profile.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return target

    def list_profiles(self) -> List[Tuple[str, Path]]:
        """List valid saved reference profiles and their bundled DOCX paths."""
        profiles: List[Tuple[str, Path]] = []
        for metadata_path in self.root.glob("*/profile.json"):
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                reference = metadata_path.parent / metadata["reference_file"]
                if (
                    metadata.get("profile_version") == 1
                    and reference.resolve().parent == metadata_path.parent.resolve()
                    and reference.is_file()
                ):
                    profiles.append((str(metadata["name"]), reference))
            except (OSError, KeyError, TypeError, ValueError):
                continue
        return sorted(profiles, key=lambda item: item[0].casefold())
