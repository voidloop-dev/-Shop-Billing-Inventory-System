@echo off
cd /d "%~dp0"
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Error starting app. Make sure Python is installed and requirements.txt packages are installed.
    echo Run:  pip install -r requirements.txt
    pause
)
