#!/usr/bin/env python3
"""Run the bundled tool directly from an installed skill."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from openfilmqa.__main__ import main
raise SystemExit(main())
