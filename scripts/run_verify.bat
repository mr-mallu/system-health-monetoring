@echo off
set ROOT=%~dp0..
cd /d "%ROOT%"
python tests\verify_app.py > tests\verify_output.txt 2>&1
type tests\verify_output.txt
