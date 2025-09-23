# scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from zoneinfo import ZoneInfo
from datetime import datetime
from send_digest_supabase import run_daily_digest  # Supabase 버전 사용

KST = ZoneInfo("Asia/Seoul")

def start_scheduler():
    sched = BackgroundScheduler(timezone=str(KST))
    sched.add_job(run_daily_digest, "cron", hour=9, minute=0, id="daily_all_cycles")  # 09:00 KST
    sched.start()
    print(f"[{datetime.now(KST)}] Scheduler started.")
    return sched
