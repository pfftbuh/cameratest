@echo off
REM Change directory to the folder where this batch file lives
cd /d %~dp0

REM Activate your venv
call ..\312venv\Scripts\activate.bat

REM Set Django settings module for this project
set DJANGO_SETTINGS_MODULE=cameratest.settings

REM Run Daphne on port 8000
python -m daphne -p 8000 cameratest.routing:application
