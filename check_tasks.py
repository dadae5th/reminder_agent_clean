import sqlite3

def check_tasks():
    conn = sqlite3.connect("reminder.db")
    cursor = conn.cursor()

    # 전체 작업 개수 확인
    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_tasks = cursor.fetchone()[0]
    print(f"전체 작업 개수: {total_tasks}")

    # 모든 작업 출력
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    for task in tasks:
        print(task)

    conn.close()

if __name__ == "__main__":
    check_tasks()
