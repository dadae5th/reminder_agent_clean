#!/bin/bash
# start_codespace_server.sh - GitHub Codespaces에서 서버 자동 시작

echo "🚀 GitHub Codespaces 서버 자동 시작 스크립트"
echo "현재 시간: $(date)"

# 환경 변수 확인
echo "📊 환경 변수 상태:"
echo "- CODESPACE_NAME: ${CODESPACE_NAME:-'not set'}"
echo "- GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN: ${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-'not set'}"

# Python 환경 확인
echo "🐍 Python 환경:"
python --version
pip --version

# 필요한 패키지 설치
echo "📦 패키지 설치 중..."
pip install -r requirements.txt

# 데이터베이스 초기화 (필요시)
echo "🗄️ 데이터베이스 확인..."
if [ ! -f "reminder.db" ]; then
    echo "데이터베이스 생성 중..."
    python -c "
import sqlite3
conn = sqlite3.connect('reminder.db')
conn.execute('''CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')
conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    assignee_email TEXT,
    frequency TEXT CHECK(frequency IN ('daily', 'weekly', 'monthly')),
    status TEXT DEFAULT 'pending',
    assignee TEXT,
    hmac_token TEXT,
    last_completed_at TEXT,
    due_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assignee_email) REFERENCES users (email)
)''')
conn.commit()
conn.close()
print('데이터베이스 초기화 완료')
"
fi

# 기존 서버 프로세스 종료
echo "🔄 기존 서버 프로세스 확인..."
pkill -f "python.*webhook.py" 2>/dev/null || true

# 서버 시작
echo "🌟 웹훅 서버 시작..."
export PORT=8080
nohup python webhook.py > server.log 2>&1 &
SERVER_PID=$!

# 서버 시작 확인
sleep 3
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ 서버가 성공적으로 시작되었습니다! (PID: $SERVER_PID)"
    echo "📊 대시보드: https://${CODESPACE_NAME}-8080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/dashboard"
    echo "🔍 헬스체크: https://${CODESPACE_NAME}-8080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/health"
else
    echo "❌ 서버 시작에 실패했습니다."
    echo "로그 확인:"
    tail -20 server.log
    exit 1
fi

echo "📝 서버 로그를 확인하려면: tail -f server.log"
echo "🔄 서버를 재시작하려면: ./start_codespace_server.sh"
