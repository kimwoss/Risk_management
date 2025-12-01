"""
Standalone News Monitor - GitHub Actions용
Streamlit 없이 독립적으로 뉴스를 수집하고 텔레그램 알림을 전송합니다.
3분마다 GitHub Actions에서 자동 실행됩니다.
"""
import pandas as pd
from datetime import datetime

# 공통 모듈 import
from news_collector import (
    KEYWORDS,
    EXCLUDE_KEYWORDS,
    MAX_ITEMS_PER_RUN,
    crawl_naver_news,
    load_news_db,
    save_news_db,
    load_sent_cache,
    save_sent_cache,
    detect_new_articles,
    send_telegram_notification,
    _naver_headers,
    _normalize_url,
    load_api_usage,
    increment_api_usage,
    check_api_quota,
    is_first_run,
    mark_initialized,
)

# 키워드 우선순위 정의 (1=최우선, 숫자가 낮을수록 우선순위 높음)
KEYWORD_PRIORITY = {
    "포스코인터내셔널": 1,  # 최우선
    "POSCO INTERNATIONAL": 1,
    "포스코인터": 1,
    "삼척블루파워": 2,
    "포스코모빌리티솔루션": 2,
    "포스코플로우": 2,
    "구동모터코아": 3,
    "구동모터코어": 3,
    "미얀마 LNG": 3,
    "포스코": 4,  # 가장 낮은 우선순위
}

# 로거 import
try:
    from logger import logger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False
    print("[WARNING] logger.py를 찾을 수 없습니다. 로깅 기능이 비활성화됩니다.")


def safe_print(text: str):
    """Windows 콘솔 인코딩 오류 방지"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 이모지 제거하고 재시도
        text_clean = text.encode('ascii', 'ignore').decode('ascii')
        print(text_clean)


def apply_keyword_filters(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """키워드별 필터링 로직 적용"""
    if df.empty:
        return df

    # "포스코인터내셔널" 정확한 매칭
    if keyword == "포스코인터내셔널":
        def should_include(row):
            title = str(row.get("기사제목", ""))
            description = str(row.get("주요기사 요약", ""))
            return "포스코인터내셔널" in title or "포스코인터내셔널" in description

        mask = df.apply(should_include, axis=1)
        df = df[mask].reset_index(drop=True)
        if not df.empty:
            safe_print(f"[MONITOR] '포스코인터내셔널' 정확 매칭: {len(df)}건")

    # "포스코모빌리티솔루션" 정확한 매칭
    elif keyword == "포스코모빌리티솔루션":
        def should_include(row):
            title = str(row.get("기사제목", ""))
            description = str(row.get("주요기사 요약", ""))
            return "포스코모빌리티솔루션" in title or "포스코모빌리티솔루션" in description

        mask = df.apply(should_include, axis=1)
        df = df[mask].reset_index(drop=True)
        if not df.empty:
            safe_print(f"[MONITOR] '포스코모빌리티솔루션' 정확 매칭: {len(df)}건")

    # "포스코플로우" 정확한 매칭
    elif keyword == "포스코플로우":
        def should_include(row):
            title = str(row.get("기사제목", ""))
            description = str(row.get("주요기사 요약", ""))
            return "포스코플로우" in title or "포스코플로우" in description

        mask = df.apply(should_include, axis=1)
        df = df[mask].reset_index(drop=True)
        if not df.empty:
            safe_print(f"[MONITOR] '포스코플로우' 정확 매칭: {len(df)}건")

    # "포스코" 키워드 특별 처리
    elif keyword == "포스코":
        def should_include(row):
            title = str(row.get("기사제목", ""))
            title_lower = title.lower()
            description = str(row.get("주요기사 요약", ""))

            # "포스코" 또는 "posco" 포함 체크
            if "포스코" not in title and "posco" not in title_lower:
                return False

            # 부동산 키워드 제외
            exclude_words = ["청약", "분양", "입주", "재건축", "정비구역", "인테리어"]
            for exclude_word in exclude_words:
                if exclude_word in title or exclude_word in description:
                    return False

            return True

        mask = df.apply(should_include, axis=1)
        df = df[mask].reset_index(drop=True)
        if not df.empty:
            safe_print(f"[MONITOR] '포스코' 필터링 완료: {len(df)}건")

    # 기타 키워드 - 부동산 키워드만 제외
    else:
        exclude_words = ["분양", "청약", "입주", "재건축", "정비구역"]
        def should_include(row):
            title = str(row.get("기사제목", ""))
            description = str(row.get("주요기사 요약", ""))
            for exclude_word in exclude_words:
                if exclude_word in title or exclude_word in description:
                    return False
            return True

        mask = df.apply(should_include, axis=1)
        df = df[mask].reset_index(drop=True)

    return df


def main():
    """백그라운드 뉴스 모니터링 메인 함수"""
    error_count = 0
    total_collected = 0
    telegram_success = 0

    try:
        safe_print("=" * 80)
        safe_print(f"[MONITOR] 뉴스 수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        safe_print("=" * 80)

        # 전송 캐시 로드
        sent_cache = load_sent_cache()

        # API 키 체크
        headers = _naver_headers()
        api_ok = bool(headers.get("X-Naver-Client-Id") and headers.get("X-Naver-Client-Secret"))

        if not api_ok:
            safe_print("[MONITOR] ❌ API 키가 없어 수집을 건너뜁니다.")
            if LOGGER_AVAILABLE:
                logger.log_error("missing_api_key", "Naver API 키가 설정되지 않았습니다")
            return

        # 기존 DB 로드
        existing_db = load_news_db()
        safe_print(f"[MONITOR] 기존 DB 로드 완료: {len(existing_db)}건")

        # 뉴스 수집 (우선순위 기반)
        all_news = []
        quota_exceeded = False
        num_keywords = len(KEYWORDS)
        items_per_keyword = MAX_ITEMS_PER_RUN // num_keywords

        # 현재 API 사용량 확인
        current_api_usage = load_api_usage()
        safe_print(f"[MONITOR] 현재 API 사용량: {current_api_usage}회")
        safe_print(f"[MONITOR] 수집 설정: 총 {MAX_ITEMS_PER_RUN}개 / 키워드당 약 {items_per_keyword}개")

        # 키워드 우선순위별로 정렬
        keywords_sorted = sorted(KEYWORDS, key=lambda k: KEYWORD_PRIORITY.get(k, 999))
        safe_print(f"[MONITOR] 우선순위 정렬: {', '.join([f'{kw}(P{KEYWORD_PRIORITY.get(kw, 999)})' for kw in keywords_sorted[:3]])}...")

        for kw in keywords_sorted:
            # API 할당량 확인 (2회 호출 필요 - 평균 페이지네이션)
            if not check_api_quota(required_calls=2):
                priority = KEYWORD_PRIORITY.get(kw, 999)

                # 우선순위가 낮은 키워드는 스킵
                if priority >= 3:
                    safe_print(f"[MONITOR] ⏭️ API 할당량 부족 - 우선순위 낮은 키워드 스킵: '{kw}' (P{priority})")
                    continue
                else:
                    safe_print(f"[MONITOR] ⚠️ API 할당량 부족하지만 우선순위 높음: '{kw}' (P{priority}) - 계속 수집")

            safe_print(f"[MONITOR] 키워드 '{kw}' 검색 중... (우선순위: {KEYWORD_PRIORITY.get(kw, 999)})")
            df_kw = crawl_naver_news(kw, max_items=items_per_keyword, sort="date")

            # API 사용량 증가
            current_api_usage = increment_api_usage(calls=2)

            # API 할당량 초과 체크
            if df_kw.attrs.get('quota_exceeded', False):
                safe_print(f"[MONITOR] ⚠️ API 할당량 초과 감지 - 뉴스 수집 중단")
                quota_exceeded = True
                if LOGGER_AVAILABLE:
                    logger.log_error("api_quota_exceeded", "Naver API 할당량 초과")
                error_count += 1
                break

            # 키워드별 필터링 적용
            df_kw = apply_keyword_filters(df_kw, kw)

            if not df_kw.empty:
                all_news.append(df_kw)
                total_collected += len(df_kw)
                safe_print(f"[MONITOR] '{kw}': {len(df_kw)}건 수집")

                # 수집 로깅
                if LOGGER_AVAILABLE:
                    logger.log_collection(kw, len(df_kw), api_calls=2)

        # API 할당량 초과 시 처리
        if quota_exceeded:
            safe_print(f"[MONITOR] ❌ API 할당량 초과로 뉴스 수집 실패")
            safe_print(f"[MONITOR] 💡 매일 자정(KST) 이후 할당량 재설정")
            return

        # 통합 정리 & 저장
        df_new = pd.concat(all_news, ignore_index=True) if all_news else pd.DataFrame()
        if not df_new.empty:
            safe_print(f"[MONITOR] 총 수집: {len(df_new)}건")

            # 날짜순 정렬
            df_new["날짜_datetime"] = pd.to_datetime(df_new["날짜"], errors="coerce")
            df_new = df_new.sort_values("날짜_datetime", ascending=False, na_position="last").reset_index(drop=True)
            df_new = df_new.drop("날짜_datetime", axis=1)

            # 중복 제거
            key = df_new["URL"].where(df_new["URL"].astype(bool), df_new["기사제목"] + "|" + df_new["날짜"])
            df_new = df_new.loc[~key.duplicated()].reset_index(drop=True)

            # 기존 DB와 병합
            merged = pd.concat([df_new, existing_db], ignore_index=True) if not existing_db.empty else df_new
            merged = merged.drop_duplicates(subset=["URL", "기사제목"], keep="first").reset_index(drop=True)
            if not merged.empty:
                merged["날짜"] = pd.to_datetime(merged["날짜"], errors="coerce")
                merged = merged.sort_values("날짜", ascending=False, na_position="last").reset_index(drop=True)
                merged["날짜"] = merged["날짜"].dt.strftime("%Y-%m-%d %H:%M")

            # 신규 기사 감지
            new_articles = detect_new_articles(existing_db, df_new, sent_cache)

            # DB 먼저 저장
            save_news_db(merged)
            safe_print(f"[MONITOR] ✅ DB 저장 완료: 총 {len(merged)}건")

            # 텔레그램 알림 (기존 DB가 비어있지 않을 때만)
            if new_articles and not existing_db.empty:
                safe_print(f"[MONITOR] ✅ 신규 기사 {len(new_articles)}건 감지 - 텔레그램 알림 전송")
                sent_cache_before = len(sent_cache)
                sent_cache = send_telegram_notification(new_articles, sent_cache)
                telegram_success = len(sent_cache) - sent_cache_before

                # 텔레그램 로깅
                if LOGGER_AVAILABLE:
                    failed = len(new_articles) - telegram_success
                    logger.log_telegram(telegram_success, failed, len(new_articles))

            elif new_articles:
                safe_print(f"[MONITOR] ⏭️ 신규 기사 {len(new_articles)}건 감지 - 첫 실행이므로 알림 스킵")
                # 첫 실행에서도 캐시에 추가
                for article in new_articles:
                    url = article.get("link", "")
                    if url:
                        sent_cache.add(url)
                        sent_cache.add(_normalize_url(url))
                safe_print(f"[MONITOR] 신규 기사 {len(new_articles)}건을 캐시에 추가")

            safe_print(f"[MONITOR] ✅ 뉴스 수집 완료")
        else:
            safe_print(f"[MONITOR] ℹ️ 새로 수집된 기사가 없습니다.")

        # 항상 캐시 저장
        safe_print(f"[MONITOR] 캐시 저장 중... (현재 {len(sent_cache)}건)")
        save_sent_cache(sent_cache)

        # 실행 요약 로깅
        if LOGGER_AVAILABLE:
            logger.log_run_summary(
                total_articles=total_collected,
                new_articles=len(new_articles) if 'new_articles' in locals() else 0,
                telegram_sent=telegram_success,
                errors=error_count
            )
            # 일일 통계 출력
            logger.print_daily_summary()
            logger.save_daily_stats()

        safe_print("=" * 80)
        safe_print(f"[MONITOR] 작업 종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        safe_print("=" * 80)

    except Exception as e:
        safe_print(f"[MONITOR] ❌ 뉴스 수집 오류: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        safe_print(f"[MONITOR] 상세 오류:\n{error_details}")

        # 에러 로깅
        if LOGGER_AVAILABLE:
            logger.log_error("unexpected_error", str(e), error_details)


if __name__ == "__main__":
    main()
