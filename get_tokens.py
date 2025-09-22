#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 현재 데이터베이스의 실제 토큰 확인
import sqlite3

conn = sqlite3.connect('reminder.db')
cursor = conn.cursor()

print("=== 현재 데이터베이스의 토큰들 ===")
try:
    cursor.execute("SELECT id, title, hmac_token, status FROM tasks LIMIT 10")
    tasks = cursor.fetchall()
    
    if tasks:
        print(f"총 {len(tasks)}개 업무 발견:")
        for i, (task_id, title, token, status) in enumerate(tasks, 1):
            print(f"{i}. ID: {task_id}")
            print(f"   제목: {title}")
            print(f"   토큰: {token}")
            print(f"   상태: {status}")
            print(f"   완료 URL: http://localhost:8000/complete?token={token}")
            print("---")
    else:
        print("업무가 없습니다.")
        
except Exception as e:
    print(f"오류: {e}")
    
    # 테이블 구조 확인
    print("\n=== 테이블 구조 확인 ===")
    cursor.execute("PRAGMA table_info(tasks)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"컬럼: {col[1]} (타입: {col[2]})")

conn.close()
