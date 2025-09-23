# complete_task_action.py - GitHub Actions로 업무 완료 처리
import os
import sqlite3
from datetime import datetime
import sys

def complete_task_by_token(token):
    """토큰으로 업무 완료 처리"""
    try:
        # SQLite 연결
        conn = sqlite3.connect('reminder.db')
        conn.row_factory = sqlite3.Row
        
        # 토큰으로 업무 찾기
        task = conn.execute(
            "SELECT * FROM tasks WHERE hmac_token = ? AND status = 'pending'", 
            (token,)
        ).fetchone()
        
        if not task:
            print(f"❌ 토큰에 해당하는 업무를 찾을 수 없습니다: {token}")
            return False
        
        # 업무 완료 처리
        now = datetime.now().isoformat()
        conn.execute(
            "UPDATE tasks SET status = 'done', last_completed_at = ? WHERE id = ?",
            (now, task['id'])
        )
        conn.commit()
        conn.close()
        
        print(f"✅ 업무 완료: {task['title']}")
        return True
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        token = sys.argv[1]
        complete_task_by_token(token)
    else:
        print("❌ 토큰이 필요합니다")
