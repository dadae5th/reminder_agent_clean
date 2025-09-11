# digest.py
from datetime import datetime
from zoneinfo import ZoneInfo
import yaml
from db import all_recipients, active_tasks_for_today, get_conn
from mailer import make_token, build_task_url, send_email

KST = ZoneInfo("Asia/Seoul")

def _load_cfg():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def html_for_tasks(tasks, base_url, dashboard_url=None):
    if not tasks:
        return None
    rows = []
    for t in tasks:
        token = t["hmac_token"]
        if not token:
            token = make_token(t["id"])
            with get_conn() as conn:
                conn.execute("UPDATE tasks SET hmac_token=? WHERE id=?", (token, t["id"]))
        url = build_task_url(base_url, token)
        if dashboard_url:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}next={dashboard_url}"
        badge = {"daily":"일간", "weekly":"주간", "monthly":"월간"}.get(t["frequency"], t["frequency"])
        rows.append(f"""
          <tr>
            <td style="padding:8px;border:1px solid #ddd;">
              <div style="font-weight:600">{t['title']}</div>
              <div style="font-size:12px;color:#666;">주기: {badge}</div>
            </td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center;">
              <a href="{url}" style="padding:6px 10px;border-radius:6px;border:1px solid #222;text-decoration:none;">
                완료
              </a>
            </td>
          </tr>
        """)
    table = f"""
      <table style="border-collapse:collapse;width:100%;font-family:Arial,Apple SD Gothic Neo,Malgun Gothic;">
        <thead>
          <tr>
            <th style="padding:8px;border:1px solid #ddd;background:#f5f5f5;text-align:left;">업무</th>
            <th style="padding:8px;border:1px solid #ddd;background:#f5f5f5;text-align:center;">액션</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    """
    now_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    return f"""
      <div style="font-family:Arial,Apple SD Gothic Neo,Malgun Gothic;max-width:680px;margin:auto;">
        <h2 style="margin-bottom:8px;">오늘의 해야할 일</h2>
        <div style="color:#666;margin-bottom:16px;">생성 시각: {now_str} (KST)</div>
        {table}
        <p style="color:#666;font-size:12px;margin-top:12px">
          * 완료 버튼을 클릭하면 이번 사이클에서 제외되고 대시보드에 즉시 반영됩니다.
        </p>
      </div>
    """

def run_daily_digest():
    cfg = _load_cfg()
    base_url = cfg["base_url"]
    dashboard_url = cfg.get("dashboard_url")
    mail_cfg = cfg["smtp"]

    recipients = all_recipients()
    for r in recipients:
        tasks = active_tasks_for_today(r)
        html = html_for_tasks(tasks, base_url, dashboard_url)
        if html:
            send_email(
                smtp_host=mail_cfg["host"],
                smtp_port=mail_cfg["port"],
                smtp_id=mail_cfg["user"],
                smtp_pw=mail_cfg["pass"],
                sender_name=mail_cfg["sender_name"],
                sender_email=mail_cfg["sender_email"],
                to_email=r,
                subject="[일일 알림] 오늘의 해야할 일",
                html_body=html
            )
