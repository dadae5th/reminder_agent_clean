FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 종속성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# SQLite 데이터베이스 초기화
RUN python -c "
import sqlite3
import os
from datetime import datetime

# 데이터베이스 초기화
conn = sqlite3.connect('reminder.db')

# 스키마 생성
conn.execute('''
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)''')

conn.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    assignee_email TEXT,
    frequency TEXT CHECK(frequency IN ('daily', 'weekly', 'monthly')),
    status TEXT DEFAULT 'pending',
    assignee TEXT,
    hmac_token TEXT,
    last_completed_at TEXT,
    due_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assignee_email) REFERENCES users (email)
)''')

conn.commit()
conn.close()
print('Database schema created')
"

# 포트 설정
EXPOSE 8080

# 웹서버 시작
CMD ["uvicorn", "webhook:app", "--host", "0.0.0.0", "--port", "8080"]
