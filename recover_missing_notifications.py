"""
누락된 텔레그램 알림 복구 스크립트

DB에는 있지만 캐시에 없는 기사들을 찾아서 텔레그램으로 전송합니다.
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
from news_collector import (
    load_news_db,
    load_sent_cache,
    save_sent_cache,
    send_telegram_notification,
    _normalize_url,
    _publisher_from_link
)

def main():
    print("=" * 80)
    print("[RECOVERY] 누락된 텔레그램 알림 복구 시작")
    print("=" * 80)

    # DB 및 캐시 로드
    db = load_news_db()
    sent_cache = load_sent_cache()

    print(f"[RECOVERY] DB 로드: {len(db)}건")
    print(f"[RECOVERY] 캐시 로드: {len(sent_cache)}건")

    # DB에 있지만 캐시에 없는 기사 찾기
    missing_articles = []
    KST = timezone(timedelta(hours=9))
    now = datetime.now(KST).replace(tzinfo=None)
    MAX_DAYS = 7  # 최근 7일 이내 기사만 복구

    for _, row in db.iterrows():
        url = str(row.get("URL", "")).strip()
        if not url or url == "nan" or url == "":
            continue

        url_normalized = _normalize_url(url)

        # 캐시에 없는 기사 확인
        if url not in sent_cache and url_normalized not in sent_cache:
            # 날짜 확인 (최근 7일 이내)
            article_date_str = row.get("날짜", "")
            try:
                article_date = pd.to_datetime(article_date_str, errors="coerce")
                if pd.notna(article_date):
                    time_diff = now - article_date
                    days_diff = time_diff.total_seconds() / 86400

                    if days_diff <= MAX_DAYS:
                        title = str(row.get("기사제목", "")).strip()
                        press = _publisher_from_link(url)
                        keyword = str(row.get("검색키워드", "")).strip()

                        missing_articles.append({
                            "title": title,
                            "link": url,
                            "date": article_date_str,
                            "press": press,
                            "keyword": keyword,
                            "days_ago": days_diff
                        })
                        print(f"[RECOVERY] 누락 발견: {title[:50]}... ({days_diff:.1f}일 전)")
            except Exception as e:
                print(f"[RECOVERY] 날짜 처리 오류: {e}")
                continue

    print(f"\n[RECOVERY] 총 {len(missing_articles)}건의 누락된 기사 발견")

    if missing_articles:
        # 날짜순 정렬 (최신순)
        missing_articles.sort(key=lambda x: x['days_ago'])

        print(f"[RECOVERY] 텔레그램 알림 전송 시작...")

        # 텔레그램 전송
        sent_cache = send_telegram_notification(missing_articles, sent_cache)

        # 캐시 저장
        save_sent_cache(sent_cache)

        print(f"[RECOVERY] ✅ 복구 완료: {len(missing_articles)}건 전송")
    else:
        print(f"[RECOVERY] ℹ️ 누락된 기사가 없습니다.")

    print("=" * 80)
    print("[RECOVERY] 복구 작업 종료")
    print("=" * 80)

if __name__ == "__main__":
    main()
