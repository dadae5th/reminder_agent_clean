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

@app.post("/complete-tasks")
async def complete_multiple_tasks(request: Request):
    """이메일 폼에서 다중 업무 완료 처리"""
    try:
        form_data = await request.form()
        task_tokens = form_data.getlist("task")  # 체크박스에서 선택된 모든 토큰
        
        # 클라이언트 정보 수집
        client_ip = getattr(request, 'client', {}).get('host', 'unknown')
        user_agent = request.headers.get('user-agent', 'unknown')
        
        logger.info(f"📝 다중 업무 완료 요청: {len(task_tokens)}개 토큰")
        
        completed_tasks = []
        failed_tokens = []
        
        for token in task_tokens:
            try:
                # Supabase로 업무 완료 처리
                task = supabase_manager.get_task_by_token(token)
                if task and supabase_manager.mark_task_completed_by_token(token):
                    completed_tasks.append(task['title'])
                    
                    # 상세 완료 기록 저장
                    completion_data = {
                        'task_id': task['id'],
                        'completed_at': supabase_manager.kst_now().isoformat(),
                        'completion_method': 'email',
                        'user_agent': user_agent,
                        'ip_address': client_ip,
                        'notes': f"이메일 폼을 통한 일괄 완료"
                    }
                    supabase_manager.supabase.table('completion_logs').insert(completion_data).execute()
                    logger.info(f"✅ 완료: {task['title']}")
                else:
                    failed_tokens.append(token)
                    logger.warning(f"⚠️ 완료 실패: 토큰 {token}")
                    
            except Exception as e:
                failed_tokens.append(token)
                logger.error(f"❌ 토큰 처리 오류 {token}: {e}")
        
        logger.info(f"🎉 완료된 업무: {len(completed_tasks)}개, 실패: {len(failed_tokens)}개")
        
        # 대시보드로 리다이렉트
        target = _cfg().get("dashboard_url")
        if target:
            return RedirectResponse(url=target, status_code=303)
        
        # 리다이렉트 URL이 없으면 결과 페이지 표시
        success_msg = f"완료된 업무: {', '.join(completed_tasks)}" if completed_tasks else ""
        fail_msg = f"실패한 업무: {len(failed_tokens)}개" if failed_tokens else ""
        
        return HTMLResponse(f"""
            <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2>📋 업무 처리 결과</h2>
                {f'<p style="color: green;">✅ {success_msg}</p>' if success_msg else ''}
                {f'<p style="color: red;">❌ {fail_msg}</p>' if fail_msg else ''}
                <p><a href="/dashboard" style="color: #007bff;">📊 대시보드 보기</a></p>
            </body></html>
        """)
        
    except Exception as e:
        logger.error(f"❌ 다중 업무 완료 처리 오류: {e}")
        return HTMLResponse(f"""
            <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h2>❌ 처리 오류</h2>
                <p>업무 완료 처리 중 오류가 발생했습니다: {str(e)}</p>
                <p><a href="/dashboard" style="color: #007bff;">📊 대시보드 보기</a></p>
            </body></html>
        """, status_code=500)

@app.get("/dashboard")
async def serve_dashboard():
    """실시간 Supabase 대시보드"""
    try:
        # Supabase에서 실시간 데이터 조회
        stats = supabase_manager.get_task_statistics()
        all_tasks = supabase_manager.get_all_tasks()
        recent_completions = supabase_manager.get_completion_logs(limit=10)
        
        # HTML 대시보드 생성
        dashboard_html = generate_supabase_dashboard(stats, all_tasks, recent_completions)
        
        logger.info(f"📊 대시보드 생성 완료 - 업무 {stats['total_tasks']}개")
        
        return HTMLResponse(content=dashboard_html, media_type="text/html; charset=utf-8")
        
    except Exception as e:
        logger.error(f"❌ 대시보드 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"""
            <html><body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1>❌ 대시보드 오류</h1>
                <p>Supabase 연결 또는 데이터 조회 중 오류가 발생했습니다:</p>
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
    """업무 통계 API"""
    try:
        stats = supabase_manager.get_task_statistics()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"API 통계 조회 오류: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/tasks")
def get_all_tasks():
    """모든 업무 조회 API"""
    try:
        tasks = supabase_manager.get_all_tasks()
        return {"success": True, "data": tasks, "count": len(tasks)}
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
