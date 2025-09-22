#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 전체 시스템 상태 점검
import sqlite3
import os
import sys

print("=" * 60)
print("🔍 전체 시스템 상태 점검")
print("=" * 60)

# 1. 파일 존재 확인
print("\n1. 핵심 파일 존재 확인:")
files_to_check = [
    "config.yaml",
    "reminder.db", 
    "db.py",
    "digest.py",
    "mailer.py",
    "webhook.py"
]

for file in files_to_check:
    exists = "✅" if os.path.exists(file) else "❌"
    print(f"   {exists} {file}")

# 2. 데이터베이스 연결 테스트
print("\n2. 데이터베이스 연결 테스트:")
try:
    conn = sqlite3.connect('reminder.db')
    cursor = conn.cursor()
    print("   ✅ 데이터베이스 연결 성공")
    
    # 테이블 구조 확인
    print("\n3. 테이블 구조 확인:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"   테이블 개수: {len(tables)}")
    for table in tables:
        print(f"   - {table[0]}")
    
    # Users 테이블 데이터
    print("\n4. Users 테이블 데이터:")
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    print(f"   사용자 수: {len(users)}")
    for user in users:
        print(f"   - {user}")
    
    # Tasks 테이블 데이터  
    print("\n5. Tasks 테이블 데이터:")
    cursor.execute("SELECT id, title, assignee_email, frequency, status FROM tasks LIMIT 10")
    tasks = cursor.fetchall()
    print(f"   업무 수: {len(tasks)}")
    for task in tasks:
        print(f"   - ID:{task[0]} {task[1]} ({task[2]}) [{task[3]}] {task[4]}")
    
    # 특정 이메일의 업무 확인
    print("\n6. bae.jae.kwon@drbworld.com 업무 확인:")
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE assignee_email = ?", ("bae.jae.kwon@drbworld.com",))
    count = cursor.fetchone()[0]
    print(f"   해당 이메일 업무 수: {count}")
    
    if count > 0:
        cursor.execute("SELECT title, frequency, status, hmac_token FROM tasks WHERE assignee_email = ? LIMIT 5", 
                      ("bae.jae.kwon@drbworld.com",))
        user_tasks = cursor.fetchall()
        for task in user_tasks:
            print(f"   - {task[0]} [{task[1]}] {task[2]} (토큰: {task[3][:20]}...)")
    
    conn.close()
    
except Exception as e:
    print(f"   ❌ 데이터베이스 오류: {e}")

# 3. Config.yaml 확인
print("\n7. Config.yaml 확인:")
try:
    import yaml
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    print(f"   Base URL: {config.get('base_url', 'MISSING')}")
    print(f"   Dashboard URL: {config.get('dashboard_url', 'MISSING')}")
    
    smtp = config.get('smtp', {})
    print(f"   SMTP Host: {smtp.get('host', 'MISSING')}")
    print(f"   SMTP User: {smtp.get('user', 'MISSING')}")
    print(f"   SMTP Pass: {'*' * len(smtp.get('pass', '')) if smtp.get('pass') else 'MISSING'}")
    
except Exception as e:
    print(f"   ❌ Config 로드 오류: {e}")

print("\n" + "=" * 60)
print("점검 완료")
print("=" * 60)
