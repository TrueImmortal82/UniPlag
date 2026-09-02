@echo off
setlocal
cd /d "%~dp0"

echo ===================================================
echo   UniPlag Server Launcher
echo ===================================================

if exist "dist\UniPlag_Server\UniPlag_Server.exe" (
    "dist\UniPlag_Server\UniPlag_Server.exe" %*
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run_server.py %*
) else (
    python run_server.py %*
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Server stopped with exit code %ERRORLEVEL%.
    pause
)
