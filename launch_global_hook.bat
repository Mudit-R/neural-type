@echo off
title Neural-Type Global Keyboard Hook (Direct Python)
cd /d "%~dp0"
echo ============================================================
echo   Starting Neural-Type Live Global Hook (Python .venv)...
echo   Controls:
echo     [Ctrl + Alt + A] : Pause / Resume Autocorrect
echo     [Ctrl + Alt + Q] : Emergency Exit
echo     [Tab]            : Undo Last Correction
echo ============================================================
echo.
.venv\Scripts\python.exe win32_hook\global_keyboard_hook.py
pause
