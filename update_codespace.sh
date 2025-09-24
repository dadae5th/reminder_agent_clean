#!/bin/bash
# GitHub Actions에서 Codespaces 서버 업데이트를 위한 스크립트

echo "🔄 GitHub Codespaces 서버 업데이트 시작..."

# 1. 최신 코드 가져오기
echo "📥 최신 코드 가져오기..."
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/dadae5th/reminder_agent_clean/dispatches \
  -d '{"event_type":"update-codespace"}'

echo "✅ Codespace 업데이트 요청 완료"
