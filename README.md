# 해야할일LIST 자동 알림 AI Agent

- 메일은 매일 09:00(KST) 1회 발송
- daily/weekly/monthly 모두 '이번 사이클 기준 미완료'면 메일에 포함
- 메일의 '완료' 클릭 시 DB의 last_completed_at 갱신 -> 같은 사이클 동안 제외
- 성공 시 config.yaml의 dashboard_url로 즉시 리다이렉트

## 빠른 시작
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt

# 스키마 생성 & 샘플
python seed_sample.py --init --sample

# 실행 (웹훅 + 스케줄러)
python run_all.py --port 8510

# 즉시 발송 테스트(1회)
python run_all.py --port 8510 --send-now

웹훅 문서: http://localhost:8510/docs
대시보드 주소는 config.yaml의 dashboard_url에 설정하세요.
