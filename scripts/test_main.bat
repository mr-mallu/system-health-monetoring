@echo off
set ROOT=%~dp0..
cd /d "%ROOT%"
python -c "import sys; sys.path.insert(0, '.'); from main import main; print('Main module OK')"
