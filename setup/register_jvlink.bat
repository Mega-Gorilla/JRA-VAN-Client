@echo off
echo ========================================
echo JV-Link.exe Registration
echo ========================================
echo.

cd /d "%~dp0"

if not exist "JV-Link.exe" (
    echo ERROR: JV-Link.exe not found in this directory
    echo.
    pause
    exit /b 1
)

echo Registering JV-Link.exe...
JV-Link.exe /regserver

if %errorlevel% == 0 (
    echo.
    echo SUCCESS: JV-Link.exe registered successfully!
) else (
    echo.
    echo ERROR: Registration failed. Please run as Administrator.
)

echo.
pause