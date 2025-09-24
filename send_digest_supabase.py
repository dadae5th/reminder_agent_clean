# send_digest_supabase.py - Supabase 기반 메일 발송 시스템
import sqlite3
import os
from datetime import datetime, timedelta
import yaml
from contextlib import contextmanager
from supabase_client import SupabaseManager
from mailer import make_token, build_task_url, send_email

# 시간대 설정 - zoneinfo 호환성 처리
try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo("Asia/Seoul")
except ImportError:
    # Python 3.8 이하 호환성
    from datetime import timezone
    KST = timezone(timedelta(hours=9))

@contextmanager
def get_sqlite_conn():
    """SQLite 연결 관리"""
    conn = sqlite3.connect("reminder.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def _load_cfg():
    """설정 로드 - config.yaml 강제 사용 (환경변수 무시)"""
    print("[INFO] 🔧 config.yaml에서 설정 로드") 
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        raise Exception("config.yaml 파일이 없습니다.")

def get_users_and_tasks_from_sqlite():
    """SQLite에서만 사용자와 업무 정보 가져오기 (GitHub Actions용)"""
    users_tasks = {}
    
    try:
        with get_sqlite_conn() as conn:
            # 사용자별 업무 조회
            query = """
                SELECT DISTINCT u.email, u.name,
                       t.id, t.title, t.frequency, t.hmac_token,
                       t.last_completed_at, t.due_date
                FROM users u
                JOIN tasks t ON u.email = t.assignee_email
                WHERE t.status = 'pending'
                ORDER BY u.email, t.id
            """
            
            rows = conn.execute(query).fetchall()
            
            current_email = None
            current_user_name = None
            current_tasks = []
            
            for row in rows:
                email = row['email']
                
                if email != current_email:
                    # 이전 사용자 데이터 저장
                    if current_email and current_tasks:
                        today_tasks = filter_tasks_for_today(current_tasks)
                        if today_tasks:
                            users_tasks[current_email] = {
                                'name': current_user_name,
                                'tasks': today_tasks
                            }
                    
                    # 새 사용자 시작
                    current_email = email
                    current_user_name = row['name']
                    current_tasks = []
                
                # 업무 데이터 추가
                task_data = {
                    'id': row['id'],
                    'title': row['title'],
                    'frequency': row['frequency'],
                    'hmac_token': row['hmac_token'],
                    'last_completed_at': row['last_completed_at'],
                    'due_date': row['due_date']
                }
                current_tasks.append(task_data)
            
            # 마지막 사용자 처리
            if current_email and current_tasks:
                today_tasks = filter_tasks_for_today(current_tasks)
                if today_tasks:
                    users_tasks[current_email] = {
                        'name': current_user_name,
                        'tasks': today_tasks
                    }
            
            print(f"[SUCCESS] ✅ SQLite에서 {len(users_tasks)}명의 업무 데이터 조회 성공")
            return users_tasks
            
    except Exception as e:
        print(f"[ERROR] ❌ SQLite 조회 실패: {e}")
        return {}

def get_users_and_tasks():
    """Supabase 또는 SQLite에서 사용자와 업무 정보 가져오기"""
    users_tasks = {}
    
    # GitHub Actions 환경에서는 SQLite만 사용 (간단함)
    if os.getenv('GITHUB_ACTIONS') == 'true':
        print("[INFO] 🔗 GitHub Actions 환경: SQLite 모드 사용")
        return get_users_and_tasks_from_sqlite()
    
    try:
        # Supabase 시도
        print("[INFO] 🔗 Supabase에서 데이터 조회 시도...")
        supabase_manager = SupabaseManager(use_service_key=False)
        
        # 사용자 목록 가져오기
        users = supabase_manager.get_all_users()
        
        # SSL 오류나 연결 오류 시 즉시 fallback
        if not users:
            raise Exception("No users found from Supabase")
            
        print(f"[INFO] 📧 Supabase에서 {len(users)}명의 사용자 발견")
        
        for user in users:
            email = user['email']
            # 해당 사용자의 오늘 할 업무 가져오기
            tasks = supabase_manager.get_tasks_for_today(email)
            if tasks:
                users_tasks[email] = {
                    'name': user['name'],
                    'tasks': tasks
                }
                print(f"[INFO] 📋 {email}: {len(tasks)}개 업무")
        
        print(f"[SUCCESS] ✅ Supabase에서 {len(users_tasks)}명의 업무 데이터 조회 성공")
        return users_tasks
        
    except Exception as e:
        print(f"[WARNING] ⚠️ Supabase 연결 실패: {e}")
        print("[INFO] 🔄 SQLite fallback 모드로 전환...")
        
        # SQLite fallback
        try:
            with get_sqlite_conn() as conn:
                # 사용자별 업무 조회
                query = """
                    SELECT DISTINCT u.email, u.name,
                           t.id, t.title, t.frequency, t.hmac_token,
                           t.last_completed_at, t.due_date
                    FROM users u
                    JOIN tasks t ON u.email = t.assignee_email
                    WHERE t.status = 'pending'
                    ORDER BY u.email, t.id
                """
                
                rows = conn.execute(query).fetchall()
                
                current_email = None
                current_tasks = []
                
                for row in rows:
                    email = row['email']
                    
                    if email != current_email:
                        # 이전 사용자 데이터 저장
                        if current_email and current_tasks:
                            # 오늘 해야 할 업무 필터링
                            today_tasks = filter_tasks_for_today(current_tasks)
                            if today_tasks:
                                users_tasks[current_email] = {
                                    'name': rows[0]['name'] if rows else email.split('@')[0],
                                    'tasks': today_tasks
                                }
                        
                        # 새 사용자 시작
                        current_email = email
                        current_tasks = []
                    
                    # 업무 데이터 추가
                    task_data = {
                        'id': row['id'],
                        'title': row['title'],
                        'frequency': row['frequency'],
                        'hmac_token': row['hmac_token'],
                        'last_completed_at': row['last_completed_at'],
                        'due_date': row['due_date']
                    }
                    current_tasks.append(task_data)
                
                # 마지막 사용자 처리
                if current_email and current_tasks:
                    today_tasks = filter_tasks_for_today(current_tasks)
                    if today_tasks:
                        users_tasks[current_email] = {
                            'name': current_tasks[0].get('name', current_email.split('@')[0]),
                            'tasks': today_tasks
                        }
                
                print(f"[SUCCESS] ✅ SQLite에서 {len(users_tasks)}명의 업무 데이터 조회 성공")
                return users_tasks
                
        except Exception as sqlite_error:
            print(f"[ERROR] ❌ SQLite fallback도 실패: {sqlite_error}")
            return {}

def filter_tasks_for_today(tasks):
    """오늘 해야 할 업무 필터링"""
    now = datetime.now(KST)
    today_tasks = []
    
    for task in tasks:
        frequency = task['frequency']
        last_completed = task.get('last_completed_at')
        
        should_send = False
        
        if frequency == "daily":
            # 매일: 오늘 완료하지 않았으면 발송
            if not last_completed:
                should_send = True
            else:
                try:
                    last_date = datetime.fromisoformat(last_completed.replace('Z', '+00:00'))
                    if last_date.date() < now.date():
                        should_send = True
                except:
                    should_send = True
                    
        elif frequency == "weekly":
            # 주간: 이번 주에 완료하지 않았으면 발송 (월요일 기준)
            week_start = now - timedelta(days=now.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            
            if not last_completed:
                should_send = True
            else:
                try:
                    last_date = datetime.fromisoformat(last_completed.replace('Z', '+00:00'))
                    if last_date < week_start:
                        should_send = True
                except:
                    should_send = True
                    
        elif frequency == "monthly":
            # 월간: 이번 달에 완료하지 않았으면 발송
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            if not last_completed:
                should_send = True
            else:
                try:
                    last_date = datetime.fromisoformat(last_completed.replace('Z', '+00:00'))
                    if last_date < month_start:
                        should_send = True
                except:
                    should_send = True
        
        if should_send:
            today_tasks.append(task)
    
    return today_tasks

def html_for_tasks(tasks, base_url, dashboard_url=None):
    """업무 목록을 HTML로 변환"""
    if not tasks:
        return None
        
    rows = []
    for t in tasks:
        token = t.get("hmac_token")
        if not token:
            token = make_token(t["id"])
            # 토큰 업데이트 시도
            try:
                with get_sqlite_conn() as conn:
                    conn.execute("UPDATE tasks SET hmac_token = ? WHERE id = ?", (token, t["id"]))
            except:
                pass
        
        url = build_task_url(base_url, token)
        if dashboard_url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}next={dashboard_url}"
            
        badge = {"daily":"일간", "weekly":"주간", "monthly":"월간"}.get(t["frequency"], t["frequency"])
        rows.append(f"""
          <tr>
            <td style="padding:8px;border:1px solid #ddd;">
              <input type="checkbox" name="task" value="{token}" style="margin-right:8px;">
              <div style="font-weight:600;display:inline-block">{t['title']}</div>
              <div style="font-size:12px;color:#666;">주기: {badge}</div>
            </td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center;">
              <a href="{url}" style="padding:6px 10px;border-radius:6px;border:1px solid #222;text-decoration:none;">
                개별 완료
              </a>
            </td>
          </tr>
        """)
    
    table = f"""
      <form action="{base_url}/complete-tasks" method="post">
        <table style="border-collapse:collapse;width:100%;font-family:Arial,Apple SD Gothic Neo,Malgun Gothic;">
          <thead>
            <tr>
              <th style="padding:8px;border:1px solid #ddd;background:#f5f5f5;text-align:left;">업무</th>
              <th style="padding:8px;border:1px solid #ddd;background:#f5f5f5;text-align:center;">액션</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
        <div style="margin-top:10px;text-align:center;">
          <input type="submit" value="선택한 업무 모두 완료" 
                 style="padding:8px 16px;border-radius:6px;border:1px solid #222;background:#f8f8f8;cursor:pointer;">
        </div>
      </form>
    """
    return table

def log_email_sent(recipient_email, task_count, status="sent", error_message=None):
    """이메일 발송 기록 저장"""
    try:
        # Supabase에 저장 시도
        supabase_manager = SupabaseManager(use_service_key=True)
        data = {
            'recipient_email': recipient_email,
            'subject': '[일일 알림] 오늘의 해야할 일 📋',
            'task_count': task_count,
            'status': status,
            'error_message': error_message,
            'sent_at': datetime.now(KST).isoformat()
        }
        supabase_manager.supabase.table('email_logs').insert(data).execute()
        print(f"[INFO] 📝 Supabase에 이메일 로그 저장: {recipient_email}")
        
    except Exception as e:
        print(f"[WARNING] ⚠️ Supabase 로그 저장 실패: {e}")
        # SQLite fallback (필요시 구현)

def run_daily_digest():
    """일일 이메일 발송 실행"""
    try:
        cfg = _load_cfg()
        mail_cfg = cfg["smtp"]  # mail 대신 smtp 사용
        base_url = cfg["base_url"]  # server.base_url 대신 base_url 사용
        dashboard_url = cfg["dashboard_url"]  # 직접 dashboard_url 사용
        
        print(f"[INFO] 📧 이메일 발송 시작 - 서버: {mail_cfg['host']}")
        
        # 사용자와 업무 데이터 가져오기
        users_tasks = get_users_and_tasks()
        
        if not users_tasks:
            print("[WARNING] ⚠️ 발송할 업무가 있는 사용자가 없습니다.")
            return False
        
        print(f"[INFO] 📧 이메일 발송 시작 - 대상자: {len(users_tasks)}명")
        
        sent_count = 0
        for email, user_data in users_tasks.items():
            name = user_data['name']
            tasks = user_data['tasks']
            
            print(f"[INFO] 📋 {email} ({name}): {len(tasks)}개 업무")
            
            if tasks:
                # HTML 생성
                html = html_for_tasks(tasks, base_url, dashboard_url)
                if not html:
                    continue
                
                greeting = f"안녕하세요, {name}님! 👋"
                full_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>오늘의 해야할 일</title>
                </head>
                <body style="font-family:Arial,Apple SD Gothic Neo,Malgun Gothic;line-height:1.6;color:#333;">
                    <div style="max-width:600px;margin:0 auto;padding:20px;">
                        <h2 style="color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px;">
                            📋 오늘의 해야할 일
                        </h2>
                        <p>{greeting}</p>
                        <p>오늘 완료해야 할 업무들을 알려드립니다:</p>
                        {html}
                        <div style="margin-top:20px;padding:15px;background:#f8f9fa;border-radius:6px;">
                            <p style="margin:0;font-size:14px;color:#666;">
                                💡 <strong>팁:</strong> 각 업무의 "개별 완료" 버튼을 클릭하거나, 
                                여러 업무를 선택해서 "모두 완료" 버튼을 사용하세요.
                            </p>
                            <p style="margin:5px 0 0 0;font-size:14px;color:#666;">
                                📊 <a href="{dashboard_url}" style="color:#3498db;">대시보드</a>에서 
                                전체 진행 상황을 확인할 수 있습니다.
                            </p>
                        </div>
                        <hr style="margin:20px 0;border:none;border-top:1px solid #eee;">
                        <p style="font-size:12px;color:#999;text-align:center;">
                            업무 알림 시스템 | 생산성 향상을 위한 자동화 도구
                        </p>
                    </div>
                </body>
                </html>
                """
                
                try:
                    print(f"[DEBUG] 📤 {email}에게 이메일 발송 중...")
                    send_email(
                        smtp_host=mail_cfg["host"],
                        smtp_port=mail_cfg["port"],
                        smtp_id=mail_cfg["user"],
                        smtp_pw=mail_cfg["pass"],
                        sender_name=mail_cfg["sender_name"],
                        sender_email=mail_cfg["sender_email"],
                        to_email=email,
                        subject="[일일 알림] 오늘의 해야할 일 📋",
                        html_body=full_html
                    )
                    sent_count += 1
                    print(f"[SUCCESS] ✅ {email}에게 이메일 발송 성공")
                    
                    # 발송 기록 저장
                    log_email_sent(email, len(tasks))
                    
                except Exception as e:
                    print(f"[ERROR] ❌ {email}에게 이메일 발송 실패: {e}")
                    log_email_sent(email, len(tasks), "failed", str(e))
            else:
                print(f"[DEBUG] 📭 {email}: 오늘 할 업무가 없음")
        
        print(f"[SUCCESS] 🎉 총 {sent_count}명에게 이메일 발송 완료")
        return sent_count > 0
        
    except Exception as e:
        print(f"[CRITICAL ERROR] ❌ 이메일 발송 시스템 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Supabase 기반 일일 알림 이메일 발송 시작...")
    success = run_daily_digest()
    if success:
        print("✅ 이메일 발송 완료!")
    else:
        print("❌ 이메일 발송 실패!")
