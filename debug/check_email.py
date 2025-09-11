import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect("reminder.db")
cursor = conn.cursor()

# 이메일 데이터 확인
query = "SELECT title, assignee_email FROM tasks WHERE assignee_email = ?;"
email_to_check = "bae.jae.kwon@drbworld.com"

cursor.execute(query, (email_to_check,))
results = cursor.fetchall()

if results:
    print("다음 이메일이 데이터베이스에 저장되어 있습니다:")
    for row in results:
        print(f"업무: {row[0]}, 이메일: {row[1]}")
else:
    print("해당 이메일이 데이터베이스에 없습니다.")

# 연결 종료
conn.close()
