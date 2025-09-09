#!/usr/bin/env python3
"""
Standalone entry point for pogtool.

This script allows you to run pogtool directly without installing it as a package:
    python pogtool.py stats app.log --levels
    python pogtool.py compare old.log new.log
    python pogtool.py merge app1.log app2.log

For more information, see README.md or run:
    python pogtool.py --help
"""

import sys
import os

# Add the current directory to Python path so we can import the pogtool package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pogtool.cli import main

if __name__ == "__main__":
    main()