# add_task.py - 새로운 업무 추가용 스크립트
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_conn():
    conn = sqlite3.connect("reminder.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def add_user(email, name):
    """새 사용자 추가"""
    with get_conn() as conn:
        conn.execute("INSERT OR IGNORE INTO users (email, name) VALUES (?, ?)", (email, name))
        print(f"사용자 추가됨: {name} ({email})")

def add_task(title, assignee_email, frequency, creator_name):
    """새 업무 추가"""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO tasks (title, assignee_email, frequency, status, creator_name)
            VALUES (?, ?, ?, 'pending', ?)
        """, (title, assignee_email, frequency, creator_name))
        print(f"업무 추가됨: {title} ({frequency})")

if __name__ == "__main__":
    # 사용 예시
    print("=== 사용자 추가 ===")
    # add_user("new@example.com", "새사용자")
    
    print("=== 업무 추가 ===")
    # add_task("새로운 업무", "bae.jae.kwon@drbworld.com", "daily", "배재권")
    
    print("직접 편집해서 사용하세요!")
