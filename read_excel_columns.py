import pandas as pd

# 엑셀 파일 경로
file_path = "해야 할 일 체크리스트.xlsx"

# 엑셀 파일 읽기
try:
    xl = pd.ExcelFile(file_path)
    sheet_name = xl.sheet_names[0]  # 첫 번째 시트 선택
    df = xl.parse(sheet_name)

    # 열 이름 출력
    print("엑셀 시트의 열 이름:")
    for col in df.columns:
        print(col)
except Exception as e:
    print(f"엑셀 파일을 읽는 중 오류 발생: {e}")
