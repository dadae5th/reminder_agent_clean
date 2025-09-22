# 해야할일 자동 알림 시스템 (Supabase 연동)

매일 정해진 시간에 할 일 목록을 이메일로 발송하고, 이메일에서 직접 완료 처리할 수 있는 시스템입니다. **Supabase**와 연동하여 모든 데이터가 실시간으로 저장되고 관리됩니다.

## 🚀 주요 기능

- 📧 **자동 이메일 발송**: 매일 09:00(KST)에 미완료 업무 알림
- 🔄 **스마트 주기 관리**: daily/weekly/monthly 주기별 업무 관리
- ✅ **이메일 완료 처리**: 이메일에서 직접 업무 완료 클릭 가능
- 📊 **실시간 대시보드**: Supabase 연동으로 실시간 업무 현황 확인
- 🔗 **자동 리다이렉션**: 완료 후 대시보드로 자동 이동
- 🗄️ **Supabase 통합**: PostgreSQL 기반 클라우드 데이터베이스
- 📈 **완료 기록 추적**: 모든 완료 기록이 자동으로 저장 및 분석
- 🔐 **보안**: Row Level Security (RLS) 적용

## 🏗️ 시스템 아키텍처

```
📧 이메일 → 👆 클릭 → 🔗 FastAPI → 🗄️ Supabase → 📊 실시간 대시보드
```

## 📁 파일 구조

```
├── 🔧 설정 파일
│   ├── config.yaml           # SMTP, URL 설정
│   ├── .env                  # Supabase 인증 정보
│   └── requirements.txt      # Python 의존성
├── 🗄️ 데이터베이스
│   ├── supabase_client.py    # Supabase 클라이언트
│   ├── supabase_schema.sql   # Supabase 스키마
│   └── migrate_to_supabase.py # 마이그레이션 도구
├── 📧 이메일 시스템
│   ├── digest.py             # 이메일 발송 로직
│   ├── mailer.py             # 메일 전송 기능
│   └── scheduler.py          # 스케줄러
├── 🌐 웹 서버
│   ├── webhook.py            # FastAPI 서버
│   └── generate_dashboard.py # 대시보드 생성
├── 🔧 유틸리티
│   ├── add_task.py           # 업무 추가 도구
│   ├── import_from_excel.py  # 엑셀 가져오기
│   ├── run_server.bat        # 서버 실행 스크립트
│   └── send_digest.bat       # 이메일 발송 스크립트
└── 📚 문서
    └── README.md             # 이 파일
```

## 🛠️ 설치 및 설정

### 1. Python 환경 설정
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Supabase 프로젝트 설정

1. [Supabase](https://supabase.com)에서 새 프로젝트 생성
2. SQL Editor에서 `supabase_schema.sql` 실행
3. API 키 복사 (Project Settings → API)

### 3. 환경 설정 파일

**`.env` 파일 생성:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

**`config.yaml` 파일 수정:**
```yaml
base_url: http://localhost:8003
dashboard_url: http://localhost:8003/dashboard
smtp:
  host: smtp.gmail.com
  port: 465
  user: your-email@gmail.com
  pass: your-app-password
  sender_name: 해야할일 알림
  sender_email: your-email@gmail.com
```

### 4. 데이터 마이그레이션

```bash
# 기존 SQLite 데이터가 있는 경우
python migrate_to_supabase.py

# 새로 시작하는 경우 (샘플 데이터 생성)
python migrate_to_supabase.py
```

## 🚀 실행 방법

### 1. 서버 시작
```bash
# 배치 파일 사용
run_server.bat

# 또는 직접 실행
python -m uvicorn webhook:app --host 0.0.0.0 --port 8003
```

### 2. 이메일 발송 테스트
```bash
# 배치 파일 사용
send_digest.bat

# 또는 직접 실행
python digest.py
```

## 📊 대시보드 및 API

### 웹 인터페이스
- **대시보드**: http://localhost:8003/dashboard
- **이메일 테스트**: http://localhost:8003/send-test-email
- **서버 상태**: http://localhost:8003/health

### REST API 엔드포인트
- `GET /api/stats` - 업무 통계
- `GET /api/tasks` - 모든 업무 조회
- `GET /api/completions` - 완료 기록 조회
- `POST /api/tasks` - 새 업무 생성

## 🔄 워크플로우

1. **📧 이메일 발송**: 스케줄러가 매일 09:00에 자동 발송
2. **👆 업무 완료**: 이메일의 완료 버튼 클릭
3. **🗄️ 자동 저장**: Supabase에 완료 기록 실시간 저장
4. **📊 대시보드 업데이트**: 실시간으로 상태 반영
5. **📈 분석**: 완료 기록 및 통계 자동 생성

## 🎯 Supabase 테이블 구조

- `users` - 사용자 정보
- `tasks` - 업무 정보 (제목, 담당자, 주기, 상태)
- `completion_logs` - 완료 기록 (시간, 방법, IP, User-Agent)
- `email_logs` - 이메일 발송 기록
- `system_settings` - 시스템 설정

## 🔧 고급 기능

### 자동 새로고침
대시보드는 30초마다 자동으로 새로고침되어 실시간 상태를 표시합니다.

### 완료 기록 추적
모든 완료 활동이 다음 정보와 함께 기록됩니다:
- 완료 시간 (KST)
- 완료 방법 (이메일/대시보드/API)
- 클라이언트 IP 주소
- User-Agent 정보

### 이메일 발송 로그
모든 이메일 발송 기록이 저장되어 배송 상태를 추적할 수 있습니다.

## 🔒 보안

- Supabase Row Level Security (RLS) 적용
- HTTPS 지원 (프로덕션 환경)
- API 키 암호화 저장
- 토큰 기반 업무 완료 인증

## 🆘 문제 해결

### Supabase 연결 오류
```bash
# 연결 테스트
python -c "from supabase_client import supabase_manager; print(supabase_manager.get_task_statistics())"
```

### 이메일 발송 실패
1. Gmail 앱 비밀번호 확인
2. `config.yaml`의 SMTP 설정 확인
3. 방화벽 포트 465 허용

### 대시보드 접속 불가
1. 서버 실행 상태 확인: http://localhost:8003/health
2. 포트 8003 사용 여부 확인
3. Supabase 연결 상태 확인

## 🚀 프로덕션 배포

1. **환경 변수 설정**: `.env` 파일의 실제 Supabase 정보 입력
2. **HTTPS 설정**: 리버스 프록시 (nginx) 설정
3. **도메인 연결**: `config.yaml`의 URL을 실제 도메인으로 변경
4. **모니터링**: Supabase 대시보드에서 실시간 모니터링
