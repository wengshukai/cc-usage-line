@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在安装 Claude Code 状态栏...
echo.
python install.py
echo.
pause
