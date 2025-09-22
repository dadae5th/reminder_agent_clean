# create_sample_tasks.py - 샘플 업무 40개 생성
import sqlite3
from datetime import datetime
from contextlib import contextmanager

@contextmanager
def get_conn():
    conn = sqlite3.connect("reminder.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def create_sample_tasks():
    """40개의 샘플 업무 생성"""
    
    # 일일 업무 (20개)
    daily_tasks = [
        "이메일 확인 및 답장", "일일 스탠드업 미팅 참석", "프로젝트 진행상황 업데이트",
        "코드 리뷰 진행", "버그 리포트 확인", "팀 슬랙 메시지 확인", 
        "일일 업무 계획 수립", "고객 문의 응답", "데일리 백업 확인",
        "시스템 모니터링 체크", "일일 매출 확인", "팀 진행상황 공유",
        "개발 환경 점검", "보안 로그 확인", "데이터베이스 상태 체크",
        "서버 성능 모니터링", "고객 피드백 정리", "일일 KPI 확인",
        "업무 우선순위 재정렬", "내일 일정 계획"
    ]
    
    # 주간 업무 (15개)
    weekly_tasks = [
        "주간 회의 자료 준비", "팀 성과 리포트 작성", "주간 프로젝트 리뷰",
        "클라이언트 미팅 준비", "주간 마케팅 분석", "경쟁사 동향 조사",
        "팀 교육 계획 수립", "주간 예산 검토", "신규 기능 기획",
        "품질 보증 테스트", "주간 운영 리포트", "파트너사 연락",
        "주간 인벤토리 확인", "팀빌딩 활동 계획", "주간 보안 점검"
    ]
    
    # 월간 업무 (5개)
    monthly_tasks = [
        "월간 리포트 작성", "월간 예산 계획", "직원 성과 평가",
        "월간 전략 회의", "시스템 백업 및 복구 테스트"
    ]
    
    with get_conn() as conn:
        # 기존 테스트 데이터 삭제 (ID 631-633)
        conn.execute("DELETE FROM tasks WHERE id BETWEEN 631 AND 633")
        
        task_id = 1
        
        # 일일 업무 추가
        for task in daily_tasks:
            conn.execute("""
                INSERT INTO tasks (id, title, assignee_email, frequency, status, creator_name)
                VALUES (?, ?, ?, 'daily', 'pending', ?)
            """, (task_id, task, "bae.jae.kwon@drbworld.com", "배재권"))
            task_id += 1
        
        # 주간 업무 추가
        for task in weekly_tasks:
            conn.execute("""
                INSERT INTO tasks (id, title, assignee_email, frequency, status, creator_name)
                VALUES (?, ?, ?, 'weekly', 'pending', ?)
            """, (task_id, task, "bae.jae.kwon@drbworld.com", "배재권"))
            task_id += 1
        
        # 월간 업무 추가
        for task in monthly_tasks:
            conn.execute("""
                INSERT INTO tasks (id, title, assignee_email, frequency, status, creator_name)
                VALUES (?, ?, ?, 'monthly', 'pending', ?)
            """, (task_id, task, "bae.jae.kwon@drbworld.com", "배재권"))
            task_id += 1
        
        print(f"✅ 총 {len(daily_tasks + weekly_tasks + monthly_tasks)}개의 업무가 생성되었습니다!")
        print(f"   - 일일 업무: {len(daily_tasks)}개")
        print(f"   - 주간 업무: {len(weekly_tasks)}개") 
        print(f"   - 월간 업무: {len(monthly_tasks)}개")

if __name__ == "__main__":
    create_sample_tasks()
