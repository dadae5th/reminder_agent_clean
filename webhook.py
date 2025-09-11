# webhook.py (server version)
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from db import mark_done_by_token
import yaml
from urllib.parse import urlparse

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
def complete_task(token: str, next: str | None = None):
    ok = mark_done_by_token(token)
    if ok:
        target = _pick_target(next, _cfg().get("dashboard_url"))
        if target:
            return RedirectResponse(url=target, status_code=303)
        return HTMLResponse("완료되었습니다. config.yaml에 dashboard_url을 지정하면 자동 이동합니다.")
    return HTMLResponse("이미 완료되었거나 토큰이 유효하지 않습니다.", status_code=400)
