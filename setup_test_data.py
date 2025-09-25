#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
테스트 데이터 설정 스크립트
"""

import sqlite3
import hashlib
import hmac
from datetime import datetime

def setup_test_data():
    # 데이터베이스 연결
    conn = sqlite3.connect('reminder.db')
    cursor = conn.cursor()
    
    # 스키마 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT NOT NULL,
      assignee_email TEXT,
      frequency TEXT CHECK(frequency IN ('daily','weekly','monthly','quarterly')) NOT NULL,
      due_date TEXT,
      status TEXT CHECK(status IN ('pending','done')) DEFAULT 'pending',
      hmac_token TEXT UNIQUE,
      last_completed_at TEXT,
      updated_at TEXT,
      assignee TEXT
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
      email TEXT PRIMARY KEY,
      name TEXT
    );
    ''')
    
    # 기존 데이터 삭제
    cursor.execute('DELETE FROM tasks')
    cursor.execute('DELETE FROM users')
    
    # 사용자 추가
    cursor.execute("INSERT INTO users (email, name) VALUES (?, ?)", ('dadae5th@gmail.com', '관리자'))
    
    # 시크릿 키 (config.yaml의 secret 사용)
    secret_key = 'gBckLh5s3CSP5VIu6TPi0f1aic6tofQ9EFgrcwf24W1Zl4B2'
    
    # 테스트 업무들 추가
    tasks = [
        ('프로젝트 A 완료 보고서 작성', 'dadae5th@gmail.com', 'daily'),
        ('주간 회의 자료 준비', 'dadae5th@gmail.com', 'weekly'),
        ('코드 리뷰 완료', 'dadae5th@gmail.com', 'daily'),
        ('월간 성과 보고서 작성', 'dadae5th@gmail.com', 'monthly')
    ]
    
    for title, email, frequency in tasks:
        # HMAC 토큰 생성
        token_data = f'{title}:{email}:{frequency}'
        hmac_token = hmac.new(secret_key.encode(), token_data.encode(), hashlib.sha256).hexdigest()
        
        cursor.execute('''
            INSERT INTO tasks (title, assignee_email, frequency, status, hmac_token, updated_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
        ''', (title, email, frequency, hmac_token, datetime.now().isoformat()))
    
    conn.commit()
    print(f'테스트 데이터 {len(tasks)}개 추가 완료')
    
    # 데이터 확인
    cursor.execute('SELECT id, title, assignee_email, frequency, status, hmac_token FROM tasks')
    rows = cursor.fetchall()
    for row in rows:
        print(f'ID: {row[0]}, 제목: {row[1][:20]}..., 주기: {row[3]}, 토큰: {row[5][:20]}...')
    
    conn.close()
    return True

if __name__ == "__main__":
    try:
        setup_test_data()
        print("✅ 테스트 데이터 설정 완료!")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
