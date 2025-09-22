@echo off
title Reminder Scheduler
cd /d "c:\Users\bae.jae.kwon\Documents\reminder_agent_clean"
echo 리마인더 스케줄러를 시작합니다...
echo 이 창을 닫지 마세요 - 매일 9시에 메일을 발송합니다.
echo.
.\.venv\Scripts\python.exe run_scheduler.py
pause
