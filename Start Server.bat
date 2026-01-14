@echo off
cd /d "%~dp0"
echo Starting Topic Selection Server...
echo Connect at: http://192.168.0.103:5000
python app.py
pause