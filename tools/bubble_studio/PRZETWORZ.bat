@echo off
setlocal
title Nokturn Bubble Studio - kolejka bez okna
set "BUBBLE_SCRIPT=%~dp0bootstrap.ps1"
if not exist "%BUBBLE_SCRIPT%" set "BUBBLE_SCRIPT=%~dp0tools\bubble_studio\bootstrap.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%BUBBLE_SCRIPT%" -Mode process
set "BUBBLE_EXIT=%ERRORLEVEL%"
echo.
pause
exit /b %BUBBLE_EXIT%
