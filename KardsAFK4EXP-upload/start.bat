@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ==========================================
echo   KardsAFK4EXP - KARDS auto AFK script
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [!] Python not found in PATH. Install Python 3.8+ first.
    pause
    exit /b 1
)

python -c "import pyautogui, cv2, pygetwindow" >nul 2>nul
if errorlevel 1 (
    echo [*] First run: installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [!] Dependency install failed. Check your network / pip mirror.
        pause
        exit /b 1
    )
)

echo [*] Requires: game resolution 2220x1271, game language = Chinese
echo [*] Emergency stop: move mouse to the TOP-LEFT corner of the screen
echo.

python kards.py

echo.
echo [*] Script exited. See kards.log for details.
pause
