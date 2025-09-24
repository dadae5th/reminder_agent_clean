# 🔍 Reminder Agent Clean - 코드 사용 현황 분석

## 📋 핵심 사용 파일들 (ACTIVE)

### 🌐 웹 서버 (GitHub Codespaces에서 24/7 실행)
- **webhook.py** ✅ - 메인 FastAPI 서버 (포트 8080)
  - 개별 업무 완료: `/complete?token=xxx`
  - 다중 업무 완료: POST `/complete-tasks`
  - 대시보드: `/dashboard`
  - 헬스체크: `/health`

### 📧 이메일 시스템 (GitHub Actions에서 매일 09:00 실행)
- **send_digest_supabase.py** ✅ - Supabase 연동 이메일 발송
- **mailer.py** ✅ - 이메일 발송 유틸리티
- **supabase_client.py** ✅ - Supabase 클라이언트

### 🗄️ 데이터베이스
- **reminder.db** ✅ - SQLite 데이터베이스 (우선 사용)
- **schema.sql** ✅ - 데이터베이스 스키마

### ⚙️ 설정 파일
- **config.yaml** ✅ - 서버 URL 및 SMTP 설정
- **.env** ✅ - 환경 변수 (로컬 개발용)
- **requirements.txt** ✅ - Python 패키지 의존성

### 🚀 GitHub Actions 워크플로우
- **.github/workflows/daily-email.yml** ✅ - 매일 이메일 발송

### 🐳 배포 설정
- **.devcontainer/devcontainer.json** ✅ - GitHub Codespaces 설정
- **start_codespace_server.sh** ✅ - 서버 자동 시작 스크립트
- **check_server_status.sh** ✅ - 서버 상태 확인 스크립트

## 🗑️ 사용하지 않는 파일들 (INACTIVE)

### 테스트/개발용 파일들
- add_test_tasks.py
- check_*.py (여러 개)
- debug_tokens.py
- generate_test_token.py
- get_test_tokens.py
- quick_*.py (여러 개)
- simple_*.py (여러 개)
- test_*.py (여러 개)
- manual_*.py (여러 개)
- reset_and_*.py

### 구버전 파일들
- digest.py (send_digest_supabase.py로 대체됨)
- task_manager.py (웹 대시보드로 대체됨)
- scheduler.py (GitHub Actions로 대체됨)
- generate_dashboard.py (webhook.py에 통합됨)

### 로컬 실행용 배치 파일들 (로컬에서만 사용)
- *.bat 파일들 (Windows 로컬 전용)

### 문서/가이드 파일들
- README*.md
- *.md 가이드 파일들
- 엑셀 템플릿 파일들

## 🎯 현재 시스템 아키텍처

```
GitHub Codespaces (24/7)
├── webhook.py (포트 8080)
│   ├── 개별 완료: /complete
│   ├── 다중 완료: /complete-tasks
│   └── 대시보드: /dashboard
│
GitHub Actions (매일 09:00)
├── send_digest_supabase.py
│   ├── SQLite 데이터 읽기
│   ├── 이메일 생성 (HTML)
│   └── SMTP 발송
│
데이터 저장
├── reminder.db (SQLite - 메인)
└── Supabase (백업/로그)
```

## 🔧 자동화 플로우

1. **GitHub Actions** (매일 09:00 KST)
   - send_digest_supabase.py 실행
   - SQLite에서 업무 데이터 조회
   - 이메일 HTML 생성 (완료 버튼 포함)
   - SMTP로 이메일 발송

2. **사용자 이메일 상호작용**
   - 개별 완료: GitHub Codespaces의 /complete 엔드포인트 호출
   - 다중 완료: /complete-tasks 엔드포인트로 POST 요청
   - 자동으로 대시보드로 리다이렉트

3. **서버 자동 복구** (새로 추가)
   - GitHub Codespaces 재시작 시 자동으로 서버 시작
   - 헬스체크 및 상태 모니터링

## 📊 최적화 완료 사항

✅ 개별 완료 기능 - 정상 작동
✅ 다중 완료 GET 안내페이지 - 사용자 친화적 메시지
✅ GitHub Actions 이메일 발송 - 매일 자동 실행
✅ URL 구조 수정 - base_url 문제 해결
✅ 자동 서버 시작 - Codespaces 재시작 대응
✅ 서버 상태 모니터링 - 자동 복구 스크립트
