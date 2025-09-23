# import_from_excel.py - 엑셀 파일에서 데이터 가져오기
import pandas as pd
import sqlite3
import os
import glob
from contextlib import contextmanager
from mailer import make_token

@contextmanager
def get_conn():
    conn = sqlite3.connect("reminder.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def find_excel_files():
    """현재 폴더에서 엑셀 파일 찾기"""
    excel_files = []
    
    # .xlsx와 .xls 파일 찾기
    for pattern in ['*.xlsx', '*.xls']:
        excel_files.extend(glob.glob(pattern))
    
    return excel_files

def select_excel_file():
    """엑셀 파일 선택"""
    excel_files = find_excel_files()
    
    if not excel_files:
        print("❌ 현재 폴더에 엑셀 파일이 없습니다.")
        return None
    
    print("📂 발견된 엑셀 파일:")
    for i, file in enumerate(excel_files, 1):
        print(f"   {i}. {file}")
    
    if len(excel_files) == 1:
        print(f"\n✅ 자동 선택: {excel_files[0]}")
        return excel_files[0]
    
    try:
        choice = int(input(f"\n파일을 선택하세요 (1-{len(excel_files)}): ")) - 1
        if 0 <= choice < len(excel_files):
            return excel_files[choice]
        else:
            print("❌ 잘못된 선택입니다.")
            return None
    except ValueError:
        print("❌ 숫자를 입력해주세요.")
        return None

def analyze_excel_structure(file_path):
    """엑셀 파일 구조 분석"""
    try:
        # 첫 번째 시트 읽기
        df = pd.read_excel(file_path)
        print(f"📊 엑셀 파일 분석: {file_path}")
        print(f"   - 총 행 수: {len(df)}")
        print(f"   - 컬럼 수: {len(df.columns)}")
        print(f"   - 컬럼명: {list(df.columns)}")
        print("\n📋 첫 5행 샘플:")
        print(df.head())
        return df
    except Exception as e:
        print(f"❌ 엑셀 파일 읽기 오류: {e}")
        return None

def import_tasks_from_excel(file_path, title_col="제목", assignee_col="담당자", frequency_col="주기", email_col="이메일"):
    """엑셀 파일에서 업무 데이터를 가져와 데이터베이스에 저장"""
    
    df = analyze_excel_structure(file_path)
    if df is None:
        return False
    
    # 컬럼명 매핑 확인
    print(f"\n🔍 컬럼 매핑:")
    print(f"   - 제목: {title_col}")
    print(f"   - 담당자: {assignee_col}")
    print(f"   - 주기: {frequency_col}")
    print(f"   - 이메일: {email_col}")
    
    # 필수 컬럼 확인
    required_cols = [title_col, assignee_col, frequency_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"❌ 필수 컬럼이 없습니다: {missing_cols}")
        print(f"사용 가능한 컬럼: {list(df.columns)}")
        return False
    
    # 기존 데이터 확인
    with get_conn() as conn:
        backup_count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        print(f"\n💾 기존 업무 수: {backup_count}개")
        
        if backup_count > 0:
            print("⚠️ 기존 데이터가 있습니다. 기존 데이터를 유지하고 새 데이터를 추가합니다.")
        else:
            print("✅ 새로운 데이터를 추가합니다.")
    
    # 사용자 정보 수집
    unique_assignees = df[assignee_col].dropna().unique()
    print(f"\n👥 담당자 목록: {list(unique_assignees)}")
    
    # 사용자 등록
    with get_conn() as conn:
        for assignee in unique_assignees:
            if pd.isna(assignee):
                continue
            
            # 이메일 찾기
            assignee_email = None
            if email_col in df.columns:
                email_row = df[df[assignee_col] == assignee][email_col].iloc[0]
                if not pd.isna(email_row):
                    assignee_email = email_row
            
            if not assignee_email:
                assignee_email = f"{assignee.lower().replace(' ', '.')}@company.com"
            
            conn.execute("INSERT OR IGNORE INTO users (email, name) VALUES (?, ?)", 
                        (assignee_email, assignee))
            print(f"   📧 {assignee} → {assignee_email}")
    
    # 업무 데이터 가져오기
    imported_count = 0
    with get_conn() as conn:
        for idx, row in df.iterrows():
            title = row[title_col]
            assignee = row[assignee_col]
            frequency = row[frequency_col]
            
            # 빈 데이터 스킵
            if pd.isna(title) or pd.isna(assignee) or pd.isna(frequency):
                continue
            
            # 주기 정규화
            frequency = str(frequency).lower()
            if 'daily' in frequency or '일' in frequency:
                frequency = 'daily'
            elif 'weekly' in frequency or '주' in frequency:
                frequency = 'weekly'
            elif 'monthly' in frequency or '월' in frequency:
                frequency = 'monthly'
            else:
                frequency = 'daily'  # 기본값
            
            # 담당자 이메일 찾기
            if email_col in df.columns and not pd.isna(row[email_col]):
                assignee_email = row[email_col]
            else:
                # users 테이블에서 찾기
                user = conn.execute("SELECT email FROM users WHERE name = ?", (assignee,)).fetchone()
                assignee_email = user[0] if user else f"{assignee.lower().replace(' ', '.')}@company.com"
            
            # 업무 추가 (중복 체크)
            existing = conn.execute("""
                SELECT id FROM tasks WHERE title = ? AND assignee_email = ?
            """, (title, assignee_email)).fetchone()
            
            if existing:
                print(f"   ⚠️ 중복 업무 스킵: {title}")
                continue
            
            conn.execute("""
                INSERT INTO tasks (title, assignee_email, frequency, status, assignee)
                VALUES (?, ?, ?, 'pending', ?)
            """, (title, assignee_email, frequency, assignee))
            
            imported_count += 1
    
    # 토큰 생성
    with get_conn() as conn:
        tasks = conn.execute("SELECT id FROM tasks WHERE hmac_token IS NULL").fetchall()
        for task in tasks:
            token = make_token(task[0])
            conn.execute("UPDATE tasks SET hmac_token = ? WHERE id = ?", (token, task[0]))
    
    print(f"\n✅ 데이터 가져오기 완료!")
    print(f"   - 가져온 업무 수: {imported_count}개")
    print(f"   - 등록된 사용자 수: {len(unique_assignees)}개")
    
    return True

if __name__ == "__main__":
    print("🚀 엑셀 업무 데이터 가져오기")
    print("=" * 30)
    
    # 자동으로 엑셀 파일 찾기
    file_path = select_excel_file()
    
    if file_path:
        print(f"\n📂 선택된 파일: {file_path}")
        success = import_tasks_from_excel(file_path)
        
        if success:
            print("\n🎉 업무 데이터 가져오기가 완료되었습니다!")
            print("   - 웹 대시보드에서 확인하세요: http://localhost:8003/dashboard")
        else:
            print("\n❌ 데이터 가져오기에 실패했습니다.")
    else:
        print("\n💡 직접 파일 경로를 입력하시겠습니까?")
        manual_path = input("엑셀 파일 경로 (Enter로 취소): ").strip()
        if manual_path:
            import_tasks_from_excel(manual_path)
