"""Day 22 verify — panel docs pack present."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"

REQUIRED = [
    "PANEL_SYNOPSIS.md",
    "ARCHITECTURE.md",
    "MODULE_TECH_STACK.md",
    "DATASET.md",
    "PANEL_PACK.md",
    "SAMPLE_CCTV_PACK.md",
    "DEMO_CHECKLIST.md",
    "ML_RECOMMENDER.md",
]


def main() -> int:
    missing = []
    for name in REQUIRED:
        path = DOCS / name
        if not path.exists() or path.stat().st_size < 200:
            missing.append(name)
            print(f"[FAIL] missing/short {name}")
        else:
            print(f"[PASS] {name} ({path.stat().st_size} bytes)")

    # Synopsis should mention key product terms
    syn = (DOCS / "PANEL_SYNOPSIS.md").read_text(encoding="utf-8")
    for token in ("CrowdPulse", "DCRS", "Gradient Boosting", "YOLO"):
        assert token in syn, f"synopsis missing {token}"
    print("[PASS] synopsis contains core terms")

    arch = (DOCS / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "mermaid" in arch
    print("[PASS] architecture includes mermaid diagrams")

    data = (DOCS / "DATASET.md").read_text(encoding="utf-8")
    assert "synthetic" in data.lower() and "YOLO" in data
    print("[PASS] dataset doc covers YOLO + synthetic GB labels")

    if missing:
        print("Day 22 verification FAILED")
        return 1
    print("Day 22 verification OK — panel docs ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
