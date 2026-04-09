"""
response_history.py
대응이력 DB 로드 및 키워드 검색
실제 파일: data/언론대응내역.csv
컬럼: 순번, 발생 일시, 발생 유형, 현업 부서, 단계, 이슈 발생 보고, 대응 결과
"""
import os
import pandas as pd

DATA_FOLDER = os.path.abspath("data")
HISTORY_CSV = os.path.join(DATA_FOLDER, "언론대응내역.csv")

# 정규화 후 컬럼명
NORM_COLS = ["id", "date", "issue_type", "department", "crisis_level", "summary", "result"]


def load_response_history() -> pd.DataFrame:
    """대응이력 DB 로드. 실패 시 빈 DataFrame 반환."""
    if not os.path.exists(HISTORY_CSV):
        return pd.DataFrame(columns=NORM_COLS)
    try:
        df = pd.read_csv(HISTORY_CSV, encoding="utf-8-sig")
        # 컬럼 정규화
        col_map = {}
        for col in df.columns:
            c = col.strip()
            if "순번" in c:
                col_map[col] = "id"
            elif "일시" in c or "날짜" in c:
                col_map[col] = "date"
            elif "유형" in c:
                col_map[col] = "issue_type"
            elif "부서" in c:
                col_map[col] = "department"
            elif "단계" in c or "위기" in c:
                col_map[col] = "crisis_level"
            elif "보고" in c or "이슈" in c or "제목" in c or "summary" in c.lower():
                col_map[col] = "summary"
            elif "결과" in c or "result" in c.lower():
                col_map[col] = "result"
        if col_map:
            df = df.rename(columns=col_map)
        for col in NORM_COLS:
            if col not in df.columns:
                df[col] = ""
        return df[NORM_COLS].fillna("")
    except Exception:
        return pd.DataFrame(columns=NORM_COLS)


def search_response_history(keyword: str, history_db: pd.DataFrame, top_k: int = 5) -> pd.DataFrame:
    """키워드로 대응이력 검색"""
    if history_db.empty:
        return pd.DataFrame(columns=NORM_COLS)

    mask = (
        history_db["summary"].str.contains(keyword, case=False, na=False) |
        history_db["result"].str.contains(keyword, case=False, na=False) |
        history_db["issue_type"].str.contains(keyword, case=False, na=False)
    )
    result = history_db[mask].copy()
    result = result.sort_values("date", ascending=False).head(top_k)
    return result
