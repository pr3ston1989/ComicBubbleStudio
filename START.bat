@echo off
setlocal
wscript.exe "%~dp0START.vbs"
exit /b %ERRORLEVEL%
