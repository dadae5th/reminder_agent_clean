# GitHub Codespaces에서 웹훅 서버 실행하기

## 1단계: 파일 커밋 및 푸시

```bash
git add .
git commit -m "웹훅 서버 클라우드 배포 준비"
git push origin automation-system
```

## 2단계: GitHub Codespace 생성

1. GitHub 리포지토리 (https://github.com/dadae5th/reminder_agent_clean) 접속
2. "Code" 버튼 클릭
3. "Codespaces" 탭 선택
4. "Create codespace on automation-system" 클릭

## 3단계: Codespace에서 환경 설정

```bash
# 환경변수 파일 생성
cat > .env << 'EOF'
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_service_key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASS=your_app_password
SMTP_SENDER_NAME=업무 알림 시스템
SMTP_SENDER_EMAIL=your_email
BASE_URL=https://your-codespace-url.githubpreview.dev
DASHBOARD_URL=https://your-codespace-url.githubpreview.dev/dashboard
SECRET=your_secret_key
EOF
```

## 4단계: 서버 실행

```bash
# 종속성 설치
pip install -r requirements.txt

# 웹훅 서버 시작
python webhook.py
```

## 5단계: 포트 공개 설정

1. Codespace 하단의 "PORTS" 탭 클릭
2. 포트 8080 찾기
3. "Visibility" 열에서 "Public" 선택
4. 생성된 URL 복사 (예: https://psychic-space-disco-abc123.githubpreview.dev)

## 6단계: 이메일 설정 업데이트

생성된 Codespace URL을 이메일 템플릿에 사용:
- BASE_URL을 Codespace URL로 업데이트
- DASHBOARD_URL을 Codespace URL/dashboard로 업데이트

## 장점

✅ **무료**: GitHub 무료 계정도 월 120시간 제공
✅ **안정성**: Microsoft Azure 기반 인프라
✅ **자동 SSL**: HTTPS 자동 제공
✅ **포트 포워딩**: 자동 포트 공개
✅ **영구 실행**: 브라우저 탭을 닫아도 계속 실행
✅ **GitHub 통합**: 코드 변경사항 자동 동기화

## 주의사항

⚠️ **비활성 시 종료**: 30분 비활성 시 자동 종료 (재시작 가능)
⚠️ **월 사용량 제한**: 무료 계정은 월 120시간 제한
⚠️ **임시 URL**: Codespace 재시작 시 URL 변경 가능성

## 대안: Render.com 자동 배포

더 안정적인 운영을 원한다면 Render.com 사용:

1. https://render.com 가입
2. GitHub 리포지토리 연결
3. "New Web Service" 생성
4. 환경변수 설정
5. 자동 배포 완료

이 방법은 완전 무료이고 24/7 실행됩니다.
