@echo off
setlocal

set "VENV_DIR=%~dp0.venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create virtual environment. Make sure Python is installed.
        pause
        exit /b 1
    )
)

call "%VENV_DIR%\Scripts\activate.bat"

pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo Starting pyLapse Web UI...
python "%~dp0web_ui.py" %*
