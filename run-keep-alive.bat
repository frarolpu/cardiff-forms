@echo off
REM Keep Render Alive - Batch Script Launcher
REM This script runs the Python keep-alive bot and can be scheduled with Windows Task Scheduler

cd /d "C:\TempApp\Cardiff Forms"

REM Run the Python script
venv\Scripts\python.exe keep_render_alive.py

REM If script crashes, restart it after 60 seconds
if errorlevel 1 (
    echo Script crashed. Restarting in 60 seconds...
    timeout /t 60 /nobreak
    goto start
)

:start
goto start
