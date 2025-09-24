@echo off
echo Starting Reminder Agent Server...
.venv\Scripts\python.exe -m uvicorn webhook:app --host 0.0.0.0 --port 8080
pause
