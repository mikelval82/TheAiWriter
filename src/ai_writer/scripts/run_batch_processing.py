#!/usr/bin/env python3
"""Script to run batch PDF processing."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ai_writer.processors.batch_processor import main

if __name__ == "__main__":
    main()
