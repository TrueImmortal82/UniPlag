@echo off
setlocal
cd /d "%~dp0"
set "PORT=7894"

netstat -ano | findstr /R ":7894 .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [!] Port %PORT% is already in use. Owning process(es):
    netstat -ano | findstr /R ":7894 .*LISTENING"
    choice /C YN /N /M "Kill owning PID(s) and start fresh? [Y/N] "
    if errorlevel 2 exit /b 1
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R ":7894 .*LISTENING"') do (
        taskkill /F /PID %%p >nul 2>&1
    )
)

.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port %PORT%
endlocal