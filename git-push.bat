@echo off
cd telegram-ai-bot
echo.
echo === Добавление всех изменений ===
.\..\cmd\git.exe add .
echo.
set /p msg="Введи описание изменений: "
echo.
echo === Создание коммита ===
.\..\cmd\git.exe commit -m "%msg%"
echo.
echo === Отправка на GitHub ===
.\..\cmd\git.exe push
echo.
echo Готово! Нажми любую клавишу...
pause > nul
