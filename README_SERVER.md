# 서버 배포(요약)
1) 서버에 프로젝트 업로드(/opt/reminder)
2) config.yaml 수정: base_url=http://<서버IP>:8510, dashboard_url=http://<서버IP>:8505
3) 설치: sudo bash install_server.sh
4) 서비스 시작: sudo systemctl enable --now reminder.service
5) 헬스체크: curl http://127.0.0.1:8510/health
