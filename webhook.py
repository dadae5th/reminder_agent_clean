# webhook.py (server version)
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from typing import List, Optional
from db import mark_done_by_token, get_task_by_token
import yaml
from urllib.parse import urlparse
from datetime import datetime
import os

app = FastAPI()

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

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/complete")
def complete_task(token: str, next: Optional[str] = None):
    ok = mark_done_by_token(token)
    if ok:
        target = _pick_target(next, _cfg().get("dashboard_url"))
        if target:
            return RedirectResponse(url=target, status_code=303)
        return HTMLResponse("완료되었습니다. config.yaml에 dashboard_url을 지정하면 자동 이동합니다.")
    return HTMLResponse("이미 완료되었거나 토큰이 유효하지 않습니다.", status_code=400)

@app.post("/complete-tasks")
async def complete_multiple_tasks(request: Request):
    form_data = await request.form()
    tasks = form_data.getlist("tasks")  # 체크박스에서 선택된 모든 값 가져오기
    
    print(f"[DEBUG] 받은 태스크 토큰들: {tasks}")  # 디버그 로그
    
    completed = []
    for token in tasks:
        print(f"[DEBUG] 토큰 처리 중: {token}")  # 디버그 로그
        if mark_done_by_token(token):
            task = get_task_by_token(token)
            if task:
                completed.append(task['title'])
                print(f"[DEBUG] 완료됨: {task['title']}")  # 디버그 로그
            else:
                print(f"[DEBUG] 토큰에 해당하는 태스크 없음: {token}")  # 디버그 로그
        else:
            print(f"[DEBUG] 완료 처리 실패: {token}")  # 디버그 로그
    
    print(f"[DEBUG] 완료된 업무들: {completed}")  # 디버그 로그
    
    target = _cfg().get("dashboard_url")
    print(f"[DEBUG] 리다이렉트 대상: {target}")  # 디버그 로그
    
    if target:
        return RedirectResponse(url=target, status_code=303)
    
    message = f"완료된 업무: {', '.join(completed)}" if completed else "완료된 업무가 없습니다."
    return HTMLResponse(f"{message}<br>config.yaml에 dashboard_url을 지정하면 자동 이동합니다.")

@app.get("/dashboard")
async def serve_dashboard():
    """동적으로 대시보드를 생성하여 반환"""
    try:
        from generate_dashboard import generate_dashboard
        
        # 동적으로 대시보드 HTML 생성
        dashboard_html = generate_dashboard()
        
        print(f"[DEBUG] 생성된 HTML 길이: {len(dashboard_html)}")  # 디버그 로그
        print(f"[DEBUG] HTML 시작: {dashboard_html[:100]}...")  # 디버그 로그
        
        return HTMLResponse(content=dashboard_html, media_type="text/html; charset=utf-8")
    except Exception as e:
        print(f"[ERROR] 대시보드 생성 오류: {e}")  # 에러 로그
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"<h1>대시보드 생성 오류</h1><p>{str(e)}</p>", status_code=500)

@app.get("/send-test-email")
async def send_test_email():
    """이메일 발송 테스트 엔드포인트"""
    try:
        from digest import run_daily_digest
        print("[DEBUG] 이메일 발송 시작...")
        
        result = run_daily_digest()
        print(f"[DEBUG] 이메일 발송 결과: {result}")
        
        return HTMLResponse(f"""
        <html>
        <body>
        <h2>📧 이메일 발송 테스트</h2>
        <p>✅ 이메일 발송 완료!</p>
        <p>📬 bae.jae.kwon@drbworld.com으로 이메일을 확인하세요.</p>
        <p>📦 스팸 폴더도 확인해보세요.</p>
        <br>
        <a href="/dashboard">📊 대시보드로 이동</a>
        </body>
        </html>
        """)
    except Exception as e:
        print(f"[ERROR] 이메일 발송 오류: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"""
        <html>
        <body>
        <h2>❌ 이메일 발송 실패</h2>
        <p>오류: {str(e)}</p>
        <a href="/dashboard">📊 대시보드로 이동</a>
        </body>
        </html>
        """, status_code=500)
