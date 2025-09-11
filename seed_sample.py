# seed_sample.py
import argparse
from db import get_conn, init_schema

USERS = [
    ("bae.jae.kwon@drbworld.com", "배재권"),
    ("sample.user@example.com", "샘플")
]

TASKS = [
    ("코드 디핑기 열처리 챔버 청소", "bae.jae.kwon@drbworld.com", "weekly"),
    ("RTO Pre filter 청소", "bae.jae.kwon@drbworld.com", "monthly"),
    ("설비 가동 중 손 접금 금지(교육)", "sample.user@example.com", "daily"),
]

def insert_users():
    with get_conn() as conn:
        for email, name in USERS:
            conn.execute("INSERT OR IGNORE INTO users(email, name) VALUES(?,?)", (email, name))

def insert_tasks():
    with get_conn() as conn:
        for title, email, freq in TASKS:
            conn.execute(
                """INSERT INTO tasks(title, assignee_email, frequency, status)
                   VALUES (?,?,?, 'pending')""",
                (title, email, freq)
            )

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true", help="스키마 초기화(schema.sql 실행)")
    ap.add_argument("--sample", action="store_true", help="샘플 데이터 삽입")
    args = ap.parse_args()

    if args.init:
        init_schema()
        print("Schema created.")

    if args.sample:
        insert_users()
        insert_tasks()
        print("Sample data inserted.")
