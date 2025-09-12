#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 올바른 스키마로 테스트 데이터 생성
import sqlite3
import hashlib
import hmac
from datetime import datetime

# 스키마에 맞는 데이터 생성
conn = sqlite3.connect('reminder.db')
cursor = conn.cursor()

# 기존 데이터 삭제
cursor.execute("DELETE FROM tasks")
cursor.execute("DELETE FROM users")

# 사용자 추가
cursor.execute("INSERT OR REPLACE INTO users (email, name) VALUES (?, ?)", 
               ("bae.jae.kwon@seegene.com", "배재권"))

# 테스트 업무 추가 (올바른 스키마 사용)
secret_key = "your_secret_key_here"
tasks = [
    "프로젝트 A 완료 보고서 작성",
    "주간 회의 자료 준비",
    "코드 리뷰 완료",
    "시스템 배포 점검",
    "문서 업데이트"
]

for i, task_title in enumerate(tasks, 1):
    # HMAC 토큰 생성
    token_data = f"{task_title}:daily:bae.jae.kwon@seegene.com:{i}"
    hmac_token = hmac.new(secret_key.encode(), token_data.encode(), hashlib.sha256).hexdigest()
    
    cursor.execute("""
        INSERT INTO tasks (title, assignee_email, frequency, status, hmac_token, assignee) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (task_title, "bae.jae.kwon@seegene.com", "daily", "pending", hmac_token, "배재권"))

conn.commit()

# 결과 확인
cursor.execute("SELECT id, title, hmac_token FROM tasks")
tasks = cursor.fetchall()

print("=== 생성된 테스트 데이터 ===")
for task_id, title, token in tasks:
    print(f"ID: {task_id}")
    print(f"제목: {title}")
    print(f"토큰: {token}")
    print(f"완료 URL: http://localhost:8000/complete?token={token}")
    print("---")

conn.close()
print(f"\n총 {len(tasks)}개 업무 생성 완료!")
