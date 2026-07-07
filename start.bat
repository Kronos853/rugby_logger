@echo off
chcp 65001 >nul
title Sports Video Logger
cd /d "%~dp0"
echo.
echo === Sports Video Logger ===
echo Запуск Python-сервера...
echo Остановка: Ctrl+C
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start.ps1"
if errorlevel 1 (
    echo.
    echo Ошибка запуска.
    pause
)
