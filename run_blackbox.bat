@echo off
chcp 65001 > nul
title UniPlag & ICG — Enterprise BlackBox Launcher

echo ======================================================================
echo   🛡️  UniPlag & ICG Enterprise — Запуск из зашифрованного BlackBox
echo ======================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ❌ Ошибка: Виртуальное окружение .venv не найдено.
    echo Пожалуйста, установите зависимости:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

.venv\Scripts\python.exe run_blackbox.py --port 7932

pause
