# task_manager.py - 업무 추가/삭제/관리 도구
import sqlite3
from contextlib import contextmanager
from mailer import make_token
import datetime

@contextmanager
def get_conn():
    conn = sqlite3.connect("reminder.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def show_tasks():
    """현재 업무 목록 표시"""
    with get_conn() as conn:
        tasks = conn.execute("""
            SELECT id, title, assignee, assignee_email, frequency, status, 
                   last_completed_at, due_date
            FROM tasks 
            ORDER BY id
        """).fetchall()
        
        if not tasks:
            print("❌ 등록된 업무가 없습니다.")
            return []
        
        print("\n📋 현재 업무 목록:")
        print("=" * 80)
        print(f"{'ID':<3} {'제목':<20} {'담당자':<10} {'주기':<8} {'상태':<10} {'마지막완료':<12}")
        print("-" * 80)
        
        for task in tasks:
            last_completed = task['last_completed_at']
            if last_completed:
                last_completed = last_completed[:10]  # YYYY-MM-DD만 표시
            else:
                last_completed = "미완료"
            
            print(f"{task['id']:<3} {task['title']:<20} {task['assignee']:<10} "
                  f"{task['frequency']:<8} {task['status']:<10} {last_completed:<12}")
        
        return tasks

def add_task():
    """새 업무 추가"""
    print("\n➕ 새 업무 추가")
    print("=" * 30)
    
    title = input("업무 제목: ").strip()
    if not title:
        print("❌ 업무 제목을 입력해주세요.")
        return False
    
    assignee = input("담당자 이름: ").strip()
    if not assignee:
        print("❌ 담당자를 입력해주세요.")
        return False
    
    print("\n주기 선택:")
    print("1. daily (매일)")
    print("2. weekly (매주)")
    print("3. monthly (매월)")
    
    freq_choice = input("주기 선택 (1-3): ").strip()
    frequency_map = {'1': 'daily', '2': 'weekly', '3': 'monthly'}
    frequency = frequency_map.get(freq_choice, 'daily')
    
    email = input(f"이메일 주소 (Enter시 자동생성): ").strip()
    if not email:
        email = f"{assignee.lower().replace(' ', '.')}@company.com"
    
    # 중복 체크
    with get_conn() as conn:
        existing = conn.execute("""
            SELECT id FROM tasks WHERE title = ? AND assignee_email = ?
        """, (title, email)).fetchone()
        
        if existing:
            print(f"❌ 동일한 업무가 이미 존재합니다. (ID: {existing['id']})")
            return False
        
        # 사용자 등록 (없으면)
        conn.execute("INSERT OR IGNORE INTO users (email, name) VALUES (?, ?)", 
                    (email, assignee))
        
        # 업무 추가
        cursor = conn.execute("""
            INSERT INTO tasks (title, assignee_email, frequency, status, assignee)
            VALUES (?, ?, ?, 'pending', ?)
        """, (title, email, frequency, assignee))
        
        task_id = cursor.lastrowid
        
        # 토큰 생성
        token = make_token(task_id)
        conn.execute("UPDATE tasks SET hmac_token = ? WHERE id = ?", (token, task_id))
        
        print(f"✅ 업무가 추가되었습니다!")
        print(f"   - ID: {task_id}")
        print(f"   - 제목: {title}")
        print(f"   - 담당자: {assignee} ({email})")
        print(f"   - 주기: {frequency}")
        print(f"   - 완료 링크: http://localhost:8080/complete?token={token}")
        
        return True

def delete_task():
    """업무 삭제"""
    tasks = show_tasks()
    if not tasks:
        return False
    
    try:
        task_id = int(input("\n삭제할 업무 ID: "))
        
        with get_conn() as conn:
            task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            
            if not task:
                print("❌ 해당 ID의 업무를 찾을 수 없습니다.")
                return False
            
            print(f"\n⚠️ 삭제 확인:")
            print(f"   - ID: {task['id']}")
            print(f"   - 제목: {task['title']}")
            print(f"   - 담당자: {task['assignee']}")
            
            confirm = input("정말 삭제하시겠습니까? (y/N): ").strip().lower()
            
            if confirm == 'y':
                conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                print("✅ 업무가 삭제되었습니다.")
                return True
            else:
                print("❌ 삭제가 취소되었습니다.")
                return False
                
    except ValueError:
        print("❌ 올바른 숫자를 입력해주세요.")
        return False

def update_task():
    """업무 수정"""
    tasks = show_tasks()
    if not tasks:
        return False
    
    try:
        task_id = int(input("\n수정할 업무 ID: "))
        
        with get_conn() as conn:
            task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            
            if not task:
                print("❌ 해당 ID의 업무를 찾을 수 없습니다.")
                return False
            
            print(f"\n📝 업무 수정 (현재값, Enter로 유지)")
            print(f"현재 제목: {task['title']}")
            new_title = input("새 제목: ").strip()
            if not new_title:
                new_title = task['title']
            
            print(f"현재 담당자: {task['assignee']}")
            new_assignee = input("새 담당자: ").strip()
            if not new_assignee:
                new_assignee = task['assignee']
            
            print(f"현재 주기: {task['frequency']}")
            print("1. daily (매일)")
            print("2. weekly (매주)")
            print("3. monthly (매월)")
            freq_choice = input("새 주기 (1-3, Enter로 유지): ").strip()
            frequency_map = {'1': 'daily', '2': 'weekly', '3': 'monthly'}
            new_frequency = frequency_map.get(freq_choice, task['frequency'])
            
            print(f"현재 이메일: {task['assignee_email']}")
            new_email = input("새 이메일: ").strip()
            if not new_email:
                new_email = task['assignee_email']
            
            # 업데이트
            conn.execute("""
                UPDATE tasks 
                SET title = ?, assignee = ?, assignee_email = ?, frequency = ?,
                    updated_at = ?
                WHERE id = ?
            """, (new_title, new_assignee, new_email, new_frequency, 
                  datetime.datetime.now().isoformat(), task_id))
            
            # 사용자 정보도 업데이트
            conn.execute("INSERT OR REPLACE INTO users (email, name) VALUES (?, ?)", 
                        (new_email, new_assignee))
            
            print("✅ 업무가 수정되었습니다!")
            return True
            
    except ValueError:
        print("❌ 올바른 숫자를 입력해주세요.")
        return False

def show_completion_stats():
    """완료 통계 표시"""
    with get_conn() as conn:
        # 전체 통계
        total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        completed_tasks = conn.execute("""
            SELECT COUNT(*) FROM tasks WHERE last_completed_at IS NOT NULL
        """).fetchone()[0]
        
        print(f"\n📊 업무 통계:")
        print(f"   - 전체 업무: {total_tasks}개")
        print(f"   - 완료된 업무: {completed_tasks}개")
        print(f"   - 미완료 업무: {total_tasks - completed_tasks}개")
        
        # 담당자별 통계
        assignee_stats = conn.execute("""
            SELECT assignee, COUNT(*) as total,
                   SUM(CASE WHEN last_completed_at IS NOT NULL THEN 1 ELSE 0 END) as completed
            FROM tasks 
            GROUP BY assignee
        """).fetchall()
        
        if assignee_stats:
            print(f"\n👥 담당자별 통계:")
            for stat in assignee_stats:
                completion_rate = (stat['completed'] / stat['total']) * 100 if stat['total'] > 0 else 0
                print(f"   - {stat['assignee']}: {stat['completed']}/{stat['total']} ({completion_rate:.1f}%)")

def main_menu():
    """메인 메뉴"""
    while True:
        print("\n🎯 업무 관리 도구")
        print("=" * 30)
        print("1. 업무 목록 보기")
        print("2. 업무 추가")
        print("3. 업무 수정")
        print("4. 업무 삭제")
        print("5. 완료 통계")
        print("6. 웹 대시보드 주소")
        print("0. 종료")
        
        choice = input("\n선택하세요 (0-6): ").strip()
        
        if choice == '1':
            show_tasks()
        elif choice == '2':
            add_task()
        elif choice == '3':
            update_task()
        elif choice == '4':
            delete_task()
        elif choice == '5':
            show_completion_stats()
        elif choice == '6':
            print("\n🌐 웹 대시보드:")
            print("   - 대시보드: http://localhost:8080/dashboard")
            print("   - 서버 실행: python -m uvicorn webhook:app --host 0.0.0.0 --port 8080")
        elif choice == '0':
            print("👋 업무 관리 도구를 종료합니다.")
            break
        else:
            print("❌ 올바른 선택지를 입력해주세요.")

if __name__ == "__main__":
    main_menu()
