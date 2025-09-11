# import_from_excel.py
import argparse
import pandas as pd
from db import get_conn, init_schema
from datetime import datetime

USER_SHEET_CANDIDATES = ["Users", "users", "담당자", "수신자"]
TASK_SHEET_CANDIDATES = ["Tasks", "tasks", "할일", "업무", "체크리스트"]

USER_COLS = {
    "email": ["email", "이메일", "메일", "주소", "email_address"],
    "name":  ["name", "이름", "담당자", "성명"],
}

TASK_COLS = {
    "title": ["title", "업무", "업무명", "할일", "task", "내용"],
    "assignee": ["담당자"],  # '담당자' 열을 정확히 매핑
    "assignee_email": ["담당자 이메일"],
    "frequency": ["frequency", "주기", "cycle"],
    "due_date": ["due_date", "마감일", "기한", "due", "deadline"],
    "start_date": ["start_date", "시작일", "시작일자", "시작일자"],
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

def calculate_due_date(frequency):
    now = datetime.now()
    if frequency == "daily":
        return now + pd.Timedelta(days=1)
    elif frequency == "weekly":
        return now + pd.Timedelta(weeks=1)
    elif frequency == "monthly":
        return now + pd.DateOffset(months=1)
    return None

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
    t_col = df.columns[3]  # 4번째 열: 업무명
    a_col = df.columns[6]  # 7번째 열: 담당자
    ae_col = find_col(df, TASK_COLS["assignee_email"])
    f_col = find_col(df, TASK_COLS["frequency"])

    missing = [k for k,v in [("title",t_col),("assignee",a_col),("frequency",f_col)] if not v]
    if missing:
        print(f"[tasks] 필수 컬럼 누락: {missing}"); return 0

    cnt = 0
    with get_conn() as conn:
        for _, row in df.iterrows():
            title = str(row.get(t_col)).strip() if pd.notna(row.get(t_col)) else None
            assignee = str(row.get(a_col)).strip() if pd.notna(row.get(a_col)) else None  # 7번째 열 값 가져오기
            assignee_email = str(row.get(ae_col)).strip() if pd.notna(row.get(ae_col)) else None
            freq  = normalize_freq(row.get(f_col))
            if not title or freq not in ("daily","weekly","monthly"): continue

            due_date = calculate_due_date(freq).strftime("%Y-%m-%d")

            conn.execute(
                """INSERT INTO tasks(title, assignee, assignee_email, frequency, status, due_date)
                   VALUES (?,?,?,?, 'pending', ?)
                   ON CONFLICT(title, frequency) DO UPDATE SET due_date=excluded.due_date, assignee=excluded.assignee, assignee_email=excluded.assignee_email""",
                (title, assignee, assignee_email, freq, due_date)
            )
            cnt += 1
    print(f"[tasks] 업데이트 또는 삽입: {cnt}건")
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
