@echo off
title AI Autocorrect Sandbox
cd /d "%~dp0"
echo Starting AI Autocorrect Safe Sandbox...
.venv\Scripts\python.exe test_sandbox\sandbox_gui.py
pause
