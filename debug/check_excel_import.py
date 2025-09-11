import pandas as pd

def check_excel_import():
    # 엑셀 파일 읽기
    file_path = "해야 할 일 체크리스트.xlsx"
    xl = pd.ExcelFile(file_path)
    sheet_name = xl.sheet_names[0]
    df = pd.read_excel(xl, sheet_name)
    
    # 담당자 컬럼의 모든 고유 값 출력
    print("=== 엑셀 파일의 고유한 담당자 목록 ===")
    unique_assignees = df['담당자'].unique()
    for assignee in unique_assignees:
        count = len(df[df['담당자'] == assignee])
        print(f"담당자: {assignee}, 업무 수: {count}")
    
    # 생산기술팀 관련 업무 상세 출력
    print("\n=== 생산기술팀 담당 업무 ===")
    tech_team_tasks = df[df['담당자'] == '생산기술팀']
    for _, row in tech_team_tasks.iterrows():
        print(f"업무명: {row['업무명']}")
        print(f"주기: {row['주기']}")
        print("---")

if __name__ == "__main__":
    check_excel_import()
