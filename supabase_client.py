# supabase_client.py - Supabase 클라이언트 및 데이터베이스 로직
import os
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv
import logging

# 시간대 설정 - 호환성 처리
try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo("Asia/Seoul")
except ImportError:
    from datetime import timezone
    KST = timezone(timedelta(hours=9))

# SSL 우회는 로컬 환경에서만 (회사 네트워크)
try:
    import ssl
    import urllib3
    if os.getenv('GITHUB_ACTIONS') != 'true':  # GitHub Actions가 아닐 때만
        ssl._create_default_https_context = ssl._create_unverified_context
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        os.environ['PYTHONHTTPSVERIFY'] = '0'
except ImportError:
    pass  # urllib3가 없어도 계속 진행

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseManager:
    def __init__(self, use_service_key=False):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.service_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL과 SUPABASE_KEY를 .env 파일에 설정해주세요")
        
        # 마이그레이션 시에는 service_role 키 사용
        selected_key = self.service_key if use_service_key and self.service_key else self.key
        self.supabase: Client = create_client(self.url, selected_key)
        logger.info("✅ Supabase 클라이언트 초기화 완료")
    
    def kst_now(self) -> datetime:
        """현재 한국 시간 반환"""
        return datetime.now(KST)
    
    def cycle_start(self, frequency: str, now: datetime) -> datetime:
        """주기별 시작 시간 계산"""
        d0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if frequency == "daily":
            return d0
        elif frequency == "weekly":
            return d0 - timedelta(days=d0.weekday())
        elif frequency == "monthly":
            return d0.replace(day=1)
        return d0
    
    # ========== 사용자 관리 ==========
    def get_all_users(self) -> List[Dict]:
        """모든 사용자 조회"""
        try:
            response = self.supabase.table('users').select('*').execute()
            return response.data
        except Exception as e:
            logger.error(f"사용자 조회 오류: {e}")
            return []
    
    def add_user(self, email: str, name: str) -> bool:
        """사용자 추가"""
        try:
            data = {
                'email': email,
                'name': name,
                'created_at': self.kst_now().isoformat()
            }
            response = self.supabase.table('users').insert(data).execute()
            logger.info(f"✅ 사용자 추가: {name} ({email})")
            return True
        except Exception as e:
            logger.error(f"사용자 추가 오류: {e}")
            return False
    
    def get_all_recipients(self) -> List[str]:
        """이메일 발송 대상자 목록"""
        users = self.get_all_users()
        return [user['email'] for user in users]
    
    # ========== 업무 관리 ==========
    def get_all_tasks(self) -> List[Dict]:
        """모든 업무 조회"""
        try:
            response = self.supabase.table('tasks').select('*').order('id').execute()
            return response.data
        except Exception as e:
            logger.error(f"업무 조회 오류: {e}")
            return []
    
    def add_task(self, title: str, assignee_email: str, frequency: str, creator_name: str) -> Optional[int]:
        """새 업무 추가"""
        try:
            data = {
                'title': title,
                'assignee_email': assignee_email,
                'frequency': frequency,
                'status': 'pending',
                'creator_name': creator_name,
                'created_at': self.kst_now().isoformat()
            }
            response = self.supabase.table('tasks').insert(data).execute()
            task_id = response.data[0]['id']
            logger.info(f"✅ 업무 추가: {title} (ID: {task_id})")
            return task_id
        except Exception as e:
            logger.error(f"업무 추가 오류: {e}")
            return None
    
    def active_tasks_for_today(self, email: str) -> List[Dict]:
        """오늘 해야 할 활성 업무 조회"""
        now = self.kst_now()
        cs_daily = self.cycle_start("daily", now).isoformat()
        cs_weekly = self.cycle_start("weekly", now).isoformat()
        cs_monthly = self.cycle_start("monthly", now).isoformat()
        
        try:
            # 각 주기별로 미완료 업무 조회
            daily_tasks = self.supabase.table('tasks').select('*').match({
                'assignee_email': email,
                'frequency': 'daily'
            }).or_(f'last_completed_at.is.null,last_completed_at.lt.{cs_daily}').execute()
            
            weekly_tasks = self.supabase.table('tasks').select('*').match({
                'assignee_email': email,
                'frequency': 'weekly'
            }).or_(f'last_completed_at.is.null,last_completed_at.lt.{cs_weekly}').execute()
            
            monthly_tasks = self.supabase.table('tasks').select('*').match({
                'assignee_email': email,
                'frequency': 'monthly'
            }).or_(f'last_completed_at.is.null,last_completed_at.lt.{cs_monthly}').execute()
            
            # 모든 결과 합치기
            all_tasks = []
            all_tasks.extend(daily_tasks.data)
            all_tasks.extend(weekly_tasks.data)
            all_tasks.extend(monthly_tasks.data)
            
            logger.info(f"📋 {email}의 오늘 업무: {len(all_tasks)}개")
            return all_tasks
            
        except Exception as e:
            logger.error(f"활성 업무 조회 오류: {e}")
            return []
    
    def mark_task_completed(self, task_id: int) -> bool:
        """업무를 완료 상태로 변경"""
        try:
            now_iso = self.kst_now().isoformat()
            data = {
                'status': 'done',
                'last_completed_at': now_iso,
                'updated_at': now_iso
            }
            response = self.supabase.table('tasks').update(data).eq('id', task_id).execute()
            
            if response.data:
                logger.info(f"✅ 업무 완료: ID {task_id}")
                
                # 완료 기록 추가
                self.add_completion_log(task_id, now_iso)
                return True
            else:
                logger.warning(f"⚠️ 업무 완료 실패: ID {task_id} (업무를 찾을 수 없음)")
                return False
                
        except Exception as e:
            logger.error(f"업무 완료 처리 오류: {e}")
            return False
    
    def mark_task_completed_by_token(self, token: str) -> bool:
        """토큰으로 업무 완료 처리"""
        try:
            # 토큰으로 업무 찾기
            response = self.supabase.table('tasks').select('*').eq('hmac_token', token).execute()
            
            if not response.data:
                logger.warning(f"⚠️ 토큰에 해당하는 업무 없음: {token}")
                return False
            
            task = response.data[0]
            return self.mark_task_completed(task['id'])
            
        except Exception as e:
            logger.error(f"토큰 기반 업무 완료 오류: {e}")
            return False
    
    def get_task_by_token(self, token: str) -> Optional[Dict]:
        """토큰으로 업무 조회"""
        try:
            response = self.supabase.table('tasks').select('*').eq('hmac_token', token).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"토큰 기반 업무 조회 오류: {e}")
            return None
    
    def update_task_token(self, task_id: int, token: str) -> bool:
        """업무에 토큰 추가"""
        try:
            data = {'hmac_token': token}
            response = self.supabase.table('tasks').update(data).eq('id', task_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"토큰 업데이트 오류: {e}")
            return False
    
    # ========== 완료 기록 관리 ==========
    def add_completion_log(self, task_id: int, completed_at: str) -> bool:
        """업무 완료 기록 추가"""
        try:
            data = {
                'task_id': task_id,
                'completed_at': completed_at,
                'created_at': self.kst_now().isoformat()
            }
            response = self.supabase.table('completion_logs').insert(data).execute()
            logger.info(f"📝 완료 기록 추가: Task ID {task_id}")
            return True
        except Exception as e:
            logger.error(f"완료 기록 추가 오류: {e}")
            return False
    
    def get_completion_logs(self, task_id: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """완료 기록 조회"""
        try:
            query = self.supabase.table('completion_logs').select('*, tasks(*)')
            
            if task_id:
                query = query.eq('task_id', task_id)
            
            response = query.order('completed_at', desc=True).limit(limit).execute()
            return response.data
        except Exception as e:
            logger.error(f"완료 기록 조회 오류: {e}")
            return []
    
    # ========== 통계 및 분석 ==========
    def get_task_statistics(self) -> Dict:
        """업무 통계 조회"""
        try:
            # 전체 업무 수
            total_response = self.supabase.table('tasks').select('id', count='exact').execute()
            total_count = total_response.count
            
            # 완료된 업무 수
            completed_response = self.supabase.table('tasks').select('id', count='exact').eq('status', 'done').execute()
            completed_count = completed_response.count
            
            # 진행 중 업무 수
            pending_response = self.supabase.table('tasks').select('id', count='exact').eq('status', 'pending').execute()
            pending_count = pending_response.count
            
            # 오늘 완료된 업무 수
            today = self.kst_now().date().isoformat()
            today_completed_response = self.supabase.table('completion_logs').select('id', count='exact').gte('completed_at', today).execute()
            today_completed_count = today_completed_response.count
            
            return {
                'total_tasks': total_count,
                'completed_tasks': completed_count,
                'pending_tasks': pending_count,
                'today_completed': today_completed_count
            }
        except Exception as e:
            logger.error(f"통계 조회 오류: {e}")
            return {
                'total_tasks': 0,
                'completed_tasks': 0,
                'pending_tasks': 0,
                'today_completed': 0
            }

# 글로벌 인스턴스
supabase_manager = SupabaseManager()
