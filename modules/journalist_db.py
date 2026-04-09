"""
journalist_db.py
출입기자 DB 로드 및 키워드 매칭
파일 없거나 DRM 암호화된 경우 빈 DataFrame 반환
"""
import os
import pandas as pd

DATA_FOLDER = os.path.abspath("data")
JOURNALIST_CSV = os.path.join(DATA_FOLDER, "출입기자_리스트.csv")

# 기대 컬럼 (실제 파일 구조에 맞게 조정)
EXPECTED_COLS = ["name", "media", "beat", "tone", "contact", "last_contact_date", "notes"]


def load_journalist_db() -> pd.DataFrame:
    """출입기자 DB 로드. 실패 시 빈 DataFrame 반환."""
    if not os.path.exists(JOURNALIST_CSV):
        return pd.DataFrame(columns=EXPECTED_COLS)
    try:
        df = pd.read_csv(JOURNALIST_CSV, encoding="utf-8-sig")
        # 컬럼명 정규화 (한글 컬럼명 → 영문 매핑)
        col_map = {}
        for col in df.columns:
            col_lower = col.strip()
            if "이름" in col_lower or "기자" in col_lower:
                col_map[col] = "name"
            elif "언론사" in col_lower or "매체" in col_lower or "소속" in col_lower:
                col_map[col] = "media"
            elif "비트" in col_lower or "beat" in col_lower.lower() or "담당" in col_lower:
                col_map[col] = "beat"
            elif "논조" in col_lower or "성향" in col_lower or "tone" in col_lower.lower():
                col_map[col] = "tone"
            elif "연락" in col_lower or "contact" in col_lower.lower() or "이메일" in col_lower:
                col_map[col] = "contact"
            elif "최근" in col_lower or "날짜" in col_lower or "date" in col_lower.lower():
                col_map[col] = "last_contact_date"
            elif "비고" in col_lower or "notes" in col_lower.lower() or "메모" in col_lower:
                col_map[col] = "notes"
        if col_map:
            df = df.rename(columns=col_map)
        for col in EXPECTED_COLS:
            if col not in df.columns:
                df[col] = ""
        return df[EXPECTED_COLS].fillna("")
    except Exception:
        return pd.DataFrame(columns=EXPECTED_COLS)


def match_journalists(keyword: str, news_items: list[dict], journalist_db: pd.DataFrame) -> pd.DataFrame:
    """키워드·보도 매체 기준으로 출입기자 매칭"""
    if journalist_db.empty:
        return pd.DataFrame(columns=EXPECTED_COLS)

    news_media_set = {item.get("media_name", "") for item in news_items}
    news_media_set.discard("")

    media_matched = journalist_db[journalist_db["media"].isin(news_media_set)]

    beat_matched = journalist_db[
        journalist_db["beat"].str.contains(keyword, case=False, na=False) |
        journalist_db["notes"].str.contains(keyword, case=False, na=False)
    ]

    return pd.concat([media_matched, beat_matched]).drop_duplicates(subset=["name", "media"]).head(10)
