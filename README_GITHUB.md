# GitHub Actions 자동 메일 발송 설정 가이드

## 🎯 목표
PC가 꺼져 있어도 GitHub Actions를 통해 매일 오전 9시에 자동으로 업무 알림 메일을 발송합니다.

## 📋 설정 단계

### 1. GitHub Repository 생성 및 코드 업로드
```bash
cd c:\Users\bae.jae.kwon\Documents\reminder_agent_clean
git init
git add .
git commit -m "Initial commit: Reminder system"
git branch -M main
git remote add origin https://github.com/dadae5th/reminder_agent_clean.git
git push -u origin main
```

### 2. GitHub Secrets 설정
Repository → Settings → Secrets and variables → Actions에서 다음 secrets 추가:

#### 필수 Secrets:
- `SMTP_USER`: dadae5th@gmail.com
- `SMTP_PASS`: kptwwtdbavjgajly
- `SECRET_KEY`: gBckLh5s3CSP5VIu6TPi0f1aic6tofQ9EFgrcwf24W1Zl4B2
- `BASE_URL`: https://your-server-url.com/complete (나중에 설정)
- `DASHBOARD_URL`: https://your-server-url.com/dashboard (나중에 설정)

### 3. 스케줄 확인
- GitHub Actions는 **매일 오전 9시 (KST)**에 자동 실행됩니다
- `cron: '0 0 * * *'`는 UTC 0시 = KST 9시입니다

### 4. 수동 실행
- GitHub Repository → Actions → "Daily Reminder Email" → "Run workflow" 버튼으로 수동 실행 가능

## ⚡ 즉시 테스트 방법

### 테스트용 즉시 실행 스케줄 (5분마다)
```yaml
# .github/workflows/test-reminder.yml
on:
  schedule:
    - cron: '*/5 * * * *'  # 5분마다 실행 (테스트용)
```

### 현재 시간 기준 1분 후 실행
```yaml
# 현재 시간이 09:15라면
- cron: '16 0 * * *'  # UTC 00:16 = KST 09:16
```

## 🔧 로컬 PC 설정 (백업용)

로컬에서도 실행하려면:
```bash
# 한번만 실행
start_all.bat

# 또는 개별 실행
start_scheduler.bat  # 스케줄러만
start_server.bat     # 웹서버만
```

## 📊 모니터링

### GitHub Actions에서 확인:
1. Repository → Actions
2. "Daily Reminder Email" 워크플로우 확인
3. 실행 로그에서 성공/실패 확인

### 메일 발송 확인:
- 매일 오전 9시 이후 메일함 확인
- 실패 시 GitHub Actions 로그 확인

## 🎁 추가 기능

### 웹 서버 클라우드 배포 (선택사항)
- Heroku, Railway, Render 등을 사용하여 웹 서버도 클라우드에 배포 가능
- 그러면 PC 없이도 업무 완료 링크와 대시보드 접근 가능

## ⚠️ 중요 사항
1. **GitHub Secrets 보안**: 절대 코드에 직접 비밀번호 작성 금지
2. **cron 시간 확인**: UTC와 KST 시간차 9시간 주의
3. **무료 한도**: GitHub Actions 무료 계정은 월 2000분 제한
4. **데이터베이스**: SQLite 파일이 GitHub에 저장되므로 백업됨
