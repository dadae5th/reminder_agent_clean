# GitHub Actions 자동화 설정 가이드

## ✅ 1단계: 파일 준비 완료
- `.github/workflows/daily-email.yml` 생성됨
- 매일 한국시간 오전 9시에 자동 실행 설정

## 🔐 2단계: GitHub Secrets 설정 (중요!)

GitHub 저장소에서 다음 작업을 수행하세요:

1. **GitHub 저장소 페이지로 이동**
   - https://github.com/dadae5th/reminder_agent_clean

2. **Settings 탭 클릭**

3. **왼쪽 메뉴에서 "Secrets and variables" > "Actions" 클릭**

4. **"New repository secret" 버튼을 클릭하여 다음 9개 추가:**

### Supabase 설정
- **SUPABASE_URL**: `https://jonwwtjhrwyxckmnlofh.supabase.co`
- **SUPABASE_KEY**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impvbnd3dGpocnd5eGNrbW5sb2ZoIiwicm9zZSI6ImFub24iLCJpYXQiOjE3NTg1MjEzMzUsImV4cCI6MjA3NDA5NzMzNX0.IwRTjWnCDJIr-PzKMjisPmZB9RC6lJevD4NpZpkjs60`
- **SUPABASE_SERVICE_KEY**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impvbnd3dGpocnd5eGNrbW5sb2ZoIiwicm9zZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1ODUyMTMzNSwiZXhwIjoyMDc0MDk3MzM1fQ.BXIiFlBnnvsAIEHwaMTVG8NYg_YOAg_kp5cNoz9rWWM`

### SMTP 이메일 설정
- **SMTP_HOST**: `smtp.gmail.com`
- **SMTP_PORT**: `465`
- **SMTP_USER**: `dadae5th@gmail.com`
- **SMTP_PASS**: `kptwwtdbavjgajly`
- **SMTP_SENDER_NAME**: `해야할일 알림`
- **SMTP_SENDER_EMAIL**: `dadae5th@gmail.com`

### 서버 설정
- **BASE_URL**: `https://your-app.herokuapp.com` (배포 후 실제 URL로 변경)
- **DASHBOARD_URL**: `https://your-app.herokuapp.com/dashboard`
- **SECRET**: `gBckLh5s3CSP5VIu6TPi0f1aic6tofQ9EFgrcwf24W1Zl4B2`

## 🚀 3단계: GitHub에 Push

현재 폴더에서 다음 명령어 실행:

```bash
git add .
git commit -m "Add GitHub Actions for daily email automation"
git push origin main
```

## ⚡ 4단계: 수동 테스트

1. GitHub 저장소 > "Actions" 탭
2. "Daily Email Reminder" 워크플로우 클릭
3. "Run workflow" 버튼으로 즉시 테스트 가능

## 🎯 결과
- **매일 한국시간 오전 9시**에 자동으로 이메일 발송
- **PC가 꺼져있어도** 클라우드에서 실행
- **GitHub Actions 로그**에서 실행 결과 확인 가능

## ⚠️ 주의사항
- GitHub 저장소가 **Public**이어야 무료로 사용 가능
- **Private**인 경우 월 2000분 제한 있음 (일반적으로 충분함)

설정 완료 후 알려주시면 테스트해보겠습니다!
