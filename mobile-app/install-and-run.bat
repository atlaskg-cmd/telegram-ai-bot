@echo off
chcp 65001 >nul
echo ============================================================
echo    AI Bot Mobile App - Установка и запуск
echo ============================================================
echo.

REM Проверка наличия Flutter
where flutter >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Flutter SDK не найден!
    echo.
    echo Для установки Flutter выполните:
    echo   1. Откройте PowerShell от имени администратора
    echo   2. Выполните: winget install --id Google.Flutter --exact
    echo   3. Перезапустите терминал
    echo.
    echo Или скачайте вручную:
    echo   https://github.com/flutter/flutter/releases
    echo.
    echo Нажмите Enter для выхода...
    pause >nul
    exit /b 1
)

echo [✓] Flutter найден
flutter --version
echo.

REM Переход в директорию проекта
cd /d "%~dp0"
echo [i] Директория проекта: %CD%
echo.

REM Инициализация платформ (если нужно)
if not exist "android" (
    echo [i] Инициализация Android платформы...
    flutter create . --platforms=android
) else (
    echo [✓] Android платформа существует
)

if not exist "ios" (
    echo [i] Инициализация iOS платформы...
    flutter create . --platforms=ios
) else (
    echo [✓] iOS платформа существует
)
echo.

REM Установка зависимостей
echo [i] Установка зависимостей...
flutter pub get
if %errorlevel% neq 0 (
    echo [!] Ошибка установки зависимостей!
    pause
    exit /b 1
)
echo [✓] Зависимости установлены
echo.

REM Проверка
echo [i] Проверка установки...
flutter doctor -v
echo.

REM Предложение запустить приложение
echo ============================================================
echo    Готово к запуску!
echo ============================================================
echo.
echo Выберите действие:
echo   1. Запустить приложение (flutter run)
echo   2. Проверить устройства (flutter devices)
echo   3. Выйти
echo.
set /p choice="Ваш выбор (1-3): "

if "%choice%"=="1" (
    echo.
    echo [i] Запуск приложения...
    echo Примечание: Убедитесь что эмулятор запущен или устройство подключено
    flutter run
) else if "%choice%"=="2" (
    echo.
    flutter devices
    pause
) else if "%choice%"=="3" (
    echo.
    echo Выход...
) else (
    echo.
    echo Неверный выбор. Выход...
)

echo.
echo ============================================================
echo    Установка завершена!
echo ============================================================
pause
