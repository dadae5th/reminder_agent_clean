from scheduler import start_scheduler
from datetime import datetime
from zoneinfo import ZoneInfo
import time

kst = ZoneInfo('Asia/Seoul')
now = datetime.now(kst)
print(f'현재 시간 (KST): {now.strftime("%Y-%m-%d %H:%M:%S")}')

print('스케줄러 시작...')
sched = start_scheduler()

# 다음 실행 시간 확인
jobs = sched.get_jobs()
if jobs:
    next_run = jobs[0].next_run_time
    print(f'다음 메일 발송 예정 시간: {next_run.strftime("%Y-%m-%d %H:%M:%S")}')

print('스케줄러가 백그라운드에서 실행 중입니다.')
print('Ctrl+C로 종료할 수 있습니다.')

try:
    while True:
        time.sleep(60)  # 1분마다 체크
        now = datetime.now(kst)
        if now.second == 0:  # 매 분의 시작에만 출력
            print(f'현재 시간: {now.strftime("%H:%M:%S")}')
except KeyboardInterrupt:
    print('\n스케줄러 종료됨')
    sched.shutdown()
