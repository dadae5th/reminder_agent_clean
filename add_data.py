#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, timedelta
import hashlib
import hmac

# 테스트 데이터 추가
conn = sqlite3.connect('reminder.db')
cursor = conn.cursor()

# 테이블 생성 확인
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    hmac_token TEXT
)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL,
    due_date TEXT NOT NULL,
    assignee TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    hmac_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# 기존 데이터 삭제
cursor.execute("DELETE FROM tasks")
cursor.execute("DELETE FROM users")

# 테스트 사용자 추가
test_email = "bae.jae.kwon@seegene.com"
cursor.execute("INSERT INTO users (name, email, hmac_token) VALUES (?, ?, ?)", 
               ("배재권", test_email, "test_token_123"))

# 테스트 업무 추가
tomorrow = datetime.now() + timedelta(days=1)
secret_key = "your_secret_key_here"

tasks = [
    "프로젝트 A 완료 보고서 작성",
    "주간 회의 자료 준비", 
    "코드 리뷰 완료",
    "시스템 배포 점검",
    "문서 업데이트"
]

for task_name in tasks:
    due_date = tomorrow.strftime('%Y-%m-%d')
    assignee = "배재권"
    
    # HMAC 토큰 생성
    token_data = f"{task_name}:{due_date}:{assignee}:{test_email}"
    hmac_token = hmac.new(secret_key.encode(), token_data.encode(), hashlib.sha256).hexdigest()
    
    cursor.execute("""
        INSERT INTO tasks (task_name, due_date, assignee, email, status, hmac_token) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (task_name, due_date, assignee, test_email, "pending", hmac_token))

conn.commit()

# 결과 확인
cursor.execute("SELECT COUNT(*) FROM tasks")
task_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM users") 
user_count = cursor.fetchone()[0]

conn.close()

print(f"데이터 추가 완료: 사용자 {user_count}명, 업무 {task_count}개")
