import sqlite3

def update_schema():
    conn = sqlite3.connect("reminder.db")
    cursor = conn.cursor()

    # 기존 테이블의 고유 제약 조건 추가
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            assignee_email TEXT,
            frequency TEXT NOT NULL,
            due_date TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            UNIQUE(title, frequency) -- 고유 제약 조건 추가
        )
    """)

    # 중복 제거 후 데이터 복사
    cursor.execute("""
        INSERT INTO tasks_new (id, title, assignee_email, frequency, due_date, status)
        SELECT MIN(id), title, assignee_email, frequency, due_date, status
        FROM tasks
        GROUP BY title, frequency
    """)

    # 기존 테이블 삭제 및 새 테이블 이름 변경
    cursor.execute("DROP TABLE tasks")
    cursor.execute("ALTER TABLE tasks_new RENAME TO tasks")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_schema()
