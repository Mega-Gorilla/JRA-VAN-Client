@echo off
echo ========================================
echo JV-Link Registry Setup (64-bit)
echo ========================================
echo.

cd /d "%~dp0"

if not exist "JV-Link.exe" (
    echo ERROR: JV-Link.exe not found
    echo.
    echo Please download JV-Link.exe and place it in this folder
    echo See DOWNLOAD_JVLINK.md for details
    echo.
    pause
    exit /b 1
)

echo Step 1: Generating registry file...
python create_registry.py
if errorlevel 1 (
    echo Failed to generate registry file
    pause
    exit /b 1
)

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Administrator privileges required
    echo Please right-click and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo.
echo Step 2: Applying registry settings...
reg import jvlink_localserver.reg
if errorlevel 1 (
    echo Failed to apply registry settings
    pause
    exit /b 1
)

echo.
echo SUCCESS: Registry settings applied!
echo.
pause