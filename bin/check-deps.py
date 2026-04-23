#!/usr/bin/env python3
"""Import-direction linter for the arbitrage bot.

Enforces the dependency rules documented in ARCHITECTURE.md §3:
- `consts.py` must not import any internal module.
- `api/*` must not import `compareprice/`, `main`, `collectMain`, or `commandMain`.
- `compareprice/*` must not import `main`, `collectMain`, or `commandMain`.
- `backtest/*` must not import `compareprice/`.
- Known violations are allow-listed (see KNOWN_VIOLATIONS).

Run: `python3 bin/check-deps.py`
Exit code: 0 on pass, 1 on any new violation.
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PY_EXCLUDE_DIRS = {"__pycache__", "data", ".venv", "venv", ".git"}

# Internal top-level modules (relative to repo root).
INTERNAL_MODULES = {
    "consts",
    "util",
    "main",
    "collectMain",
    "commandMain",
    "command_handlers",
    "graph_command_service",
    "order_execution",
    "position_reporting",
    "storage_utils",
    "telegram_utils",
    "logging_utils",
    "krwListingMain",
    "api",
    "compareprice",
    "backtest",
    "graph",
    "crawl",
}


def _layer_of(path: Path) -> str:
    """Classify a file by its architectural layer."""
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel == "consts.py":
        return "consts"
    if rel.startswith("api/"):
        return "api"
    if rel.startswith("compareprice/"):
        return "compareprice"
    if rel.startswith("backtest/"):
        return "backtest"
    if rel.startswith("graph/"):
        return "graph"
    if rel.startswith("crawl/"):
        return "crawl"
    if rel.startswith("bin/"):
        return "bin"
    if rel in {"main.py", "collectMain.py", "commandMain.py", "krwListingMain.py"}:
        return "entry"
    return "shared"


# Forbidden edges — {source_layer: {forbidden_target_top_level_name, ...}}.
FORBIDDEN = {
    "consts": {
        "util",
        "main",
        "collectMain",
        "commandMain",
        "api",
        "compareprice",
        "backtest",
        "graph",
        "crawl",
    },
    "api": {
        "compareprice",
        "main",
        "collectMain",
        "commandMain",
    },
    "compareprice": {
        "main",
        "collectMain",
        "commandMain",
    },
    "backtest": {
        "compareprice",
    },
}

# Pre-existing violations that are tracked in docs/exec-plans/tech-debt-tracker.md.
# Format: (source_rel_path, imported_top_level_module).
KNOWN_VIOLATIONS: set[tuple[str, str]] = set()


def iter_py_files():
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in PY_EXCLUDE_DIRS]
        for f in files:
            if f.endswith(".py"):
                yield Path(root) / f


def imported_top_modules(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                continue  # relative import — skip
            if node.module:
                roots.add(node.module.split(".", 1)[0])
    return roots


def main() -> int:
    violations: list[tuple[str, str, str]] = []
    for path in iter_py_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            print(f"[check-deps] syntax error: {path}: {exc}", file=sys.stderr)
            return 1

        layer = _layer_of(path)
        forbidden = FORBIDDEN.get(layer, set())
        if not forbidden:
            continue

        rel = path.relative_to(REPO_ROOT).as_posix()
        for target in imported_top_modules(tree):
            if target not in INTERNAL_MODULES:
                continue
            if target in forbidden:
                violations.append((rel, layer, target))

    new_violations = [
        (src, layer, tgt)
        for src, layer, tgt in violations
        if (src, tgt) not in KNOWN_VIOLATIONS
    ]
    allowed_hits = [
        (src, layer, tgt)
        for src, layer, tgt in violations
        if (src, tgt) in KNOWN_VIOLATIONS
    ]

    print("[check-deps] known violations (from tech-debt-tracker):")
    if allowed_hits:
        for src, layer, tgt in allowed_hits:
            print(f"  ALLOWED  {src} ({layer}) -> {tgt}")
    else:
        print("  none")

    print()
    print("[check-deps] new violations:")
    if new_violations:
        for src, layer, tgt in new_violations:
            print(f"  FAIL  {src} ({layer}) -> {tgt}")
        print()
        print("[check-deps] FAIL")
        return 1

    print("  none")
    print()
    print("[check-deps] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
