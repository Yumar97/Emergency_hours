@echo off
cd /d "C:\Users\yumar\OneDrive\Escritorio\Trabajo_EsSalud"
start "" python app.py
timeout /t 3 >nul
start http://127.0.0.1:5000
