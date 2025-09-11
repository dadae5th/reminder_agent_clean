import sqlite3

def check_tasks_data():
    conn = sqlite3.connect("reminder.db")
    cursor = conn.cursor()

    query = "SELECT assignee, assignee_email, COUNT(*) FROM tasks GROUP BY assignee, assignee_email;"
    cursor.execute(query)
    results = cursor.fetchall()

    print("담당자와 이메일별 데이터:")
    for row in results:
        print(f"담당자: {row[0]}, 이메일: {row[1]}, 개수: {row[2]}")

    conn.close()

if __name__ == "__main__":
    check_tasks_data()
