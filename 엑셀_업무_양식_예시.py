# 엑셀_업무_양식_예시.py - 엑셀 양식 생성 도구
import pandas as pd

def create_excel_template():
    """업무 관리용 엑셀 템플릿 생성"""
    
    # 샘플 데이터
    sample_data = [
        {
            "제목": "일일 이메일 확인",
            "담당자": "배재권", 
            "주기": "daily",
            "이메일": "bae.jae.kwon@drbworld.com"
        },
        {
            "제목": "주간 회의 자료 준비",
            "담당자": "배재권",
            "주기": "weekly", 
            "이메일": "bae.jae.kwon@drbworld.com"
        },
        {
            "제목": "월간 성과 보고서 작성",
            "담당자": "배재권",
            "주기": "monthly",
            "이메일": "bae.jae.kwon@drbworld.com"
        },
        {
            "제목": "시스템 백업 확인",
            "담당자": "김철수",
            "주기": "daily",
            "이메일": "kim.chulsoo@company.com"
        },
        {
            "제목": "보안 점검",
            "담당자": "이영희",
            "주기": "weekly",
            "이메일": "lee.younghee@company.com"
        }
    ]
    
    # DataFrame 생성
    df = pd.DataFrame(sample_data)
    
    # 엑셀 파일로 저장
    file_name = "업무_관리_템플릿.xlsx"
    df.to_excel(file_name, index=False, engine='openpyxl')
    
    print(f"✅ 엑셀 템플릿 생성 완료: {file_name}")
    print("\n📋 컬럼 설명:")
    print("   - 제목: 업무/작업의 제목 (필수)")
    print("   - 담당자: 업무 담당자 이름 (필수)")
    print("   - 주기: daily/weekly/monthly 또는 일/주/월 (필수)")
    print("   - 이메일: 담당자 이메일 주소 (선택, 없으면 자동 생성)")
    
    print(f"\n🎯 사용법:")
    print(f"1. {file_name} 파일을 열어서 데이터 수정")
    print(f"2. 필요한 업무들을 추가/수정")
    print(f"3. 저장 후 import_from_excel.py로 가져오기")
    
    return file_name

def show_format_rules():
    """양식 작성 규칙 안내"""
    print("📝 엑셀 파일 작성 규칙")
    print("=" * 50)
    
    print("\n🔥 필수 컬럼:")
    print("   1. 제목 - 업무나 작업의 제목")
    print("   2. 담당자 - 업무를 담당할 사람 이름")
    print("   3. 주기 - 업무 반복 주기")
    
    print("\n⏰ 주기 입력 방법:")
    print("   - 매일: 'daily', '일', '매일' 중 아무거나")
    print("   - 주간: 'weekly', '주', '매주' 중 아무거나") 
    print("   - 월간: 'monthly', '월', '매월' 중 아무거나")
    
    print("\n📧 이메일 컬럼 (선택사항):")
    print("   - 있으면: 해당 이메일로 알림 발송")
    print("   - 없으면: 담당자명으로 자동 생성")
    print("   - 예: '김철수' → 'kim.chulsoo@company.com'")
    
    print("\n⚠️ 주의사항:")
    print("   - 첫 번째 행은 반드시 컬럼명(헤더)이어야 함")
    print("   - 빈 행은 자동으로 무시됨")
    print("   - 한글 컬럼명 사용 가능")
    print("   - 컬럼 순서는 상관없음")

if __name__ == "__main__":
    print("🚀 엑셀 업무 양식 도구")
    print("=" * 30)
    
    choice = input("\n1. 템플릿 생성\n2. 양식 규칙 보기\n선택 (1 또는 2): ")
    
    if choice == "1":
        create_excel_template()
    elif choice == "2":
        show_format_rules()
    else:
        print("올바른 선택이 아닙니다.")
