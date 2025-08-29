@echo off
REM ============================================================
REM JVLink Registry Setup for 32-bit Python
REM ============================================================
REM This batch file configures registry settings for 32-bit Python
REM to use JVLink COM components correctly
REM
REM Requirements:
REM   - Administrator privileges
REM   - JRA-VAN Data Lab. installed
REM   - 32-bit Python environment
REM ============================================================

echo ============================================================
echo JVLink Registry Setup for 32-bit Python
echo ============================================================
echo.

REM Check admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Administrator privileges required
    echo.
    echo Please run this batch file as Administrator:
    echo   1. Right-click on this file
    echo   2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking DLL existence...
set JVDTLAB_DLL=C:\Windows\SysWOW64\JVDTLAB\JVDTLAB.dll
if not exist "%JVDTLAB_DLL%" (
    echo ERROR: %JVDTLAB_DLL% not found
    echo Please install JRA-VAN Data Lab. first
    pause
    exit /b 1
)
echo OK: DLL found

echo.
echo [2/4] Registering DLL with 32-bit regsvr32...
REM Use 32-bit version of regsvr32
C:\Windows\SysWOW64\regsvr32.exe /s "%JVDTLAB_DLL%"
if %errorLevel% eq 0 (
    echo OK: DLL registered successfully
) else (
    echo WARNING: DLL registration may have failed
)

echo.
echo [3/4] Configuring registry for 32-bit Python...

REM CLSID registration
reg add "HKCR\CLSID\{2AB1774D-0C41-11D7-916F-0003479BEB3F}" /ve /d "JVDTLab.JVLink" /f >nul
reg add "HKCR\CLSID\{2AB1774D-0C41-11D7-916F-0003479BEB3F}\InprocServer32" /ve /d "%JVDTLAB_DLL%" /f >nul
reg add "HKCR\CLSID\{2AB1774D-0C41-11D7-916F-0003479BEB3F}\InprocServer32" /v "ThreadingModel" /d "Apartment" /f >nul

REM ProgID registration
reg add "HKCR\JVDTLab.JVLink" /ve /d "JVDTLab.JVLink" /f >nul
reg add "HKCR\JVDTLab.JVLink\CLSID" /ve /d "{2AB1774D-0C41-11D7-916F-0003479BEB3F}" /f >nul

REM Version-specific ProgID
reg add "HKCR\JVDTLab.JVLink.1" /ve /d "JVDTLab.JVLink" /f >nul
reg add "HKCR\JVDTLab.JVLink.1\CLSID" /ve /d "{2AB1774D-0C41-11D7-916F-0003479BEB3F}" /f >nul

REM Current version
reg add "HKCR\JVDTLab.JVLink\CurVer" /ve /d "JVDTLab.JVLink.1" /f >nul

REM WOW6432Node settings for compatibility
reg add "HKCR\WOW6432Node\CLSID\{2AB1774D-0C41-11D7-916F-0003479BEB3F}" /ve /d "JVDTLab.JVLink" /f >nul 2>nul
reg add "HKCR\WOW6432Node\CLSID\{2AB1774D-0C41-11D7-916F-0003479BEB3F}\InprocServer32" /ve /d "%JVDTLAB_DLL%" /f >nul 2>nul

echo OK: Registry configured for 32-bit Python

echo.
echo [4/4] Setup complete!
echo.
echo ============================================================
echo Setup Successful!
echo ============================================================
echo.
echo Registry has been configured for 32-bit Python.
echo.
echo To test the setup:
echo   1. Make sure you're using 32-bit Python
echo   2. Run: python test_32bit_jvlink.py
echo.
echo Note: If you're using 64-bit Python, it will NOT work.
echo       JVLink requires 32-bit Python.
echo.
pause