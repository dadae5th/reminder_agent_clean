#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 직접 이메일 발송 테스트 및 문제 진단
import os
import sys
import sqlite3

print("🔍 이메일 발송 문제 진단 시작")

# 1. 데이터베이스에 올바른 데이터 생성
print("1. 데이터베이스 설정...")
try:
    # 스키마 초기화
    with open("schema.sql", "r", encoding="utf-8") as f:
        schema = f.read()
    
    conn = sqlite3.connect('reminder.db')
    cursor = conn.cursor()
    
    # 테이블 생성
    for stmt in schema.split(";"):
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt + ";")
    
    # 기존 데이터 삭제
    cursor.execute("DELETE FROM tasks")
    cursor.execute("DELETE FROM users")
    
    # 사용자 추가
    cursor.execute("INSERT INTO users (email, name) VALUES (?, ?)", 
                   ("bae.jae.kwon@drbworld.com", "배재권"))
    
    # 업무 추가
    import hashlib
    import hmac
    
    secret = "gBckLh5s3CSP5VIu6TPi0f1aic6tofQ9EFgrcwf24W1Zl4B2"
    
    tasks_data = [
        ("프로젝트 A 완료 보고서 작성", "daily"),
        ("주간 회의 자료 준비", "weekly"),
        ("월간 리포트 작성", "monthly")
    ]
    
    for i, (title, freq) in enumerate(tasks_data, 1):
        # HMAC 토큰 생성
        token_input = f"{title}:{freq}:bae.jae.kwon@drbworld.com:{i}"
        token = hmac.new(secret.encode(), token_input.encode(), hashlib.sha256).hexdigest()
        
        cursor.execute("""
            INSERT INTO tasks (title, assignee_email, frequency, status, hmac_token, assignee)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, "bae.jae.kwon@drbworld.com", freq, "pending", token, "배재권"))
    
    conn.commit()
    
    # 데이터 확인
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE assignee_email = ?", 
                   ("bae.jae.kwon@drbworld.com",))
    task_count = cursor.fetchone()[0]
    
    print(f"   ✅ 사용자: {user_count}명, 업무: {task_count}개 생성")
    
    conn.close()
    
except Exception as e:
    print(f"   ❌ 데이터베이스 설정 실패: {e}")

# 2. digest.py 테스트
print("\n2. 이메일 발송 테스트...")
try:
    # db 모듈 import
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import db
    
    # 수신자 확인
    recipients = db.all_recipients()
    print(f"   수신자: {recipients}")
    
    if not recipients:
        print("   ❌ 수신자가 없습니다!")
    else:
        # 각 수신자의 업무 확인
        for recipient in recipients:
            tasks = db.active_tasks_for_today(recipient)
            print(f"   {recipient}의 오늘 업무: {len(tasks)}개")
            
            if tasks:
                for task in tasks:
                    print(f"     - {task['title']} [{task['frequency']}]")
    
    # digest 실행
    from digest import run_daily_digest
    print(f"\n   📧 이메일 발송 시도...")
    
    result = run_daily_digest()
    print(f"   결과: {result}")
    
    print("   ✅ 이메일 발송 완료!")
    
except Exception as e:
    print(f"   ❌ 이메일 발송 실패: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 진단 완료")
print("이메일을 bae.jae.kwon@drbworld.com에서 확인하세요.")
print("스팸 폴더도 확인해보세요!")
