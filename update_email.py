import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect("reminder.db")
cursor = conn.cursor()

# 이메일이 없는 업무에 기본 이메일 추가
update_query = """
UPDATE tasks
SET assignee_email = ?
WHERE assignee_email IS NULL OR assignee_email = '';
"""
default_email = "bae.jae.kwon@drbworld.com"

cursor.execute(update_query, (default_email,))
conn.commit()

# 업데이트된 행 수 확인
print(f"{cursor.rowcount}개의 업무에 기본 이메일이 추가되었습니다.")

# 연결 종료
conn.close()
