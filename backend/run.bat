@echo off

@REM 進入 recogntionAPI 目錄
cd /d "%~dp0\recognitionAPI"

@REM 運行 python 腳本
python app.py %1