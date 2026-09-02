@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul 2>&1

title UniPlag and ICG Enterprise - BlackBox Launcher

echo ======================================================================
echo   UniPlag + ICG Enterprise -- BlackBox In-Memory Launcher
echo ======================================================================
echo.

set "PY_EXE="
if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_EXE=python"
    )
)

if "%PY_EXE%"=="" (
    echo [ERROR] Python not found.
    echo Please install Python 3.10+ and run:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

"%PY_EXE%" run_blackbox.py --port 7932

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server exited with error code %errorlevel%.
    pause
)
