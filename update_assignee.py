import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect("reminder.db")
cursor = conn.cursor()

# assignee 컬럼이 비어 있는 데이터에 기본 값 추가
update_query = """
UPDATE tasks
SET assignee = ?
WHERE assignee IS NULL OR assignee = '';
"""
default_assignee = "생산팀"

cursor.execute(update_query, (default_assignee,))
conn.commit()

# 업데이트된 행 수 확인
print(f"{cursor.rowcount}개의 업무에 기본 담당자가 추가되었습니다.")

# 연결 종료
conn.close()
