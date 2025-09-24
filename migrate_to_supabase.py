# migrate_to_supabase.py - SQLite 데이터를 Supabase로 마이그레이션
import sqlite3
from supabase_client import SupabaseManager
from mailer import make_token
import os

# 마이그레이션용 Supabase 매니저 (service_role 키 사용)
supabase_manager = SupabaseManager(use_service_key=True)

def migrate_users_from_sqlite():
    """SQLite에서 사용자 데이터를 Supabase로 마이그레이션"""
    print("👥 사용자 데이터 마이그레이션 시작...")
    
    if not os.path.exists("reminder.db"):
        print("❌ reminder.db 파일이 없습니다.")
        return False
    
    try:
        # SQLite 연결
        conn = sqlite3.connect("reminder.db")
        conn.row_factory = sqlite3.Row
        
        # 사용자 데이터 조회
        users = conn.execute("SELECT * FROM users").fetchall()
        
        migrated_count = 0
        for user in users:
            success = supabase_manager.add_user(user['email'], user['name'])
            if success:
                migrated_count += 1
                print(f"✅ 사용자 마이그레이션: {user['name']} ({user['email']})")
            else:
                print(f"⚠️ 사용자 마이그레이션 실패: {user['email']}")
        
        conn.close()
        print(f"✅ 사용자 마이그레이션 완료: {migrated_count}명")
        return True
        
    except Exception as e:
        print(f"❌ 사용자 마이그레이션 오류: {e}")
        return False

def migrate_tasks_from_sqlite():
    """SQLite에서 업무 데이터를 Supabase로 마이그레이션"""
    print("📋 업무 데이터 마이그레이션 시작...")
    
    if not os.path.exists("reminder.db"):
        print("❌ reminder.db 파일이 없습니다.")
        return False
    
    try:
        # SQLite 연결
        conn = sqlite3.connect("reminder.db")
        conn.row_factory = sqlite3.Row
        
        # 업무 데이터 조회
        tasks = conn.execute("SELECT * FROM tasks").fetchall()
        
        migrated_count = 0
        for task in tasks:
            # Supabase에 업무 추가
            task_data = {
                'title': task['title'],
                'assignee_email': task['assignee_email'],
                'frequency': task['frequency'],
                'status': task['status'],
                'creator_name': task['creator_name'] if 'creator_name' in task.keys() else '',
                'due_date': task['due_date'] if 'due_date' in task.keys() else None,
                'last_completed_at': task['last_completed_at'] if 'last_completed_at' in task.keys() else None,
                'created_at': task['created_at'] if 'created_at' in task.keys() else supabase_manager.kst_now().isoformat()
            }
            
            # HMAC 토큰 생성 (기존 토큰이 없으면)
            if 'hmac_token' not in task.keys() or not task['hmac_token']:
                token = make_token(task['id'])
                task_data['hmac_token'] = token
            else:
                task_data['hmac_token'] = task['hmac_token']
            
            try:
                response = supabase_manager.supabase.table('tasks').insert(task_data).execute()
                if response.data:
                    migrated_count += 1
                    print(f"✅ 업무 마이그레이션: {task['title']}")
                else:
                    print(f"⚠️ 업무 마이그레이션 실패: {task['title']}")
            except Exception as e:
                print(f"⚠️ 업무 마이그레이션 오류 {task['title']}: {e}")
        
        conn.close()
        print(f"✅ 업무 마이그레이션 완료: {migrated_count}개")
        return True
        
    except Exception as e:
        print(f"❌ 업무 마이그레이션 오류: {e}")
        return False

def create_sample_data():
    """Supabase에 샘플 데이터 생성"""
    print("🎯 샘플 데이터 생성 시작...")
    
    # 샘플 사용자 추가
    sample_users = [
        ("bae.jae.kwon@drbworld.com", "배재권"),
        ("admin@company.com", "관리자"),
        ("test@company.com", "테스트 사용자")
    ]
    
    for email, name in sample_users:
        supabase_manager.add_user(email, name)
    
    # 샘플 업무 추가
    sample_tasks = [
        ("일일 이메일 확인", "bae.jae.kwon@drbworld.com", "daily", "배재권"),
        ("주간 리포트 작성", "bae.jae.kwon@drbworld.com", "weekly", "배재권"),
        ("월간 성과 평가", "bae.jae.kwon@drbworld.com", "monthly", "배재권"),
        ("시스템 백업 확인", "admin@company.com", "daily", "관리자"),
        ("보안 점검", "admin@company.com", "weekly", "관리자"),
    ]
    
    created_count = 0
    for title, assignee_email, frequency, creator_name in sample_tasks:
        task_id = supabase_manager.add_task(title, assignee_email, frequency, creator_name)
        if task_id:
            # 토큰 생성 및 업데이트
            token = make_token(task_id)
            supabase_manager.update_task_token(task_id, token)
            created_count += 1
            print(f"✅ 샘플 업무 생성: {title}")
    
    print(f"✅ 샘플 데이터 생성 완료: 사용자 {len(sample_users)}명, 업무 {created_count}개")
    return True

def main():
    """메인 마이그레이션 함수"""
    print("🚀 Supabase 마이그레이션 시작...")
    print("=" * 50)
    
    # .env 파일 확인
    if not os.path.exists(".env"):
        print("❌ .env 파일이 없습니다. Supabase 설정을 먼저 완료해주세요.")
        print("📝 .env 파일에 다음 정보를 입력하세요:")
        print("   SUPABASE_URL=your_supabase_project_url")
        print("   SUPABASE_KEY=your_supabase_anon_key")
        print("   SUPABASE_SERVICE_KEY=your_supabase_service_role_key")
        return
    
    try:
        # Supabase 연결 테스트
        stats = supabase_manager.get_task_statistics()
        print(f"✅ Supabase 연결 성공 - 현재 업무 수: {stats['total_tasks']}개")
        
        choice = input("\n마이그레이션 옵션을 선택하세요:\n1. SQLite에서 마이그레이션\n2. 새로운 샘플 데이터 생성\n선택 (1 또는 2): ")
        
        if choice == "1":
            # SQLite 마이그레이션
            print("\n📦 SQLite 데이터 마이그레이션 시작...")
            migrate_users_from_sqlite()
            migrate_tasks_from_sqlite()
            
        elif choice == "2":
            # 샘플 데이터 생성
            print("\n🎯 샘플 데이터 생성 시작...")
            create_sample_data()
            
        else:
            print("❌ 잘못된 선택입니다.")
            return
        
        # 최종 통계
        final_stats = supabase_manager.get_task_statistics()
        print("\n🎉 마이그레이션 완료!")
        print("=" * 50)
        print(f"📊 최종 통계:")
        print(f"   - 전체 업무: {final_stats['total_tasks']}개")
        print(f"   - 완료 업무: {final_stats['completed_tasks']}개")
        print(f"   - 진행 중: {final_stats['pending_tasks']}개")
        print("\n🔗 다음 단계:")
        print("1. 서버 실행: python -m uvicorn webhook:app --host 0.0.0.0 --port 8080")
        print("2. 대시보드 확인: http://localhost:8080/dashboard")
        print("3. 이메일 테스트: http://localhost:8080/send-test-email")
        
    except Exception as e:
        print(f"❌ 마이그레이션 오류: {e}")
        print("💡 .env 파일의 Supabase 설정을 확인해주세요.")

if __name__ == "__main__":
    main()
