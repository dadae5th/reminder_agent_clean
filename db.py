# db.py
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DB_PATH = "reminder.db"
KST = ZoneInfo("Asia/Seoul")

@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def kst_now() -> datetime:
    return datetime.now(KST)

def cycle_start(frequency: str, now: datetime) -> datetime:
    d0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if frequency == "daily":
        return d0
    elif frequency == "weekly":
        return d0 - timedelta(days=d0.weekday())
    elif frequency == "monthly":
        return d0.replace(day=1)
    return d0

def active_tasks_for_today(email: str):
    now = kst_now()
    cs_daily   = cycle_start("daily",   now).isoformat()
    cs_weekly  = cycle_start("weekly",  now).isoformat()
    cs_monthly = cycle_start("monthly", now).isoformat()

    q = """
    SELECT *
    FROM tasks
    WHERE assignee_email = ?
      AND (
        (frequency='daily'   AND (last_completed_at IS NULL OR last_completed_at < ?))
        OR
        (frequency='weekly'  AND (last_completed_at IS NULL OR last_completed_at < ?))
        OR
        (frequency='monthly' AND (last_completed_at IS NULL OR last_completed_at < ?))
      )
    ORDER BY frequency, id
    """
    with get_conn() as conn:
        return conn.execute(q, (email, cs_daily, cs_weekly, cs_monthly)).fetchall()

def mark_done_by_token(token: str) -> bool:
    now_iso = kst_now().isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE tasks SET status='done', last_completed_at=?, updated_at=? WHERE hmac_token=?",
            (now_iso, now_iso, token)
        )
        return cur.rowcount == 1

def all_recipients():
    with get_conn() as conn:
        return [r["email"] for r in conn.execute("SELECT email FROM users")]

def init_schema():
    with open("schema.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    with get_conn() as conn:
        for stmt in sql.split(";"):
            s = stmt.strip()
            if s:
                conn.execute(s + ";")
