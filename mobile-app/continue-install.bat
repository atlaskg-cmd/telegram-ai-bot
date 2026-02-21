@echo off
chcp 65001 >nul
echo ============================================================
echo    AI Bot Mobile App - Продолжение установки
echo ============================================================
echo.

REM Flutter путь
set FLUTTER_PATH=C:\flutter\flutter\bin

REM Обновление PATH
set PATH=%PATH%;%FLUTTER_PATH%

echo [i] Переход в директорию проекта...
cd /d "%~dp0"
echo [✓] Директория: %CD%
echo.

echo [i] Проверка Flutter...
call flutter --version --suppress-analytics
echo.

echo [i] Принятие лицензий Android...
call flutter doctor --android-licenses 2>nul || echo [!] Лицензии не приняты (требуется ручной ввод)
echo.

echo [i] Инициализация проекта...
call flutter create . --platforms=android,ios
echo.

echo [i] Установка зависимостей...
call flutter pub get
echo.

echo [i] Проверка установки...
call flutter doctor -v
echo.

echo ============================================================
echo    Установка завершена!
echo ============================================================
echo.
echo Для запуска приложения:
echo   1. Убедитесь что Android эмулятор запущен или устройство подключено
echo   2. Выполните: flutter run
echo.
echo Или запустите этот файл снова для автоматического запуска
echo.
pause
