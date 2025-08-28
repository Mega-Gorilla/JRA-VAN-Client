@echo off
echo ========================================
echo Python Environment Check
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python first:
    echo 1. Download from https://www.python.org/downloads/
    echo 2. Run installer with "Add Python to PATH" checked
    echo 3. Restart this script after installation
    echo.
    pause
    exit /b 1
)

REM Show Python version
echo [OK] Python found:
python --version
echo.

REM Check Python version is 3.8+
python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python 3.8 or higher is required
    echo Please upgrade your Python installation
    echo.
    pause
    exit /b 1
)

echo [OK] Python version is compatible
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Not running as administrator
    echo The installer will request admin rights when needed
    echo.
)

echo All checks passed! You can now run:
echo   python install_windows.py
echo.
pause