@echo off
title Neural-Type Enterprise Global Hook
cd /d "%~dp0"
echo ============================================================
echo   Starting Neural-Type Standalone Service...
echo   Executable: dist\NeuralType\NeuralType.exe
echo   Controls:
echo     [Ctrl + Alt + A] : Pause / Resume Autocorrect
echo     [Ctrl + Alt + Q] : Emergency Exit
echo     [Tab]            : Undo Last Correction
echo ============================================================
echo.
"dist\NeuralType\NeuralType.exe"
pause
