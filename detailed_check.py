#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 시스템 점검 결과를 파일로 저장
import sqlite3
import os
import sys
import yaml
from datetime import datetime

def check_system():
    results = []
    results.append("=" * 60)
    results.append("🔍 전체 시스템 상태 점검")
    results.append(f"점검 시간: {datetime.now()}")
    results.append("=" * 60)
    
    # 1. 파일 존재 확인
    results.append("\n1. 핵심 파일 존재 확인:")
    files_to_check = [
        "config.yaml", "reminder.db", "db.py", "digest.py", "mailer.py", "webhook.py"
    ]
    
    for file in files_to_check:
        exists = "✅" if os.path.exists(file) else "❌"
        results.append(f"   {exists} {file}")
    
    # 2. 데이터베이스 점검
    results.append("\n2. 데이터베이스 점검:")
    try:
        conn = sqlite3.connect('reminder.db')
        cursor = conn.cursor()
        results.append("   ✅ 데이터베이스 연결 성공")
        
        # 테이블 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        results.append(f"   테이블: {[t[0] for t in tables]}")
        
        # Users 데이터
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        results.append(f"\n3. Users 테이블 ({len(users)}명):")
        for user in users:
            results.append(f"   - {user}")
        
        # Tasks 데이터
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cursor.fetchone()[0]
        results.append(f"\n4. Tasks 테이블 (총 {total_tasks}개):")
        
        cursor.execute("SELECT id, title, assignee_email, frequency, status FROM tasks LIMIT 5")
        tasks = cursor.fetchall()
        for task in tasks:
            results.append(f"   - ID:{task[0]} {task[1]} ({task[2]}) [{task[3]}] {task[4]}")
        
        # 특정 이메일 업무
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE assignee_email = ?", 
                      ("bae.jae.kwon@drbworld.com",))
        target_count = cursor.fetchone()[0]
        results.append(f"\n5. bae.jae.kwon@drbworld.com 업무: {target_count}개")
        
        if target_count > 0:
            cursor.execute("SELECT title, status FROM tasks WHERE assignee_email = ?", 
                          ("bae.jae.kwon@drbworld.com",))
            target_tasks = cursor.fetchall()
            for task in target_tasks:
                results.append(f"   - {task[0]} [{task[1]}]")
        
        conn.close()
        
    except Exception as e:
        results.append(f"   ❌ 데이터베이스 오류: {e}")
    
    # 3. Config 확인
    results.append("\n6. Config.yaml 확인:")
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        results.append(f"   Base URL: {config.get('base_url')}")
        results.append(f"   Dashboard URL: {config.get('dashboard_url')}")
        
        smtp = config.get('smtp', {})
        results.append(f"   SMTP Host: {smtp.get('host')}")
        results.append(f"   SMTP User: {smtp.get('user')}")
        results.append(f"   SMTP Pass: {'설정됨' if smtp.get('pass') else '누락'}")
        
    except Exception as e:
        results.append(f"   ❌ Config 오류: {e}")
    
    # 4. 모듈 import 테스트
    results.append("\n7. 모듈 Import 테스트:")
    try:
        import db
        results.append("   ✅ db 모듈")
        
        import digest
        results.append("   ✅ digest 모듈")
        
        import mailer
        results.append("   ✅ mailer 모듈")
        
        # DB 함수 테스트
        recipients = db.all_recipients()
        results.append(f"   수신자 목록: {recipients}")
        
        if recipients:
            first_recipient = recipients[0]
            tasks = db.active_tasks_for_today(first_recipient)
            results.append(f"   {first_recipient}의 오늘 업무: {len(tasks)}개")
        
    except Exception as e:
        results.append(f"   ❌ 모듈 오류: {e}")
        import traceback
        results.append(f"   상세: {traceback.format_exc()}")
    
    return "\n".join(results)

# 점검 실행 및 결과 저장
if __name__ == "__main__":
    try:
        result = check_system()
        with open("system_check_result.txt", "w", encoding="utf-8") as f:
            f.write(result)
        print("✅ 시스템 점검 완료 - system_check_result.txt 파일 확인")
    except Exception as e:
        print(f"❌ 점검 실패: {e}")
        import traceback
        traceback.print_exc()
