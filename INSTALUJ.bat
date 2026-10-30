@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALUJ.ps1"
exit /b %ERRORLEVEL%
