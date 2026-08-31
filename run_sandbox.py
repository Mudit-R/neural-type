"""
Convenience launcher for the AI Autocorrect Safe Sandbox Testbed.
"""

import os
import sys

# Ensure local venv python is running
base_dir = os.path.dirname(os.path.abspath(__file__))
sandbox_script = os.path.join(base_dir, "test_sandbox", "sandbox_gui.py")

if __name__ == "__main__":
    import subprocess
    venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        venv_python = sys.executable
    subprocess.run([venv_python, sandbox_script])
