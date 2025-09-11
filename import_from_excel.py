# import_from_excel.py
import argparse
import pandas as pd
from db import get_conn, init_schema

USER_SHEET_CANDIDATES = ["Users", "users", "담당자", "수신자"]
TASK_SHEET_CANDIDATES = ["Tasks", "tasks", "할일", "업무", "체크리스트"]

USER_COLS = {
    "email": ["email", "이메일", "메일", "주소", "email_address"],
    "name":  ["name", "이름", "담당자", "성명"],
}

TASK_COLS = {
    "title": ["title", "업무", "업무명", "할일", "task", "내용"],
    "assignee_email": ["assignee_email", "담당자이메일", "이메일", "메일", "email"],
    "frequency": ["frequency", "주기", "cycle"],
    "due_date": ["due_date", "마감일", "기한", "due", "deadline"],
}

FREQ_MAP = {
    "daily": "daily", "일간": "daily", "매일": "daily",
    "weekly": "weekly", "주간": "weekly", "매주": "weekly",
    "monthly": "monthly", "월간": "monthly", "매월": "monthly",
}

def find_sheet(xl: pd.ExcelFile, candidates):
    for name in candidates:
        if name in xl.sheet_names:
            return name
    return xl.sheet_names[0]

def find_col(df: pd.DataFrame, candidates):
    low = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        k = cand.lower()
        if k in low: return low[k]
    for c in df.columns:
        if not isinstance(c, str): continue
        if c.strip().lower() in [x.lower() for x in candidates]: return c
    return None

def normalize_email(x):
    if pd.isna(x): return None
    return str(x).strip().lower()

def normalize_freq(x):
    if pd.isna(x): return None
    return FREQ_MAP.get(str(x).strip().lower())

def import_users(df):
    e_col = find_col(df, USER_COLS["email"])
    n_col = find_col(df, USER_COLS["name"])
    if not e_col: 
        print("[users] 이메일 컬럼 없음 -> 건너뜀."); return 0
    cnt = 0
    with get_conn() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, name TEXT)")
        for _, row in df.iterrows():
            email = normalize_email(row.get(e_col))
            if not email: continue
            name = str(row.get(n_col)).strip() if n_col else ""
            conn.execute("INSERT OR IGNORE INTO users(email,name) VALUES(?,?)", (email, name))
            cnt += 1
    print(f"[users] 입력: {cnt}건(중복 제외)")
    return cnt

def import_tasks(df):
    t_col = find_col(df, TASK_COLS["title"])
    a_col = find_col(df, TASK_COLS["assignee_email"])
    f_col = find_col(df, TASK_COLS["frequency"])
    d_col = find_col(df, TASK_COLS["due_date"])

    missing = [k for k,v in [("title",t_col),("assignee_email",a_col),("frequency",f_col)] if not v]
    if missing:
        print(f"[tasks] 필수 컬럼 누락: {missing}"); return 0

    cnt = 0
    with get_conn() as conn:
        for _, row in df.iterrows():
            title = str(row.get(t_col)).strip() if pd.notna(row.get(t_col)) else None
            email = normalize_email(row.get(a_col))
            freq  = normalize_freq(row.get(f_col))
            if not title or not email or freq not in ("daily","weekly","monthly"): continue

            due_str = None
            if d_col and pd.notna(row.get(d_col)):
                try:
                    due_str = pd.to_datetime(row.get(d_col)).strftime("%Y-%m-%d")
                except Exception:
                    due_str = str(row.get(d_col))

            exists = conn.execute(
                "SELECT id FROM tasks WHERE title=? AND assignee_email=? AND frequency=?",
                (title, email, freq)
            ).fetchone()
            if exists: continue

            conn.execute(
                """INSERT INTO tasks(title, assignee_email, frequency, status, due_date)
                   VALUES (?,?,?, 'pending', ?)""",
                (title, email, freq, due_str)
            )
            cnt += 1
    print(f"[tasks] 입력: {cnt}건(중복 제외)")
    return cnt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True, help="엑셀(.xlsx) 파일 경로")
    ap.add_argument("--users-sheet", default=None)
    ap.add_argument("--tasks-sheet", default=None)
    args = ap.parse_args()

    init_schema()
    xl = pd.ExcelFile(args.file)

    users_sheet = args.users_sheet if args.users_sheet in (xl.sheet_names if args.users_sheet else []) else find_sheet(xl, USER_SHEET_CANDIDATES)
    tasks_sheet = args.tasks_sheet if args.tasks_sheet in (xl.sheet_names if args.tasks_sheet else []) else find_sheet(xl, TASK_SHEET_CANDIDATES)
    print(f"Users sheet: {users_sheet} / Tasks sheet: {tasks_sheet}")

    try:
        df_u = pd.read_excel(xl, users_sheet)
        import_users(df_u)
    except Exception as e:
        print("[users] 로드 실패:", e)

    try:
        df_t = pd.read_excel(xl, tasks_sheet)
        import_tasks(df_t)
    except Exception as e:
        print("[tasks] 로드 실패:", e)

if __name__=="__main__":
    main()
