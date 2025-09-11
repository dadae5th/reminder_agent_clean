import sqlite3

def check_database():
    conn = sqlite3.connect("reminder.db")
    cursor = conn.cursor()
    
    # 테이블 구조 확인
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tasks'")
    print("=== 테이블 구조 ===")
    print(cursor.fetchone()[0])
    print()
    
    # 담당자 목록 확인
    print("=== 고유한 담당자 목록 ===")
    cursor.execute("SELECT DISTINCT assignee FROM tasks ORDER BY assignee")
    assignees = cursor.fetchall()
    for assignee in assignees:
        print(f"담당자: {assignee[0]}")
    print()
    
    # 담당자별 업무 수 확인
    print("=== 담당자별 업무 수 ===")
    cursor.execute("""
        SELECT assignee, 
               COUNT(*) as total,
               SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
               SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM tasks 
        GROUP BY assignee
        ORDER BY assignee
    """)
    stats = cursor.fetchall()
    for stat in stats:
        print(f"담당자: {stat[0]}, 전체: {stat[1]}, 진행 중: {stat[2]}, 완료: {stat[3]}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
