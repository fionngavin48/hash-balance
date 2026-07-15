#!/usr/bin/env python3
"""Run the interactive hash balance analysis without pip install."""

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from hash_balance.report import main

if __name__ == "__main__":
    main()
