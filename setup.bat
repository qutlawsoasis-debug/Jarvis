@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ==================================================
echo         УСТАНОВКА АССИСТЕНТА ДЖАРВИСА
echo ==================================================
echo.

:: Проверка наличия Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА]: Python не установлен или не добавлен в PATH!
    echo Пожалуйста, установите Python с официального сайта (https://www.python.org)
    echo и не забудьте отметить галочку "Add Python to PATH" при установке.
    pause
    exit /b 1
)

:: Создание виртуального окружения
if not exist "backend\.venv" (
    echo [1/3] Создание виртуального окружения Python...
    python -m venv backend\.venv
    if !errorlevel! neq 0 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение.
        pause
        exit /b 1
    )
    echo Виртуальное окружение успешно создано.
) else (
    echo [1/3] Виртуальное окружение уже существует. Пропускаем создание.
)

:: Активация окружения и установка библиотек
echo [2/3] Обновление pip и установка зависимостей...
call backend\.venv\Scripts\activate.bat

python -m pip install --upgrade pip

:: Пытаемся установить зависимости
echo Установка requests, python-dotenv, edge-tts, SpeechRecognition...
python -m pip install requests python-dotenv edge-tts SpeechRecognition

:: Отдельная установка PyAudio с проверкой ошибок
echo Установка PyAudio (требуется для работы микрофона)...
python -m pip install pyaudio
if !errorlevel! neq 0 (
    echo.
    echo -----------------------------------------------------------------
    echo [ВНИМАНИЕ]: Стандартная установка PyAudio завершилась с ошибкой.
    echo Это часто случается на Windows, если нет прекомпилированного колеса (wheel)
    echo под вашу версию Python. Попытка установить через альтернативный метод...
    echo -----------------------------------------------------------------
    echo.
    python -m pip install pipwin
    python -m pipwin install pyaudio
    if !errorlevel! neq 0 (
        echo [КРИТИЧЕСКАЯ ОШИБКА]: Не удалось установить PyAudio.
        echo Попробуйте установить PyAudio вручную, скачав подходящий .whl файл 
        echo для вашей версии Python отсюда: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
        echo и запустив: pip install [имя_файла.whl]
        pause
        exit /b 1
    )
)

echo [3/3] Все библиотеки успешно установлены!
echo.
echo ==================================================
echo Настройка завершена!
echo Убедитесь, что в файле backend\.env указан ваш GEMINI_API_KEY.
echo Для запуска Джарвиса запустите файл run_jarvis.bat
echo ==================================================
echo.
pause
