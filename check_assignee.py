import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect("reminder.db")
cursor = conn.cursor()

# assignee 컬럼이 비어 있는 데이터 확인
query = "SELECT title, assignee FROM tasks WHERE assignee IS NULL OR assignee = '';"

cursor.execute(query)
results = cursor.fetchall()

if results:
    print("다음 업무의 담당자가 비어 있습니다:")
    for row in results:
        print(f"업무: {row[0]}, 담당자: {row[1]}")
else:
    print("모든 업무에 담당자가 지정되어 있습니다.")

# assignee 컬럼 데이터 확인
query = "SELECT title, assignee FROM tasks;"

cursor.execute(query)
results = cursor.fetchall()

if results:
    print("tasks 테이블의 assignee 데이터:")
    for row in results:
        print(f"업무: {row[0]}, 담당자: {row[1]}")
else:
    print("tasks 테이블에 데이터가 없습니다.")

# assignee 컬럼의 고유 값 확인
query = "SELECT DISTINCT assignee FROM tasks;"

cursor.execute(query)
results = cursor.fetchall()

if results:
    print("tasks 테이블의 고유한 assignee 값:")
    for row in results:
        print(f"담당자: {row[0]}")
else:
    print("tasks 테이블에 assignee 데이터가 없습니다.")

# 연결 종료
conn.close()
