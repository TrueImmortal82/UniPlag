@echo off
chcp 65001 > nul
title UniPlag & ICG — Enterprise BlackBox Launcher

echo ======================================================================
echo   🛡️  UniPlag & ICG — Запуск зашифрованного BlackBox контейнера
echo ======================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ❌ Ошибка: Виртуальное окружение .venv не найдено.
    pause
    exit /b 1
)

if not exist "dist\UniPlag_Enterprise.bbx" (
    echo 📦 Сборка зашифрованного контейнера dist\UniPlag_Enterprise.bbx...
    .venv\Scripts\python.exe scripts\build_blackbox.py
    echo.
)

.venv\Scripts\python.exe scripts\run_blackbox.py --port 7932

pause
