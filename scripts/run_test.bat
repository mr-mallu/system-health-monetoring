@echo off
set ROOT=%~dp0..
cd /d "%ROOT%"
python tests\test_imports.py
pause
