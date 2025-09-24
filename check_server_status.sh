#!/bin/bash
# check_server_status.sh - 서버 상태 확인 및 자동 복구

echo "🔍 서버 상태 확인 중..."

# 서버 프로세스 확인
SERVER_PID=$(pgrep -f "python.*webhook.py")
if [ -n "$SERVER_PID" ]; then
    echo "✅ 서버가 실행 중입니다 (PID: $SERVER_PID)"
    
    # 헬스체크 확인
    if [ -n "$CODESPACE_NAME" ]; then
        HEALTH_URL="https://${CODESPACE_NAME}-8080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/health"
        echo "🩺 헬스체크 중: $HEALTH_URL"
        
        if curl -s -f "$HEALTH_URL" > /dev/null; then
            echo "✅ 서버가 정상적으로 응답하고 있습니다"
            echo "📊 대시보드: https://${CODESPACE_NAME}-8080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/dashboard"
        else
            echo "❌ 서버가 응답하지 않습니다. 재시작이 필요할 수 있습니다."
            echo "🔄 서버 재시작: ./start_codespace_server.sh"
        fi
    else
        echo "🏠 로컬 환경에서 실행 중"
        echo "📊 대시보드: http://localhost:8080/dashboard"
    fi
else
    echo "❌ 서버가 실행되지 않고 있습니다"
    echo "🔄 서버 시작하려면: ./start_codespace_server.sh"
    
    # 자동 복구 옵션
    read -p "🤖 자동으로 서버를 시작하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 서버 자동 시작 중..."
        ./start_codespace_server.sh
    fi
fi

# 최근 로그 확인
echo ""
echo "📝 최근 서버 로그 (마지막 10줄):"
if [ -f "server.log" ]; then
    tail -10 server.log
else
    echo "로그 파일을 찾을 수 없습니다."
fi
