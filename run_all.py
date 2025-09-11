# run_all.py
import argparse, threading, time
import uvicorn
from zoneinfo import ZoneInfo
from datetime import datetime
from webhook import app
from scheduler import start_scheduler
from digest import run_daily_digest
from db import init_schema

KST = ZoneInfo("Asia/Seoul")

def run_uvicorn(host: str, port: int):
    uvicorn.run(app, host=host, port=port, log_level="info")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8510)
    parser.add_argument("--send-now", action="store_true", help="즉시 일일 발송 1회 테스트")
    parser.add_argument("--init-schema", action="store_true", help="스키마 초기화 실행")
    args = parser.parse_args()

    if args.init_schema:
        init_schema()
        print("Schema initialized.")

    t = threading.Thread(target=run_uvicorn, args=(args.host, args.port), daemon=True)
    t.start()
    print(f"[{datetime.now(KST)}] Webhook running on http://{args.host}:{args.port}")

    sched = start_scheduler()

    if args.send_now:
        print(f"[{datetime.now(KST)}] Send-now triggered.")
        run_daily_digest()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        sched.shutdown(wait=False)

if __name__ == "__main__":
    main()
