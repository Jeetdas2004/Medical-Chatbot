@echo off
title Dr. Gemini - Multimodal Medical AI Chatbot
echo ========================================================
echo  🩺 Launching Dr. Gemini Multimodal Medical AI Chatbot
echo ========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python app.py
    goto end
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py app.py
    goto end
)

if exist "C:\Users\HP\AppData\Local\Programs\Python\Python310\python.exe" (
    "C:\Users\HP\AppData\Local\Programs\Python\Python310\python.exe" app.py
    goto end
)

echo [ERROR] Python not found in PATH or standard location.
echo Please install Python 3 or add it to PATH.
pause

:end

