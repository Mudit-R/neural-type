"""
NeuraType: Enterprise Global Keyboard Hook Entry Point.
"""

import os
import sys

# Ensure base project directory is at head of sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Handle PyInstaller _MEIPASS bundle directory
if hasattr(sys, "_MEIPASS"):
    meipass = getattr(sys, "_MEIPASS")
    if meipass not in sys.path:
        sys.path.insert(0, meipass)

from win32_hook.global_keyboard_hook import main

if __name__ == "__main__":
    main()
