# webhook.py - Supabase 버전
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from typing import List, Optional
import yaml
from urllib.parse import urlparse
from datetime import datetime
import os
import logging
import sqlite3
from contextlib import contextmanager

# 로컬 SQLite 우선 사용을 위한 설정
USE_SQLITE_FIRST = True

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

# Supabase는 선택적으로만 사용
try:
    from supabase_client import SupabaseManager
    supabase_manager = SupabaseManager()
    print("Supabase 연결 성공")
except Exception as e:
    print(f"Supabase 연결 실패, SQLite 모드로 실행: {e}")
    supabase_manager = None

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="해야할일 관리 시스템", version="2.0.0")

# favicon.ico 404 오류 방지
@app.get("/favicon.ico")
def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

# 헬스체크 엔드포인트
@app.get("/")
@app.get("/health")
def health_check():
    """서버 상태 확인 - SQLite 우선"""
    try:
        # SQLite 기본 상태 확인
        with get_sqlite_conn() as conn:
            task_count = conn.execute("SELECT COUNT(*) as count FROM tasks").fetchone()
            sqlite_tasks = task_count["count"] if task_count else 0
        
        return {
            "status": "ok", 
            "database": "sqlite_connected",
            "total_tasks": sqlite_tasks,
            "message": "웹훅 서버가 정상 실행 중입니다",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}

def _cfg():
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

def _pick_target(next_url, cfg_url):
    try:
        host = urlparse(next_url).hostname if next_url else None
    except Exception:
        host = None
    if host in (None, "0.0.0.0"):
        return cfg_url
    return next_url or cfg_url

def generate_sqlite_dashboard():
    """SQLite 데이터로 대시보드 HTML 생성"""
    try:
        with get_sqlite_conn() as conn:
            # 기본 통계
            total_tasks = conn.execute("SELECT COUNT(*) as count FROM tasks").fetchone()["count"]
            completed_tasks = conn.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'done'").fetchone()["count"]
            pending_tasks = conn.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'pending'").fetchone()["count"]
            
            # 오늘 완료된 업무 (예시로 최근 24시간)
            today_completed = conn.execute("""
                SELECT COUNT(*) as count FROM tasks 
                WHERE status = 'done' AND 
                datetime(last_completed_at) > datetime('now', '-1 day')
            """).fetchone()["count"]
            
            # 업무 목록 조회
            all_tasks = conn.execute("""
                SELECT id, title, assignee_email, frequency, status, last_completed_at
                FROM tasks ORDER BY id DESC
            """).fetchall()
            
            # 상태별 분류
            pending_task_list = [dict(task) for task in all_tasks if task['status'] == 'pending']
            completed_task_list = [dict(task) for task in all_tasks if task['status'] == 'done']
            
            # 주기별 분류 (pending만)
            daily_tasks = [t for t in pending_task_list if t['frequency'] == 'daily']
            weekly_tasks = [t for t in pending_task_list if t['frequency'] == 'weekly']
            monthly_tasks = [t for t in pending_task_list if t['frequency'] == 'monthly']
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S KST")
            
            return f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📋 해야할일 관리 대시보드 (SQLite)</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
        .stat-number {{ font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }}
        .stat-label {{ color: #666; font-size: 1.1em; }}
        .section {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .section h2 {{ margin-top: 0; color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        .task-list {{ list-style: none; padding: 0; }}
        .task-item {{ padding: 15px; border: 1px solid #e1e5e9; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }}
        .task-item.daily {{ border-left: 5px solid #28a745; }}
        .task-item.weekly {{ border-left: 5px solid #ffc107; }}
        .task-item.monthly {{ border-left: 5px solid #dc3545; }}
        .task-title {{ font-weight: 600; flex-grow: 1; }}
        .task-meta {{ font-size: 0.9em; color: #666; margin-left: 10px; }}
        .completion-log {{ background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #28a745; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
        .refresh-btn {{ background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
        .api-links {{ margin-top: 20px; text-align: center; }}
        .api-links a {{ color: #667eea; text-decoration: none; margin: 0 10px; }}
    </style>
    <script>
        function refreshDashboard() {{ location.reload(); }}
        setInterval(refreshDashboard, 30000); // 30초마다 자동 새로고침
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 해야할일 관리 대시보드</h1>
            <p>🗃️ SQLite 로컬 데이터베이스 | 마지막 업데이트: {current_time}</p>
            <button class="refresh-btn" onclick="refreshDashboard()">🔄 새로고침</button>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" style="color: #667eea;">{total_tasks}</div>
                <div class="stat-label">전체 업무</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #28a745;">{completed_tasks}</div>
                <div class="stat-label">완료된 업무</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #ffc107;">{pending_tasks}</div>
                <div class="stat-label">진행 중 업무</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #dc3545;">{today_completed}</div>
                <div class="stat-label">최근 24시간 완료</div>
            </div>
        </div>

        <div class="section">
            <h2>📅 일일 업무 ({len(daily_tasks)}개)</h2>
            <ul class="task-list">
                {''.join([f'<li class="task-item daily"><span class="task-title">{task["title"]}</span><span class="task-meta">{task["assignee_email"]}</span></li>' for task in daily_tasks]) if daily_tasks else '<li style="text-align: center; color: #666;">완료된 일일 업무가 없습니다 ✅</li>'}
            </ul>
        </div>

        <div class="section">
            <h2>📆 주간 업무 ({len(weekly_tasks)}개)</h2>
            <ul class="task-list">
                {''.join([f'<li class="task-item weekly"><span class="task-title">{task["title"]}</span><span class="task-meta">{task["assignee_email"]}</span></li>' for task in weekly_tasks]) if weekly_tasks else '<li style="text-align: center; color: #666;">완료된 주간 업무가 없습니다 ✅</li>'}
            </ul>
        </div>

        <div class="section">
            <h2>📊 월간 업무 ({len(monthly_tasks)}개)</h2>
            <ul class="task-list">
                {''.join([f'<li class="task-item monthly"><span class="task-title">{task["title"]}</span><span class="task-meta">{task["assignee_email"]}</span></li>' for task in monthly_tasks]) if monthly_tasks else '<li style="text-align: center; color: #666;">완료된 월간 업무가 없습니다 ✅</li>'}
            </ul>
        </div>

        <div class="section">
            <h2>🎉 최근 완료된 업무</h2>
            {''.join([f'<div class="completion-log"><strong>{task["title"]}</strong><br><span class="timestamp">완료 시간: {task["last_completed_at"] or "N/A"} | 담당자: {task["assignee_email"]}</span></div>' for task in completed_task_list[:5]]) if completed_task_list else '<p style="text-align: center; color: #666;">아직 완료된 업무가 없습니다.</p>'}
        </div>

        <div class="api-links">
            <h3>🔗 API 링크</h3>
            <a href="/api/stats">📊 통계 API</a>
            <a href="/api/tasks">📋 업무 API</a>
            <a href="/send-test-email">📧 테스트 이메일</a>
        </div>
    </div>
</body>
</html>
"""
    except Exception as e:
        logger.error(f"SQLite 대시보드 생성 오류: {e}")
        return f"""
<html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
    <h1>❌ 대시보드 오류</h1>
    <p>SQLite 데이터베이스 조회 중 오류가 발생했습니다:</p>
    <p style="color: red;">{str(e)}</p>
    <p><a href="/health" style="color: #007bff;">서버 상태 확인</a></p>
</body></html>
"""

def generate_supabase_dashboard(stats, all_tasks, recent_completions):
    """Supabase 데이터로 대시보드 HTML 생성"""
    
    # 업무를 상태별로 분류
    pending_tasks = [t for t in all_tasks if t['status'] == 'pending']
    completed_tasks = [t for t in all_tasks if t['status'] == 'done']
    
    # 주기별 분류
    daily_tasks = [t for t in pending_tasks if t['frequency'] == 'daily']
    weekly_tasks = [t for t in pending_tasks if t['frequency'] == 'weekly']
    monthly_tasks = [t for t in pending_tasks if t['frequency'] == 'monthly']
    
    current_time = supabase_manager.kst_now().strftime("%Y-%m-%d %H:%M:%S KST")
    
    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📋 해야할일 관리 대시보드 (Supabase)</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f7fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; text-align: center; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .stat-card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
            .stat-number {{ font-size: 2.5em; font-weight: bold; margin-bottom: 10px; }}
            .stat-label {{ color: #666; font-size: 1.1em; }}
            .section {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            .section h2 {{ margin-top: 0; color: #333; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
            .task-list {{ list-style: none; padding: 0; }}
            .task-item {{ padding: 15px; border: 1px solid #e1e5e9; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: between; align-items: center; }}
            .task-item.daily {{ border-left: 5px solid #28a745; }}
            .task-item.weekly {{ border-left: 5px solid #ffc107; }}
            .task-item.monthly {{ border-left: 5px solid #dc3545; }}
            .task-title {{ font-weight: 600; flex-grow: 1; }}
            .task-meta {{ font-size: 0.9em; color: #666; margin-left: 10px; }}
            .completion-log {{ background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px; border-left: 4px solid #28a745; }}
            .timestamp {{ color: #666; font-size: 0.9em; }}
            .refresh-btn {{ background: #667eea; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
            .api-links {{ margin-top: 20px; text-align: center; }}
            .api-links a {{ color: #667eea; text-decoration: none; margin: 0 10px; }}
        </style>
        <script>
            function refreshDashboard() {{ location.reload(); }}
            setInterval(refreshDashboard, 30000); // 30초마다 자동 새로고침
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📋 해야할일 관리 대시보드</h1>
                <p>🔗 Supabase 실시간 연동 | 마지막 업데이트: {current_time}</p>
                <button class="refresh-btn" onclick="refreshDashboard()">🔄 새로고침</button>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number" style="color: #667eea;">{stats['total_tasks']}</div>
                    <div class="stat-label">전체 업무</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #28a745;">{stats['completed_tasks']}</div>
                    <div class="stat-label">완료된 업무</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #ffc107;">{stats['pending_tasks']}</div>
                    <div class="stat-label">진행 중 업무</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" style="color: #dc3545;">{stats['today_completed']}</div>
                    <div class="stat-label">오늘 완료</div>
                </div>
            </div>

            <div class="section">
                <h2>📅 일일 업무 ({len(daily_tasks)}개)</h2>
                <ul class="task-list">
                    {''.join([f'<li class="task-item daily"><span class="task-title">{task["title"]}</span><span class="task-meta">{task["assignee_email"]}</span></li>' for task in daily_tasks]) if daily_tasks else '<li style="text-align: center; color: #666;">완료된 일일 업무가 없습니다 ✅</li>'}
                </ul>
            </div>

            <div class="section">
                <h2>📆 주간 업무 ({len(weekly_tasks)}개)</h2>
                <ul class="task-list">
                    {''.join([f'<li class="task-item weekly"><span class="task-title">{task["title"]}</span><span class="task-meta">{task["assignee_email"]}</span></li>' for task in weekly_tasks]) if weekly_tasks else '<li style="text-align: center; color: #666;">완료된 주간 업무가 없습니다 ✅</li>'}
                </ul>
            </div>

            <div class="section">
                <h2>📊 월간 업무 ({len(monthly_tasks)}개)</h2>
                <ul class="task-list">
                    {''.join([f'<li class="task-item monthly"><span class="task-title">{task["title"]}</span><span class="task-meta">{task["assignee_email"]}</span></li>' for task in monthly_tasks]) if monthly_tasks else '<li style="text-align: center; color: #666;">완료된 월간 업무가 없습니다 ✅</li>'}
                </ul>
            </div>

            <div class="section">
                <h2>🎉 최근 완료 기록 (Supabase 실시간)</h2>
                {''.join([f'<div class="completion-log"><strong>{log.get("tasks", {}).get("title", "Unknown Task")}</strong><br><span class="timestamp">완료 시간: {log["completed_at"][:19]} | 방법: {log["completion_method"]}</span></div>' for log in recent_completions[:5]]) if recent_completions else '<p style="text-align: center; color: #666;">아직 완료된 업무가 없습니다.</p>'}
            </div>

            <div class="api-links">
                <h3>🔗 API 링크</h3>
                <a href="/api/stats">📊 통계 API</a>
                <a href="/api/tasks">📋 업무 API</a>
                <a href="/api/completions">✅ 완료 기록 API</a>
                <a href="/send-test-email">📧 테스트 이메일</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/health")
def health():
    """서버 상태 확인 - 별도 엔드포인트"""
    return health_check()

@app.get("/complete")
def complete_task(token: str, next: Optional[str] = None, request: Request = None):
    """이메일에서 업무 완료 처리 - SQLite 우선"""
    try:
        # SQLite로 업무 완료 처리
        with get_sqlite_conn() as conn:
            # 토큰으로 업무 찾기
            task = conn.execute(
                "SELECT * FROM tasks WHERE hmac_token = ? AND status = 'pending'", 
                (token,)
            ).fetchone()
            
            if task:
                # 업무 완료 처리
                now = datetime.now().isoformat()
                conn.execute(
                    "UPDATE tasks SET status = 'done', last_completed_at = ? WHERE id = ?",
                    (now, task['id'])
                )
                logger.info(f"✅ 업무 완료: {task['title']} (ID: {task['id']})")
                
                # 대시보드로 리다이렉트
                return RedirectResponse(url="/dashboard", status_code=303)
            else:
                logger.warning(f"⚠️ 업무 완료 실패: 토큰 {token}")
                return HTMLResponse("""
                    <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                        <h2>⚠️ 처리할 수 없습니다</h2>
                        <p>이미 완료되었거나 토큰이 유효하지 않습니다.</p>
                        <p><a href="/dashboard" style="color: #007bff;">📊 대시보드 보기</a></p>
                    </body></html>
                """, status_code=400)
            
    except Exception as e:
        logger.error(f"❌ 업무 완료 처리 오류: {e}")
        return HTMLResponse(f"""
            <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2>❌ 오류 발생</h2>
                <p>업무 완료 처리 중 오류가 발생했습니다: {str(e)}</p>
                <p><a href="/dashboard" style="color: #007bff;">📊 대시보드 보기</a></p>
            </body></html>
        """, status_code=500)

@app.get("/test-complete-tasks")
def test_complete_tasks():
    """다중 완료 기능 테스트"""
    return HTMLResponse("""
        <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h2>🧪 다중 완료 기능 테스트</h2>
            <form action="/complete-tasks" method="post">
                <p>테스트용 체크박스:</p>
                <input type="checkbox" name="task" value="test-token-1" checked> 테스트 업무 1<br>
                <input type="checkbox" name="task" value="test-token-2" checked> 테스트 업무 2<br>
                <br>
                <input type="submit" value="테스트 완료" style="padding:8px 16px;">
            </form>
            <p><a href="/dashboard">대시보드로 이동</a></p>
        </body></html>
    """)

@app.get("/complete-tasks")
async def complete_tasks_get():
    """GET 방식으로 접근할 때 안내 페이지 표시"""
    print("ℹ️ GET /complete-tasks 접근 - 안내 페이지 표시")
    
    html_content = """
    <html>
    <head>
        <title>업무 완료 처리</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center; 
                padding: 50px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                margin: 0;
            }
            .container {
                background: rgba(255, 255, 255, 0.95);
                color: #333;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                max-width: 600px;
                margin: 0 auto;
            }
            .message { 
                background: #e3f2fd; 
                padding: 25px; 
                border-radius: 10px; 
                margin: 25px 0;
                border-left: 5px solid #2196f3;
            }
            .error { 
                background: #ffebee; 
                border-left-color: #f44336;
            }
            .success {
                background: #e8f5e8;
                border-left-color: #4caf50;
            }
            a { 
                color: #1976d2; 
                text-decoration: none; 
                font-weight: bold;
            }
            a:hover { 
                text-decoration: underline; 
                color: #0d47a1;
            }
            .btn {
                display: inline-block;
                padding: 12px 24px;
                margin: 10px;
                background: #2196f3;
                color: white;
                border-radius: 6px;
                text-decoration: none;
                transition: background 0.3s;
            }
            .btn:hover {
                background: #1976d2;
                color: white;
                text-decoration: none;
            }
            .icon { font-size: 48px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">📋</div>
            <h2>업무 완료 처리 안내</h2>
            
            <div class="message error">
                <h3>⚠️ 잘못된 접근 방식입니다</h3>
                <p>이 페이지는 <strong>이메일의 "선택한 업무 모두 완료" 버튼</strong>을 통해서만 접근할 수 있습니다.</p>
                <p>직접 URL을 입력해서는 접근할 수 없습니다.</p>
            </div>
            
            <div class="message">
                <h3>📧 올바른 사용 방법</h3>
                <p>1. 이메일에서 완료할 업무들을 <strong>체크박스로 선택</strong>하세요</p>
                <p>2. <strong>"선택한 업무 모두 완료"</strong> 버튼을 클릭하세요</p>
                <p>3. 자동으로 대시보드로 이동됩니다</p>
            </div>
            
            <div class="message success">
                <h3>� 다른 방법</h3>
                <p>개별 업무 완료는 각 업무의 "개별 완료" 버튼을 사용하세요</p>
                <p>전체 업무 현황은 대시보드에서 확인할 수 있습니다</p>
            </div>
            
            <div style="margin-top: 30px;">
                <a href="/dashboard" class="btn">📊 대시보드로 이동</a>
                <a href="/test-complete-tasks" class="btn">🧪 테스트 페이지</a>
            </div>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 14px;">
                <p>문제가 계속 발생하면 이메일을 다시 받아보거나 개별 완료 버튼을 사용해주세요.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(html_content)

@app.post("/complete-tasks")
async def complete_multiple_tasks(request: Request):
    """이메일 폼에서 다중 업무 완료 처리 (SQLite 우선)"""
    
    print("🚀 /complete-tasks 엔드포인트 시작")  # 기본 print도 추가
    logger.info("🚀 /complete-tasks 엔드포인트 진입")
    
    try:
        print("📝 Form 데이터 파싱 시작")
        form_data = await request.form()
        task_tokens = form_data.getlist("task")  # 체크박스에서 선택된 모든 토큰
        
        print(f"📋 받은 토큰 개수: {len(task_tokens)}")
        logger.info(f"🔍 받은 Form 데이터: {dict(form_data)}")
        logger.info(f"📝 다중 업무 완료 요청: {len(task_tokens)}개 토큰")
        for i, token in enumerate(task_tokens):
            print(f"  토큰 {i+1}: {token[:15]}...")
            logger.info(f"  토큰 {i+1}: {token[:15]}...")
        
        if not task_tokens:
            print("⚠️ 선택된 토큰이 없음")
            logger.warning("⚠️ 선택된 토큰이 없음")
            return HTMLResponse("""
                <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h2>⚠️ 선택된 업무가 없습니다</h2>
                    <p>업무를 선택한 후 다시 시도해주세요.</p>
                    <p><a href="/dashboard" style="color: #007bff;">📊 대시보드 보기</a></p>
                </body></html>
            """)
        
        completed_tasks = []
        failed_tokens = []
        
        for token in task_tokens:
            try:
                logger.info(f"🔍 처리 중인 토큰: {token[:10]}...")
                
                # SQLite 우선 처리
                if USE_SQLITE_FIRST:
                    with get_sqlite_conn() as conn:
                        # 토큰으로 업무 조회 (hmac_token 컬럼 사용)
                        task = conn.execute("""
                            SELECT * FROM tasks 
                            WHERE hmac_token = ? AND status = 'pending'
                        """, (token,)).fetchone()
                        
                        if task:
                            logger.info(f"✅ 업무 발견: {task['title']}")
                            
                            # 업무 완료 처리
                            conn.execute("""
                                UPDATE tasks 
                                SET status = 'done', 
                                    last_completed_at = datetime('now', 'localtime'),
                                    updated_at = datetime('now', 'localtime')
                                WHERE id = ?
                            """, (task['id'],))
                            
                            completed_tasks.append(task['title'])
                            logger.info(f"✅ SQLite 완료: {task['title']}")
                        else:
                            failed_tokens.append(token)
                            logger.warning(f"⚠️ SQLite 완료 실패: 토큰 {token[:10]}... (업무 없음 또는 이미 완료됨)")
                
                # Supabase 백업 처리 (SQLite 실패 시)
                elif supabase_manager and len(completed_tasks) == 0:
                    task = supabase_manager.get_task_by_token(token)
                    if task and supabase_manager.mark_task_completed_by_token(token):
                        completed_tasks.append(task['title'])
                        
                        # 상세 완료 기록 저장
                        completion_data = {
                            'task_id': task['id'],
                            'completed_at': supabase_manager.kst_now().isoformat(),
                            'completion_method': 'email',
                            'user_agent': 'unknown',
                            'ip_address': 'unknown',
                            'notes': f"이메일 폼을 통한 일괄 완료"
                        }
                        supabase_manager.supabase.table('completion_logs').insert(completion_data).execute()
                        logger.info(f"✅ Supabase 완료: {task['title']}")
                    else:
                        failed_tokens.append(token)
                        logger.warning(f"⚠️ Supabase 완료 실패: 토큰 {token}")
                        
            except Exception as e:
                failed_tokens.append(token)
                logger.error(f"❌ 토큰 처리 오류 {token}: {e}")
        
        print(f"🎉 처리 완료: 성공 {len(completed_tasks)}개, 실패 {len(failed_tokens)}개")
        logger.info(f"🎉 완료된 업무: {len(completed_tasks)}개, 실패: {len(failed_tokens)}개")
        
        # Request 객체에서 base URL 가져오기 (개별 완료와 완전히 동일한 방식)
        base_url = str(request.base_url).rstrip("/")
        dashboard_url = f"{base_url}/dashboard"
        
        print(f"🔗 Base URL: {base_url}")
        print(f"🔗 Dashboard URL: {dashboard_url}")
        print(f"� 대시보드로 리다이렉트 (개별 완료와 동일한 로직)")
        logger.info(f"� 대시보드로 리다이렉트: {dashboard_url}")
        
        return RedirectResponse(url=dashboard_url, status_code=303)
        
    except Exception as e:
        logger.error(f"❌ 다중 업무 완료 처리 오류: {e}")
        logger.error(f"❌ 오류 상세: {str(e)}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        return HTMLResponse(f"""
            <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2>❌ 처리 오류</h2>
                <p>업무 완료 처리 중 오류가 발생했습니다:</p>
                <p style="color: red;">{str(e)}</p>
                <p><a href="/dashboard" style="color: #007bff;">📊 대시보드 보기</a></p>
                <p><a href="/test-complete-tasks" style="color: #007bff;">🧪 테스트 페이지</a></p>
            </body></html>
        """, status_code=500)

@app.get("/dashboard")
async def serve_dashboard():
    """SQLite 기반 대시보드"""
    try:
        # SQLite 대시보드 생성 (파라미터 없이)
        dashboard_html = generate_sqlite_dashboard()
        
        logger.info("📊 SQLite 대시보드 생성 완료")
        
        return HTMLResponse(content=dashboard_html, media_type="text/html; charset=utf-8")
        
    except Exception as e:
        logger.error(f"❌ 대시보드 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"""
            <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>❌ 대시보드 오류</h1>
                <p>데이터베이스 조회 중 오류가 발생했습니다:</p>
                <p style="color: red;">{str(e)}</p>
                <p><a href="/health" style="color: #007bff;">서버 상태 확인</a></p>
            </body></html>
        """, status_code=500)

@app.get("/send-test-email")
async def send_test_email():
    """Supabase 기반 이메일 발송 테스트"""
    try:
        from digest import run_daily_digest
        
        logger.info("📧 Supabase 기반 이메일 발송 시작...")
        result = run_daily_digest()
        
        return HTMLResponse(f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>📧 Supabase 이메일 발송 테스트</h2>
            <p>✅ 이메일 발송 완료!</p>
            <p>📬 이메일을 확인하세요. 모든 완료 기록이 Supabase에 실시간으로 저장됩니다.</p>
            <p>📊 <a href="/dashboard" style="color: #007bff;">실시간 대시보드 보기</a></p>
            <p>🔗 <a href="/api/stats" style="color: #007bff;">API 통계 보기</a></p>
        </body></html>
        """)
        
    except Exception as e:
        logger.error(f"❌ 이메일 발송 오류: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"""
        <html><body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>❌ 이메일 발송 실패</h2>
            <p>오류: {str(e)}</p>
            <p><a href="/dashboard" style="color: #007bff;">📊 대시보드 보기</a></p>
        </body></html>
        """, status_code=500)

# ========== API 엔드포인트 ==========

@app.get("/api/stats")
def get_statistics():
    """업무 통계 API - SQLite 우선"""
    try:
        with get_sqlite_conn() as conn:
            total_tasks = conn.execute("SELECT COUNT(*) as count FROM tasks").fetchone()["count"]
            completed_tasks = conn.execute("SELECT COUNT(*) as count FROM tasks WHERE status = 'done'").fetchone()["count"]
            pending_tasks = total_tasks - completed_tasks
            
            today = datetime.now().strftime('%Y-%m-%d')
            today_completed = conn.execute(
                "SELECT COUNT(*) as count FROM tasks WHERE DATE(last_completed_at) = ?", 
                (today,)
            ).fetchone()["count"]
            
            stats = {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'pending_tasks': pending_tasks,
                'today_completed': today_completed
            }
            
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"API 통계 조회 오류: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/tasks")
def get_all_tasks():
    """모든 업무 조회 API - SQLite 우선"""
    try:
        with get_sqlite_conn() as conn:
            tasks = conn.execute("""
                SELECT id, title, assignee_email, frequency, status, created_at, last_completed_at, hmac_token
                FROM tasks ORDER BY created_at DESC
            """).fetchall()
            
            # Row 객체를 dict로 변환
            tasks_list = [dict(task) for task in tasks]
            
        return {"success": True, "data": tasks_list, "count": len(tasks_list)}
    except Exception as e:
        logger.error(f"API 업무 조회 오류: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/completions")
def get_completion_logs(limit: int = 50):
    """완료 기록 조회 API"""
    try:
        logs = supabase_manager.get_completion_logs(limit=limit)
        return {"success": True, "data": logs, "count": len(logs)}
    except Exception as e:
        logger.error(f"API 완료 기록 조회 오류: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/tasks")
def create_task(title: str = Form(...), assignee_email: str = Form(...), 
                frequency: str = Form(...), creator_name: str = Form(...)):
    """새 업무 생성 API"""
    try:
        task_id = supabase_manager.add_task(title, assignee_email, frequency, creator_name)
        if task_id:
            return {"success": True, "task_id": task_id, "message": "업무가 생성되었습니다."}
        else:
            return {"success": False, "error": "업무 생성에 실패했습니다."}
    except Exception as e:
        logger.error(f"API 업무 생성 오류: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    # GitHub Codespaces, Railway, Render 등에서 PORT 환경변수 사용
    port = int(os.environ.get("PORT", 8080))  # 기본 포트를 8080으로 변경
    host = "0.0.0.0"
    
    logger.info(f"🚀 웹훅 서버 시작 - 호스트: {host}, 포트: {port}")
    logger.info(f"📊 대시보드: http://{host}:{port}/dashboard")
    logger.info(f"🔍 헬스체크: http://{host}:{port}/health")
    
    uvicorn.run(app, host=host, port=port)
