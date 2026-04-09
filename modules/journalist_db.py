"""
journalist_db.py
출입기자 DB 로드 및 키워드 매칭

실제 파일: data/출입기자_리스트.csv (EUC-KR)
구조 (실측):
  rows 0~8:  메타/헤더 (스킵)
  row 9~:    데이터
  col 0: 구분(종합지·경제지 등)   — ffill
  col 1: 순번
  col 2: 언론사명                 — ffill
  col 3: 출입기자(이름)
  col 4: 직급/비트
  col 5: Mobile
  col 6: E-MAIL
"""
import os
import pandas as pd

DATA_FOLDER = os.path.abspath("data")
JOURNALIST_CSV = os.path.join(DATA_FOLDER, "출입기자_리스트.csv")

NORM_COLS = ["name", "media", "beat", "tone", "contact", "email", "category"]


def load_journalist_db() -> pd.DataFrame:
    """출입기자 DB 로드. 실패 시 빈 DataFrame 반환."""
    if not os.path.exists(JOURNALIST_CSV):
        return pd.DataFrame(columns=NORM_COLS)
    try:
        # rows 0~8 스킵 (메타+헤더), 헤더 없이 위치 기반으로 읽기
        df = pd.read_csv(
            JOURNALIST_CSV,
            encoding="euc-kr",
            skiprows=9,
            header=None,
            on_bad_lines="skip",
        )

        # 위치 기반 컬럼 추출
        def _col(idx):
            return df[idx] if idx in df.columns else pd.Series([""] * len(df))

        result = pd.DataFrame()
        result["category"] = _col(0).replace("", pd.NA).ffill().fillna("")
        result["media"]    = _col(2).replace("", pd.NA).ffill().fillna("")
        result["name"]     = _col(3).fillna("")
        result["beat"]     = _col(4).fillna("")
        result["contact"]  = _col(5).fillna("")
        result["email"]    = _col(6).fillna("")
        result["tone"]     = "중립"

        # 이름이 없는 행 제거
        result["name"] = result["name"].astype(str).str.strip()
        result = result[result["name"].notna()]
        result = result[~result["name"].isin(["", "nan", "출입기자", "NaN"])]
        result = result.reset_index(drop=True)

        return result[NORM_COLS]

    except Exception as e:
        print(f"[journalist_db] 로드 실패: {e}")
        return pd.DataFrame(columns=NORM_COLS)


def match_journalists(keyword: str, news_items: list[dict], journalist_db: pd.DataFrame) -> pd.DataFrame:
    """키워드·보도 매체 기준으로 출입기자 매칭"""
    if journalist_db.empty:
        return pd.DataFrame(columns=NORM_COLS)

    news_media_set = {item.get("media_name", "") for item in news_items}
    news_media_set.discard("")

    media_matched = journalist_db[journalist_db["media"].isin(news_media_set)]
    beat_matched  = journalist_db[
        journalist_db["beat"].str.contains(keyword, case=False, na=False)
    ]

    combined = pd.concat([media_matched, beat_matched]).drop_duplicates(subset=["name", "media"])
    return combined.head(10)
