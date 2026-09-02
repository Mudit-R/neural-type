@echo off
title NeuraType Enterprise Global Hook
cd /d "%~dp0"
echo ============================================================
echo   Starting NeuraType Standalone Service...
echo   Executable: NeuraType.exe
echo   Controls:
echo     [Ctrl + Alt + A] : Pause / Resume Autocorrect
echo     [Ctrl + Alt + Q] : Emergency Exit
echo     [Tab]            : Undo Last Correction
echo ============================================================
echo.
if exist "NeuraType.exe" (
    "NeuraType.exe" %*
) else if exist "dist\NeuraType.exe" (
    "dist\NeuraType.exe" %*
) else (
    echo Error: NeuraType.exe not found.
)
pause
