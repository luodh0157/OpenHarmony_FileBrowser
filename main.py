#!/usr/bin/env python3
"""
OpenHarmony File Browser - Main Entry Point
Run: python main.py
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import main

if __name__ == "__main__":
    main()