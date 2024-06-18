@echo off

set script_dir=%~dp0

cd /d "%script_dir%recognitionAPI"

python app.py %1