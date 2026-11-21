@echo off
cd /d "%~dp0"
title To-Do Agent
set MODEL=qwen2.5:14b

echo === Checking Ollama ===
ollama list >nul 2>&1
if not errorlevel 1 goto ollama_ok

echo Ollama is not running. Trying to start it...
start "" /min ollama serve
timeout /t 6 /nobreak >nul
ollama list >nul 2>&1
if not errorlevel 1 goto ollama_ok

echo.
echo Could not reach Ollama. Please start the Ollama app and try again.
pause
exit /b 1

:ollama_ok
echo Ollama is running.

echo === Checking model %MODEL% ===
ollama list | findstr /i /c:"%MODEL%" >nul
if not errorlevel 1 goto model_ok

echo.
echo The model %MODEL% is not installed.
echo Open Command Prompt and run:  ollama pull %MODEL%
pause
exit /b 1

:model_ok
echo Model found.

echo === Checking virtual environment ===
if exist "venv\Scripts\activate.bat" goto venv_ok

echo.
echo The folder venv was not found next to this file.
pause
exit /b 1

:venv_ok
call venv\Scripts\activate.bat

echo === Starting the app ===
echo The browser will open at http://127.0.0.1:7860
echo To stop the app, press Ctrl+C or close this window.
echo.
python app.py

echo.
echo The app has stopped.
pause