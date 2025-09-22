#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 테스트 데이터 추가 및 이메일 발송
"""

import sqlite3
import hashlib
import hmac
from datetime import datetime, timedelta
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import db
    from mailer import send_digest_email
    
    print("모듈 import 성공")
    
    # 데이터베이스 초기화
    db.init_db()
    print("데이터베이스 초기화 완료")
    
    conn = sqlite3.connect('reminder.db')
    cursor = conn.cursor()
    
    # 기존 데이터 정리
    cursor.execute("DELETE FROM tasks")
    cursor.execute("DELETE FROM users")
    print("기존 데이터 정리 완료")
    
    # 테스트 사용자 추가
    test_email = "bae.jae.kwon@seegene.com"
    cursor.execute("""
        INSERT OR REPLACE INTO users (name, email, hmac_token) 
        VALUES (?, ?, ?)
    """, ("배재권", test_email, "test_token_123"))
    print("테스트 사용자 추가 완료")
    
    # 테스트 업무들 추가
    tomorrow = datetime.now() + timedelta(days=1)
    tasks = [
        ("프로젝트 A 완료 보고서 작성", tomorrow.strftime('%Y-%m-%d'), "배재권", test_email, "pending"),
        ("주간 회의 자료 준비", tomorrow.strftime('%Y-%m-%d'), "배재권", test_email, "pending"),
        ("코드 리뷰 완료", tomorrow.strftime('%Y-%m-%d'), "배재권", test_email, "pending")
    ]
    
    secret_key = "your_secret_key_here"
    
    for task_name, due_date, assignee, email, status in tasks:
        # HMAC 토큰 생성
        token_data = f"{task_name}:{due_date}:{assignee}:{email}"
        hmac_token = hmac.new(secret_key.encode(), token_data.encode(), hashlib.sha256).hexdigest()
        
        cursor.execute("""
            INSERT INTO tasks (task_name, due_date, assignee, email, status, hmac_token) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task_name, due_date, assignee, email, status, hmac_token))
    
    conn.commit()
    conn.close()
    print(f"테스트 업무 {len(tasks)}개 추가 완료")
    
    # 이메일 발송
    print("이메일 발송 시작...")
    result = send_digest_email()
    
    if result:
        print("✅ 이메일 발송 성공!")
        print("\n📧 이제 이메일을 확인하고 다음을 테스트하세요:")
        print("1. 이메일에서 완료할 업무들을 체크")
        print("2. '선택한 업무 모두 완료하기' 버튼 클릭")
        print("3. 대시보드로 리디렉션 확인")
        print("4. http://localhost:8000/dashboard 에서 실시간 반영 확인")
    else:
        print("❌ 이메일 발송 실패")

except Exception as e:
    print(f"오류 발생: {e}")
    import traceback
    traceback.print_exc()
