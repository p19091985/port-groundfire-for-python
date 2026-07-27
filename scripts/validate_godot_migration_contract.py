#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DOC = PROJECT_ROOT / "docs" / "godot_migration_strategy.md"

REQUIRED_GLOBAL_PHRASES = (
    "## Migration Compatibility Contract",
    "This is now an evolution-first migration.",
    "`versao-python/` and `versao-godot/godot/` are the canonical editions",
    "historical fidelity is comparison material rather than a hard product rule",
    "The Python/Pygame client remains the most useful behavioral reference for classic systems",
    "Prefer modern, testable architecture over exact historical coupling",
    "use SQLite for mutable runtime state where practical",
    (
        "Every migration implementation batch must name its reference material, user-visible contract, "
        "allowed adaptation, and required validation before code is treated as complete."
    ),
    "### Compatibility Annotation Template",
    "scripts/validate_godot_migration_contract.py",
    "docs/references/pygame_visual/",
)

COMPATIBILITY_ANNOTATION_LABELS = (
    "`Reference material:`",
    "`User-visible contract:`",
    "`Allowed adaptation:`",
    "`Required validation:`",
)

LEGACY_ANNOTATION_LABELS = (
    "`Fidelity target:`",
    "`User-visible invariants:`",
    "`Allowed Godot adaptation:`",
    "`Required validation:`",
)

PENDING_SECTION_HEADERS = (
    "### 1. Main Menu Visual Parity",
    "### 2. Server Browser Final Visual Parity",
    "### 3. Real Online Server Directory",
    "### 4. Local Match Gameplay Fidelity",
    "### 5. Input And HUD Completion",
    "### 6. Networked Gameplay Adapter",
    "### 7. Export And Runtime Validation",
)

# Scripts and CI files that must exist for the documented release/signing policy
# to be actionable.  These are part of the migration contract because the strategy
# document references them by name.
REQUIRED_RELEASE_FILES = (
    "scripts/sign_godot_release.sh",
    "scripts/validate_godot_release.sh",
    "scripts/package_godot_release.sh",
    "scripts/verify_godot_hosted_deployment.py",
    ".github/workflows/ci.yml",
    ".github/workflows/release.yml",
)


def _section_body(markdown: str, header: str) -> str:
    pattern = rf"^{re.escape(header)}\n(?P<body>.*?)(?=^### |^## |\Z)"
    match = re.search(pattern, markdown, flags=re.MULTILINE | re.DOTALL)
    return match.group("body") if match else ""


def validate_migration_contract(markdown: str) -> list[str]:
    errors: list[str] = []

    for phrase in REQUIRED_GLOBAL_PHRASES:
        if phrase not in markdown:
            errors.append(f"missing required migration compatibility phrase: {phrase}")

    for label in COMPATIBILITY_ANNOTATION_LABELS:
        if label not in markdown:
            errors.append(f"missing compatibility annotation template label: {label}")

    if "## What Still Needs To Be Done" not in markdown:
        errors.append("missing pending migration section: ## What Still Needs To Be Done")

    for header in PENDING_SECTION_HEADERS:
        body = _section_body(markdown, header)
        if not body:
            errors.append(f"missing pending migration subsection: {header}")
            continue
        has_compatibility_block = "Compatibility references:" in body
        has_legacy_block = "Fidelity annotations:" in body
        if not has_compatibility_block and not has_legacy_block:
            errors.append(f"{header} is missing a compatibility/reference annotations block")
            continue
        labels = COMPATIBILITY_ANNOTATION_LABELS if has_compatibility_block else LEGACY_ANNOTATION_LABELS
        for label in labels:
            if label not in body:
                errors.append(f"{header} is missing annotation label {label}")

    recommended_body = _section_body(markdown, "## Recommended Next Large Batch")
    if "Every recommended batch inherits the `Migration Compatibility Contract`." not in recommended_body:
        errors.append("Recommended Next Large Batch must explicitly inherit the Migration Compatibility Contract")

    return errors


def validate_release_files() -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_RELEASE_FILES:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            errors.append(f"missing required release/CI file: {rel_path}")
    return errors


def main() -> int:
    markdown = MIGRATION_DOC.read_text(encoding="utf-8")
    errors = validate_migration_contract(markdown)
    errors += validate_release_files()
    if errors:
        print("Godot migration compatibility contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Godot migration compatibility contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
