@echo off
cd /d "c:\Users\kimwoss\Desktop\Risk_managemnt_proj\ai_commsystem"
call .venv\Scripts\activate
echo 가상환경이 활성화되었습니다!
echo.
echo 사용 가능한 명령어:
echo   python main.py           - 메인 분석 시스템 실행
echo   python build_index.py    - FAISS 인덱스 생성
echo   python search.py         - 유사도 검색 실행
echo   python search.py "검색어" - 특정 검색어로 검색
echo.
cmd /k
