@echo off
title All Services Starter
echo ==========================================
echo 리마인더 시스템 전체 시작
echo ==========================================
echo.
echo 1. 웹 서버 시작 중...
start "Reminder Web Server" "%~dp0start_server.bat"
timeout /t 3 /nobreak >nul

echo 2. 스케줄러 시작 중...
start "Reminder Scheduler" "%~dp0start_scheduler.bat"
timeout /t 3 /nobreak >nul

echo.
echo ✅ 모든 서비스가 시작되었습니다!
echo.
echo 📧 매일 9시에 자동으로 메일이 발송됩니다.
echo 🌐 웹 서버: http://localhost:8001
echo 📊 대시보드: http://localhost:8001/dashboard
echo.
echo ⚠️  두 개의 새 창을 닫지 마세요!
echo.
pause
