"""
daily_briefing.py
P-IRIS 일간 뉴스 브리핑 전송 스크립트

매일 아침 08:00 KST (23:00 UTC 전날)에 GitHub Actions에서 실행.
전날(KST 기준) 수집된 기사를 요약하여 텔레그램으로 2개 메시지 전송:
  - 메시지 1: 헤더 + 리스크(부정) 기사 전체
  - 메시지 2: 긍정 기사 TOP5 + 키워드별 통계
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from html import escape

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── 상수 ──────────────────────────────────────────────────────────────
KST = timezone(timedelta(hours=9))
DATA_FOLDER = os.path.abspath("data")
NEWS_DB_FILE = os.path.join(DATA_FOLDER, "news_monitor.csv")

WEEKDAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]

# 표시 이름 및 그룹핑 순서
KEYWORD_DISPLAY = {
    "포스코인터내셔널": "포스코인터내셔널",
    "POSCO INTERNATIONAL": "포스코인터내셔널",
    "POSCO International": "포스코인터내셔널",
    "posco international": "포스코인터내셔널",
    "포스코인터": "포스코인터내셔널",
    "삼척블루파워": "삼척블루파워",
    "포스코모빌리티솔루션": "포스코모빌리티솔루션",
    "포스코플로우": "포스코플로우",
    "구동모터코아": "구동모터코아",
    "구동모터코어": "구동모터코아",
    "미얀마 LNG": "미얀마 LNG",
    "포스코": "포스코",
}

# 키워드 표시 순서 (중요도 순)
KEYWORD_ORDER = [
    "포스코인터내셔널",
    "삼척블루파워",
    "포스코모빌리티솔루션",
    "포스코플로우",
    "구동모터코아",
    "미얀마 LNG",
    "포스코",
]

MAX_NEG_ARTICLES = 15   # 부정 기사 최대 표시 수
MAX_POS_ARTICLES = 5    # 긍정 기사 최대 표시 수
MAX_TITLE_LEN = 52      # 기사 제목 최대 길이 (자르기 기준)
DIVIDER = "━━━━━━━━━━━━━━━━━━━━"


# ── 유틸 ──────────────────────────────────────────────────────────────

def _trunc(text: str, n: int = MAX_TITLE_LEN) -> str:
    text = text.strip()
    return text[:n] + "…" if len(text) > n else text


def _hashtag(keyword: str) -> str:
    display = KEYWORD_DISPLAY.get(keyword, keyword)
    return f"#{display.replace(' ', '')}"


def _group(keyword: str) -> str:
    # 대소문자 무관 매칭
    result = KEYWORD_DISPLAY.get(keyword)
    if result:
        return result
    result = KEYWORD_DISPLAY.get(keyword.upper())
    if result:
        return result
    result = KEYWORD_DISPLAY.get(keyword.lower())
    if result:
        return result
    return keyword


def _date_display(date_str: str) -> str:
    """'2026-04-16 18:32' → '04-16 18:32'"""
    s = str(date_str).strip()
    if len(s) >= 16:
        return s[5:16]
    return s


# ── 데이터 로드 ───────────────────────────────────────────────────────

def load_news_db() -> pd.DataFrame:
    if not os.path.exists(NEWS_DB_FILE):
        return pd.DataFrame()
    try:
        df = pd.read_csv(NEWS_DB_FILE, encoding="utf-8")
        if "sentiment" not in df.columns:
            df["sentiment"] = "pos"
        return df
    except Exception as e:
        print(f"[ERROR] DB 로드 실패: {e}")
        return pd.DataFrame()


def get_yesterday_articles(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """
    어제(KST 기준) 기사 필터링.
    Returns: (filtered_df, 'YYYY-MM-DD')
    """
    now_kst = datetime.now(KST)
    yesterday_kst = (now_kst - timedelta(days=1)).strftime("%Y-%m-%d")

    if df.empty:
        return pd.DataFrame(), yesterday_kst

    df = df.copy()
    df["_dt"] = pd.to_datetime(df["날짜"], errors="coerce")
    mask = df["_dt"].dt.strftime("%Y-%m-%d") == yesterday_kst
    result = df[mask].drop(columns=["_dt"]).copy()
    return result, yesterday_kst


# ── 메시지 빌더 ───────────────────────────────────────────────────────

def _header(date_str: str, total: int, neg: int, pos: int) -> str:
    """공통 헤더 블록 생성"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        display_date = f"{dt.year}년 {dt.month:02d}월 {dt.day:02d}일 ({WEEKDAYS_KO[dt.weekday()]})"
    except Exception:
        display_date = date_str

    lines = [
        f"<b>📋 P-IRIS 모닝 브리핑</b>",
        f"<i>{display_date} · 어제 기사 {total}건</i>",
        DIVIDER,
    ]

    if total == 0:
        lines.append("수집된 기사가 없습니다.")
        return "\n".join(lines)

    # 감성 분포 바 (10칸)
    neg_blocks = round(neg / total * 10) if total else 0
    pos_blocks = 10 - neg_blocks
    bar = "🔴" * neg_blocks + "🟢" * pos_blocks
    lines.append(bar)
    lines.append(f"🔴 리스크 {neg}건   🟢 긍정·중립 {pos}건")

    return "\n".join(lines)


def _article_block(idx: int, row: pd.Series, show_sentiment_tag: bool = False) -> str:
    """기사 한 건의 포맷 블록"""
    title = escape(_trunc(str(row.get("기사제목", "제목 없음"))))
    press = escape(str(row.get("매체명", "")).strip())
    url = str(row.get("URL", "")).strip()
    kw = str(row.get("검색키워드", "")).strip()
    date_val = _date_display(row.get("날짜", ""))
    tag = _hashtag(kw)

    # 제목에 링크 임베드
    title_linked = f'<a href="{url}">{title}</a>' if url else title

    # nan 처리
    if press.lower() == "nan":
        press = ""
    press_tag = f"[{press}]  " if press else ""

    lines = [
        f"",
        f"<b>{idx}.</b> <b>{tag}</b>",
        f"   {press_tag}{title_linked}",
    ]
    if date_val:
        lines.append(f"   🕐 {date_val}")

    return "\n".join(lines)


def build_message_risk(df: pd.DataFrame, date_str: str) -> str:
    """
    메시지 1: 헤더 + 리스크(부정) 기사
    부정 기사가 없으면 안심 메시지 출력.
    """
    total = len(df)
    neg_df = df[df["sentiment"] == "neg"].copy() if not df.empty else pd.DataFrame()
    pos_df = df[df["sentiment"] != "neg"].copy() if not df.empty else pd.DataFrame()
    neg_count = len(neg_df)
    pos_count = len(pos_df)

    blocks = [_header(date_str, total, neg_count, pos_count)]

    if total == 0:
        blocks.append("\n🛡️ <i>P-IRIS · 포스코인터내셔널 언론대응 시스템</i>")
        return "\n".join(blocks)

    blocks.append("")

    # ── 부정 기사 섹션 ──
    if neg_df.empty:
        blocks.append(DIVIDER)
        blocks.append("✅ <b>오늘 대응이 필요한 리스크 기사 없음</b>")
        blocks.append(DIVIDER)
        blocks.append("<i>전날 부정 기사가 감지되지 않았습니다.</i>")
    else:
        blocks.append(DIVIDER)
        blocks.append(f"🔴 <b>대응 필요 기사 ({neg_count}건)</b>")
        blocks.append(DIVIDER)

        neg_sorted = neg_df.sort_values("날짜", ascending=False)
        for i, (_, row) in enumerate(neg_sorted.head(MAX_NEG_ARTICLES).iterrows(), 1):
            blocks.append(_article_block(i, row))

        if neg_count > MAX_NEG_ARTICLES:
            blocks.append(f"\n<i>… 외 {neg_count - MAX_NEG_ARTICLES}건 더 있음</i>")

    return "\n".join(blocks)


def build_message_summary(df: pd.DataFrame) -> str:
    """
    메시지 2: 긍정 기사 TOP5 + 키워드별 통계
    """
    if df.empty:
        return ""

    pos_df = df[df["sentiment"] != "neg"].copy()
    blocks = []

    # ── 긍정 기사 TOP5 ──
    if not pos_df.empty:
        blocks.append(DIVIDER)
        blocks.append(f"🟢 <b>주목할 기사 TOP {min(MAX_POS_ARTICLES, len(pos_df))}</b>")
        blocks.append(DIVIDER)

        pos_sorted = pos_df.sort_values("날짜", ascending=False)
        for i, (_, row) in enumerate(pos_sorted.head(MAX_POS_ARTICLES).iterrows(), 1):
            blocks.append(_article_block(i, row))

    # ── 키워드별 통계 ──
    blocks.append("")
    blocks.append(DIVIDER)
    blocks.append("📊 <b>키워드별 현황</b>")
    blocks.append(DIVIDER)

    # 그룹핑
    df = df.copy()
    df["_group"] = df["검색키워드"].apply(_group)
    stats = (
        df.groupby("_group")
        .agg(total=("기사제목", "count"), neg=("sentiment", lambda x: (x == "neg").sum()))
        .reset_index()
    )

    # KEYWORD_ORDER 순으로 정렬
    stats["_order"] = stats["_group"].apply(
        lambda g: KEYWORD_ORDER.index(g) if g in KEYWORD_ORDER else 999
    )
    stats = stats.sort_values("_order")

    max_total = stats["total"].max() if not stats.empty else 1

    for _, row in stats.iterrows():
        kw = row["_group"]
        t = int(row["total"])
        n = int(row["neg"])
        tag = f"#{kw.replace(' ', '')}"

        # 미니 바 (8칸)
        filled = max(1, round(t / max_total * 8)) if t > 0 else 0
        bar = "█" * filled + "░" * (8 - filled)

        neg_tag = f"  <b>🔴 {n}건</b>" if n > 0 else ""
        blocks.append(f"<code>{bar}</code>  <b>{tag}</b>  {t}건{neg_tag}")

    blocks.append("")
    blocks.append(DIVIDER)
    blocks.append("🛡️ <i>P-IRIS · 포스코인터내셔널 언론대응 시스템</i>")

    return "\n".join(blocks)


# ── 전송 ──────────────────────────────────────────────────────────────

def send_telegram(text: str, bot_token: str, chat_id: str) -> bool:
    if not text.strip():
        return True
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        resp = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=(5, 15),
        )
        if resp.status_code == 200:
            print(f"[OK] 전송 성공 ({len(text)}자)")
            return True
        print(f"[ERROR] 전송 실패 {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"[ERROR] 전송 예외: {e}")
        return False


# ── 진입점 ────────────────────────────────────────────────────────────

def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        print("[ERROR] TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 환경변수 없음")
        return

    df_all = load_news_db()
    df_yesterday, yesterday_str = get_yesterday_articles(df_all)

    print(f"[INFO] 브리핑 대상: {yesterday_str} · {len(df_yesterday)}건")

    msg1 = build_message_risk(df_yesterday, yesterday_str)
    msg2 = build_message_summary(df_yesterday)

    ok1 = send_telegram(msg1, bot_token, chat_id)
    if ok1 and msg2:
        time.sleep(1)
        send_telegram(msg2, bot_token, chat_id)

    print("[INFO] 일간 브리핑 전송 완료")


if __name__ == "__main__":
    main()
