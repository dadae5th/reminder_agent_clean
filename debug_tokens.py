import sqlite3
import sys
sys.path.append('.')

from mailer import make_token

# 데이터베이스 연결
conn = sqlite3.connect('reminder.db')
conn.row_factory = sqlite3.Row

print("=" * 50)
print("📋 현재 PENDING 상태 업무들과 토큰 비교")
print("=" * 50)

pending_tasks = conn.execute(
    "SELECT id, title, hmac_token, status FROM tasks WHERE status = 'pending'"
).fetchall()

print(f"🔍 총 {len(pending_tasks)}개의 pending 업무 발견:")
for task in pending_tasks:
    # 이메일에서 생성되는 토큰
    email_token = make_token(task['id'])
    # 데이터베이스의 토큰
    db_token = task['hmac_token']
    
    match_status = "✅ 일치" if email_token == db_token else "❌ 불일치"
    
    print(f"\n📋 업무 ID: {task['id']}")
    print(f"   제목: {task['title'][:40]}...")
    print(f"   DB 토큰:    {db_token[:15]}...")
    print(f"   이메일 토큰: {email_token[:15]}...")
    print(f"   상태: {match_status}")

print("\n" + "=" * 50)
print("🔧 토큰 매칭 테스트 완료")
print("=" * 50)

conn.close()
