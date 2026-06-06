#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIGRATION_DOC = PROJECT_ROOT / "docs" / "godot_migration_strategy.md"

REQUIRED_GLOBAL_PHRASES = (
    "## Migration Fidelity Contract",
    "User experience cannot be changed by the migration.",
    "The Python/Pygame client is the behavioral, visual, input, audio, timing, and flow source of truth",
    "Godot browser goldens are regression captures, not fidelity targets.",
    (
        "Every migration implementation batch must name its Pygame reference, user-visible invariants, "
        "allowed Godot adaptation, and required validation before code is treated as complete."
    ),
    "### Fidelity Annotation Template",
    "scripts/validate_godot_migration_contract.py",
    "docs/references/pygame_visual/",
)

ANNOTATION_LABELS = (
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


def _section_body(markdown: str, header: str) -> str:
    pattern = rf"^{re.escape(header)}\n(?P<body>.*?)(?=^### |^## |\Z)"
    match = re.search(pattern, markdown, flags=re.MULTILINE | re.DOTALL)
    return match.group("body") if match else ""


def validate_migration_contract(markdown: str) -> list[str]:
    errors: list[str] = []

    for phrase in REQUIRED_GLOBAL_PHRASES:
        if phrase not in markdown:
            errors.append(f"missing required migration fidelity phrase: {phrase}")

    for label in ANNOTATION_LABELS:
        if label not in markdown:
            errors.append(f"missing fidelity annotation template label: {label}")

    if "## What Still Needs To Be Done" not in markdown:
        errors.append("missing pending migration section: ## What Still Needs To Be Done")

    for header in PENDING_SECTION_HEADERS:
        body = _section_body(markdown, header)
        if not body:
            errors.append(f"missing pending migration subsection: {header}")
            continue
        if "Fidelity annotations:" not in body:
            errors.append(f"{header} is missing a Fidelity annotations block")
        for label in ANNOTATION_LABELS:
            if label not in body:
                errors.append(f"{header} is missing annotation label {label}")

    recommended_body = _section_body(markdown, "## Recommended Next Large Batch")
    if "Every recommended batch inherits the `Migration Fidelity Contract`." not in recommended_body:
        errors.append("Recommended Next Large Batch must explicitly inherit the Migration Fidelity Contract")

    return errors


def main() -> int:
    markdown = MIGRATION_DOC.read_text(encoding="utf-8")
    errors = validate_migration_contract(markdown)
    if errors:
        print("Godot migration fidelity contract validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Godot migration fidelity contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
