@echo off
echo ======================================
echo  StudyPlatform - настройка окружения
echo ======================================
echo.

:: Проверяем, есть ли Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python не найден. Установи Python 3.10+
    pause
    exit /b 1
)

:: Создаём виртуальное окружение, если нет
if not exist ".venv" (
    echo Создание виртуального окружения...
    python -m venv .venv
    echo OK
) else (
    echo Виртуальное окружение уже существует
)

:: Активируем
echo Активация окружения...
call .venv\Scripts\activate.bat

:: Устанавливаем зависимости
echo Установка зависимостей...
pip install -r requirements.txt

:: Создаём папки, если нет
if not exist "static\uploads" mkdir static\uploads
if not exist "static\uploads\avatars" mkdir static\uploads\avatars
if not exist "static\css" mkdir static\css

:: Инициализируем базу
echo Инициализация базы данных...
python seed.py

echo.
echo ======================================
echo  Готово! Запуск приложения...
echo ======================================
echo.
echo  Админ: admin@study.ru / admin123
echo  Студент: student@study.ru / student123
echo.

:: Запуск
python run.py
pause