# 웹훅 서버 클라우드 배포 가이드

## 방법 1: GitHub Codespaces 사용 (추천)

1. **GitHub 리포지토리에서 Codespace 생성**:
   - GitHub 리포지토리 페이지에서 "Code" 버튼 클릭
   - "Codespaces" 탭 선택
   - "Create codespace on main" 클릭

2. **Codespace에서 서버 실행**:
   ```bash
   # 종속성 설치
   pip install -r requirements.txt
   
   # 환경변수 설정 (.env 파일 생성)
   echo "SUPABASE_URL=your_url" > .env
   echo "SUPABASE_KEY=your_key" >> .env
   # ... 기타 환경변수들
   
   # 웹훅 서버 시작
   python webhook.py
   ```

3. **포트 포워딩 설정**:
   - Codespace에서 자동으로 포트 8080을 감지
   - "Ports" 탭에서 포트를 "Public"으로 설정
   - 제공된 URL을 이메일 설정에 사용

## 방법 2: Render.com 배포

1. **Render.com 계정 생성**: https://render.com
2. **GitHub 리포지토리 연결**
3. **Web Service 생성**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn webhook:app --host 0.0.0.0 --port $PORT`
4. **환경변수 설정**: 모든 Supabase 및 SMTP 환경변수 추가

## 방법 3: Railway 배포

1. **Railway 계정 생성**: https://railway.app
2. **GitHub 리포지토리 연결**
3. **자동 배포 설정**: railway.json 파일 사용
4. **환경변수 설정**: Dashboard에서 환경변수 추가

## 추천 순서

1. **GitHub Codespaces** (가장 간단, 개발용)
2. **Render.com** (무료, 프로덕션 가능)
3. **Railway** (유료지만 안정적)

각 방법의 장단점:

### GitHub Codespaces
✅ 무료 (월 120시간)
✅ GitHub과 완전 통합
✅ 개발환경과 동일
❌ 월 사용량 제한
❌ 비활성 시 자동 종료

### Render.com
✅ 무료 플랜 제공
✅ 자동 배포
✅ SSL 인증서 자동
❌ 무료 플랜은 비활성 시 슬립

### Railway
✅ 매우 안정적
✅ 실시간 로그
✅ 자동 SSL
❌ 유료 (월 $5부터)
