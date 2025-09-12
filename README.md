# 해야할일 자동 알림 시스템

매일 정해진 시간에 할 일 목록을 이메일로 발송하고, 이메일에서 직접 완료 처리할 수 있는 시스템입니다.

## 주요 기능

- 📧 **자동 이메일 발송**: 매일 09:00(KST)에 미완료 업무 알림
- 🔄 **스마트 주기 관리**: daily/weekly/monthly 주기별 업무 관리
- ✅ **이메일 완료 처리**: 이메일에서 직접 업무 완료 클릭 가능
- 📊 **실시간 대시보드**: 업무 현황을 실시간으로 확인
- 🔗 **자동 리다이렉션**: 완료 후 대시보드로 자동 이동

## 파일 구조

```
├── config.yaml           # 설정 파일 (SMTP, URL 등)
├── db.py                 # 데이터베이스 로직
├── digest.py             # 이메일 발송 로직
├── generate_dashboard.py # 대시보드 생성
├── mailer.py             # 메일 전송 기능
├── scheduler.py          # 스케줄러
├── webhook.py            # 웹 서버 (FastAPI)
├── schema.sql            # DB 스키마
├── reminder.db           # SQLite 데이터베이스
├── requirements.txt      # Python 의존성
├── run_server.bat        # 서버 실행 스크립트
└── send_digest.bat       # 즉시 이메일 발송 스크립트
```

## 설치 및 실행

### 1. 환경 설정
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. 데이터베이스 초기화
```bash
sqlite3 reminder.db < schema.sql
```

### 3. 설정 파일 수정
`config.yaml`에서 SMTP 설정과 URL을 수정하세요.

### 4. 서버 실행
```bash
# 배치 파일 사용
run_server.bat

# 또는 직접 실행
python -m uvicorn webhook:app --host 0.0.0.0 --port 8003
```

### 5. 이메일 발송 테스트
```bash
# 배치 파일 사용
send_digest.bat

# 또는 직접 실행
python digest.py
```

## 사용 방법

1. **서버 시작**: `run_server.bat` 실행
2. **대시보드 확인**: http://localhost:8003/dashboard
3. **이메일 발송**: `send_digest.bat` 또는 스케줄러가 자동 발송
4. **업무 완료**: 이메일의 완료 버튼 클릭하면 자동으로 대시보드로 이동

## API 엔드포인트

- `GET /health` - 서버 상태 확인
- `GET /dashboard` - 대시보드 페이지
- `GET /complete?token=<TOKEN>` - 업무 완료 처리
- `POST /complete-tasks` - 다중 업무 완료 처리
- `GET /send-test-email` - 테스트 이메일 발송
