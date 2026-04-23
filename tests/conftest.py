"""Pytest bootstrap — make the repo root importable.

The project runs its entrypoints (`main.py`, `collectMain.py`) from the repo root,
so every internal import assumes the repo root is on sys.path. pytest collects from
./tests which shifts CWD, so we explicitly prepend the repo root here.
"""

from __future__ import annotations

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
