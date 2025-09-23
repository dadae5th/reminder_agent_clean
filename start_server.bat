@echo off
title Reminder Web Server
cd /d "c:\Users\bae.jae.kwon\Documents\reminder_agent_clean"
echo 리마인더 웹 서버를 시작합니다...
echo 업무 완료 링크와 대시보드를 제공합니다.
echo 주소: http://localhost:8003
echo.
.\.venv\Scripts\python.exe -m uvicorn webhook:app --host 0.0.0.0 --port 8003
pause
