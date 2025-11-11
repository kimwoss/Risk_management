"""
Standalone News Monitor - GitHub Actions용
Streamlit 없이 독립적으로 뉴스를 수집하고 텔레그램 알림을 전송합니다.
3분마다 GitHub Actions에서 자동 실행됩니다.
"""
import os
import re
import urllib.parse
from datetime import datetime
from html import unescape
import pandas as pd
import requests

# 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 상수
DATA_FOLDER = os.path.abspath("data")
NEWS_DB_FILE = os.path.join(DATA_FOLDER, "news_monitor.csv")
SENT_CACHE_FILE = os.path.join(DATA_FOLDER, "sent_articles_cache.json")
_MAX_SENT_CACHE = 500  # 캐시 크기 제한 (500개)

# 전송된 기사 URL 추적 (파일 기반 영구 저장)
_sent_articles_cache = set()


def _naver_headers():
    """Naver API 인증 헤더"""
    cid = os.getenv("NAVER_CLIENT_ID", "")
    csec = os.getenv("NAVER_CLIENT_SECRET", "")
    print(f"[DEBUG] NAVER_CLIENT_ID: '{cid[:10]}...' (length: {len(cid)})")
    print(f"[DEBUG] NAVER_CLIENT_SECRET: '{csec[:5]}...' (length: {len(csec)})")
    if not cid or not csec:
        print(f"[WARNING] 네이버 API 키가 없습니다. 환경변수를 확인해주세요.")
        print(f"[DEBUG] Missing API keys - ID: {bool(cid)}, Secret: {bool(csec)}")
    return {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec}


def _clean_text(s: str) -> str:
    """HTML 태그 및 공백 정리"""
    if not s:
        return ""
    s = unescape(s)
    s = re.sub(r"</?b>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _normalize_url(url: str) -> str:
    """
    URL 정규화 - 중복 체크를 위해 URL을 표준 형식으로 변환
    - 쿼리 파라미터 제거
    - 프로토콜 통일 (http → https)
    - 끝 슬래시 제거
    """
    try:
        if not url:
            return ""

        # 쿼리 파라미터와 프래그먼트 제거
        parsed = urllib.parse.urlparse(url)
        # 프로토콜을 https로 통일
        scheme = "https" if parsed.scheme in ["http", "https"] else parsed.scheme
        # 재조립
        normalized = f"{scheme}://{parsed.netloc}{parsed.path}"
        # 끝 슬래시 제거
        normalized = normalized.rstrip("/")

        return normalized
    except Exception as e:
        print(f"[WARNING] URL 정규화 실패: {url} - {e}")
        return url


def _publisher_from_link(u: str) -> str:
    """뉴스 원문 URL에서 매체명을 통일해서 반환"""
    try:
        host = urllib.parse.urlparse(u).netloc.lower().replace("www.", "")
        if not host:
            return ""

        # 1) 서브도메인까지 정확 매핑
        host_map = {
            "en.yna.co.kr": "연합뉴스",
            "news.kbs.co.kr": "KBS",
            "news.mtn.co.kr": "MTN",
            "starin.edaily.co.kr": "이데일리",
            "sports.donga.com": "동아일보",
            "biz.heraldcorp.com": "헤럴드경제",
            "daily.hankooki.com": "데일리한국",
            "news.dealsitetv.com": "딜사이트TV",
        }
        if host in host_map:
            return host_map[host]

        # 2) 기본 도메인(eTLD+1) 추출
        parts = host.split(".")
        if len(parts) >= 3 and parts[-1] == "kr" and parts[-2] in {
            "co","or","go","ne","re","pe","ac","hs","kg","sc",
            "seoul","busan","incheon","daegu","daejeon","gwangju","ulsan",
            "gyeonggi","gangwon","chungbuk","chungnam","jeonbuk","jeonnam",
            "gyeongbuk","gyeongnam","jeju"
        }:
            base = ".".join(parts[-3:])
        else:
            base = ".".join(parts[-2:])

        # 3) 기본 도메인 → 매체명 매핑 (축약 버전)
        base_map = {
            "yna.co.kr": "연합뉴스",
            "kbs.co.kr": "KBS",
            "joins.com": "중앙일보",
            "donga.com": "동아일보",
            "heraldcorp.com": "헤럴드경제",
            "edaily.co.kr": "이데일리",
            "ajunews.com": "아주경제",
            "newspim.com": "뉴스핌",
            "news1.kr": "뉴스1",
            "etoday.co.kr": "이투데이",
            "asiae.co.kr": "아시아경제",
            "nocutnews.co.kr": "노컷뉴스",
            "munhwa.com": "문화일보",
            "segye.com": "세계일보",
            "hankooki.com": "한국일보",
            "dt.co.kr": "디지털타임스",
            "ekn.kr": "에너지경제",
            "businesskorea.co.kr": "비즈니스코리아",
            "ferrotimes.com": "철강금속신문",
            # 추가 매체명 매핑
            "thepublic.kr": "더퍼블릭",
            "tf.co.kr": "더팩트",
            "straightnews.co.kr": "스트레이트뉴스",
            "smartfn.co.kr": "스마트경제",
            "sisacast.kr": "시사캐스트",
            "sateconomy.co.kr": "시사경제",
            "safetynews.co.kr": "안전신문",
            "rpm9.com": "RPM9",
            "pointdaily.co.kr": "포인트데일리",
            "newsworker.co.kr": "뉴스워커",
            "newsdream.kr": "뉴스드림",
            "nbntv.co.kr": "NBN뉴스",
            "megaeconomy.co.kr": "메가경제",
            "mediapen.com": "미디어펜",
            "job-post.co.kr": "잡포스트",
            "irobotnews.com": "로봇신문사",
            "ifm.kr": "경인방송",
            "gpkorea.com": "글로벌오토뉴스",
            "energydaily.co.kr": "에너지데일리",
            "cstimes.com": "컨슈머타임스",
            "bizwatch.co.kr": "비즈워치",
            "autodaily.co.kr": "오토데일리",
        }
        if base in base_map:
            return base_map[base]

        return ""
    except Exception:
        return ""


def fetch_naver_news(query: str, start: int = 1, display: int = 50, sort: str = "date"):
    """Naver 뉴스 API 호출"""
    try:
        url = "https://openapi.naver.com/v1/search/news.json"
        params = {"query": query, "start": start, "display": display, "sort": sort}
        headers = _naver_headers()

        print(f"[DEBUG] API Request - Query: {query}, Params: {params}")

        if not headers.get("X-Naver-Client-Id") or not headers.get("X-Naver-Client-Secret"):
            print("[DEBUG] Missing API keys, returning empty result")
            return {"items": [], "error": "missing_keys"}

        print(f"[DEBUG] Starting API request...")
        r = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"[DEBUG] API Response status: {r.status_code}")

        # 429 에러 (할당량 초과) 명시적 처리
        if r.status_code == 429:
            error_data = r.json() if r.text else {}
            error_msg = error_data.get("errorMessage", "API quota exceeded")
            print(f"[ERROR] API 할당량 초과 (429): {error_msg}")
            return {"items": [], "error": "quota_exceeded", "error_message": error_msg}

        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] API Response items count: {len(result.get('items', []))}")
        return result

    except requests.exceptions.Timeout:
        print(f"[WARNING] Naver API timeout for query: {query}")
        return {"items": [], "error": "timeout"}
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Naver API request failed for query: {query}, error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 429:
                return {"items": [], "error": "quota_exceeded"}
        return {"items": [], "error": "request_failed"}
    except Exception as e:
        print(f"[WARNING] Unexpected error in fetch_naver_news: {e}")
        return {"items": [], "error": "unexpected"}


def crawl_naver_news(query: str, max_items: int = 200, sort: str = "date") -> pd.DataFrame:
    """Naver 뉴스 수집"""
    print(f"[DEBUG] Starting crawl_naver_news for query: {query}, max_items: {max_items}")
    items, start, total = [], 1, 0
    display = min(50, max_items)
    max_attempts = 2
    attempt_count = 0
    quota_exceeded = False

    while total < max_items and start <= 100 and attempt_count < max_attempts:
        attempt_count += 1
        print(f"[DEBUG] Attempt {attempt_count} for query: {query}")

        try:
            data = fetch_naver_news(query, start=start, display=min(display, max_items - total), sort=sort)

            # API 할당량 초과 에러 체크
            if data.get("error") == "quota_exceeded":
                print(f"[ERROR] API 할당량 초과 감지 - 뉴스 수집 중단")
                quota_exceeded = True
                break

            arr = data.get("items", [])

            if not arr:
                print(f"[DEBUG] No items returned for query: {query}, attempt: {attempt_count}")
                break

            print(f"[DEBUG] Got {len(arr)} items for query: {query}")

            for it in arr:
                title = _clean_text(it.get("title"))
                desc = _clean_text(it.get("description"))
                link = it.get("originallink") or it.get("link") or ""
                pub = it.get("pubDate", "")
                try:
                    # GMT → KST 변환 후 tz 제거
                    dt = pd.to_datetime(pub, utc=True).tz_convert("Asia/Seoul").tz_localize(None)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_str = ""
                items.append({"날짜": date_str, "매체명": _publisher_from_link(link),
                              "검색키워드": query, "기사제목": title, "주요기사 요약": desc, "URL": link})

            got = len(arr)
            total += got
            if got == 0:
                break
            start += got

        except Exception as e:
            print(f"[WARNING] Error in crawl_naver_news attempt {attempt_count}: {e}")
            break

    print(f"[DEBUG] crawl_naver_news completed for {query}: {len(items)} items")
    df = pd.DataFrame(items, columns=["날짜", "매체명", "검색키워드", "기사제목", "주요기사 요약", "URL"])

    # API 할당량 초과 정보를 DataFrame 속성으로 저장
    if quota_exceeded:
        df.attrs['quota_exceeded'] = True
        print(f"[ERROR] API 할당량 초과로 뉴스 수집 실패")

    if not df.empty:
        # 최신순 정렬
        df["날짜_datetime"] = pd.to_datetime(df["날짜"], errors="coerce")
        df = df.sort_values("날짜_datetime", ascending=False, na_position="last").reset_index(drop=True)
        df = df.drop("날짜_datetime", axis=1)

        # 중복 제거 (URL 우선, 없으면 제목+날짜)
        key = df["URL"].where(df["URL"].astype(bool), df["기사제목"] + "|" + df["날짜"])
        df = df.loc[~key.duplicated()].reset_index(drop=True)
    return df


def load_news_db() -> pd.DataFrame:
    """뉴스 DB 로드"""
    if os.path.exists(NEWS_DB_FILE):
        try:
            return pd.read_csv(NEWS_DB_FILE, encoding="utf-8")
        except Exception as e:
            print(f"[WARNING] DB 로드 실패: {e}")
    return pd.DataFrame(columns=["날짜","매체명","검색키워드","기사제목","주요기사 요약","URL"])


def save_news_db(df: pd.DataFrame):
    """뉴스 DB 저장"""
    if df.empty:
        print("[DEBUG] save_news_db skipped: empty dataframe")
        return

    # 매체명 정리 (URL 기반)
    if "매체명" in df.columns and "URL" in df.columns:
        for idx, row in df.iterrows():
            if pd.notna(row["URL"]):
                df.at[idx, "매체명"] = _publisher_from_link(row["URL"])

    # 상위 200개만 저장 (중복 알림 방지)
    out = df.head(200).copy()

    # data 폴더 생성
    os.makedirs(DATA_FOLDER, exist_ok=True)

    out.to_csv(NEWS_DB_FILE, index=False, encoding="utf-8")
    print(f"[DEBUG] news saved: {len(out)} rows -> {NEWS_DB_FILE}")


def load_sent_cache() -> set:
    """
    전송된 기사 캐시를 파일에서 로드
    Returns:
        전송된 기사 URL 세트
    """
    if os.path.exists(SENT_CACHE_FILE):
        try:
            import json
            with open(SENT_CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cache = set(data.get("urls", []))
                print(f"[DEBUG] 전송 캐시 로드 완료: {len(cache)}건")
                return cache
        except Exception as e:
            print(f"[WARNING] 전송 캐시 로드 실패: {e}")
            return set()
    else:
        print(f"[DEBUG] 전송 캐시 파일 없음 - 새로 생성")
        return set()


def save_sent_cache(cache: set):
    """
    전송된 기사 캐시를 파일에 저장
    Args:
        cache: 전송된 기사 URL 세트
    """
    try:
        import json
        # data 폴더 생성
        os.makedirs(DATA_FOLDER, exist_ok=True)

        # 최근 _MAX_SENT_CACHE개만 유지
        cache_list = list(cache)[-_MAX_SENT_CACHE:]

        data = {
            "urls": cache_list,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(cache_list)
        }

        with open(SENT_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[DEBUG] 전송 캐시 저장 완료: {len(cache_list)}건 -> {SENT_CACHE_FILE}")
    except Exception as e:
        print(f"[WARNING] 전송 캐시 저장 실패: {e}")


def detect_new_articles(old_df: pd.DataFrame, new_df: pd.DataFrame) -> list:
    """
    기존 DB와 새로운 데이터를 비교하여 신규 기사 감지
    - URL을 우선 식별자로 사용
    - 최근 1시간 이내 기사만 알림 대상 (중복 방지 강화)
    - 캐시도 함께 체크
    """
    global _sent_articles_cache

    try:
        # 기존 DB가 비어있으면 신규 기사 없음으로 처리 (첫 실행 스팸 방지)
        if old_df.empty:
            print(f"[DEBUG] 기존 DB 비어있음 - 첫 실행이므로 알림 스킵")
            return []

        if new_df.empty:
            return []

        # 현재 시간 기준
        now = datetime.now()

        # 기존 DB의 URL 세트 생성 (정규화된 URL 사용)
        old_urls = set()
        old_urls_normalized = set()
        for _, row in old_df.iterrows():
            url = str(row.get("URL", "")).strip()
            if url and url != "nan" and url != "":
                old_urls.add(url)
                old_urls_normalized.add(_normalize_url(url))

        print(f"[DEBUG] 기존 DB URL 수: {len(old_urls)} (정규화: {len(old_urls_normalized)})")
        print(f"[DEBUG] 캐시 크기: {len(_sent_articles_cache)}건")
        print(f"[DEBUG] 수집된 신규 데이터 수: {len(new_df)}")

        # 신규 기사 감지
        new_articles = []
        for _, row in new_df.iterrows():
            url = str(row.get("URL", "")).strip()
            title = str(row.get("기사제목", "")).strip()

            # URL이 없거나 비어있으면 스킵
            if not url or url == "nan" or url == "":
                continue

            # URL 정규화
            url_normalized = _normalize_url(url)

            # 3단계 중복 체크: DB + 캐시 + 정규화
            is_in_db = url in old_urls or url_normalized in old_urls_normalized
            is_in_cache = url in _sent_articles_cache or url_normalized in _sent_articles_cache

            if is_in_db or is_in_cache:
                # 이미 DB에 있거나 캐시에 있으면 스킵
                continue

            # 여기까지 왔으면 진짜 신규 기사
            # 날짜 정보 로깅 (시간 필터링 제거 - GitHub Actions 실행이 불규칙하므로)
            article_date_str = row.get("날짜", "")
            try:
                article_date = pd.to_datetime(article_date_str, errors="coerce")
                if pd.notna(article_date):
                    time_diff = now - article_date
                    hours_diff = time_diff.total_seconds() / 3600
                    print(f"[DEBUG] ✅ 신규 기사 감지: {title[:50]}... ({hours_diff:.1f}시간 전)")
                else:
                    print(f"[DEBUG] ✅ 신규 기사 감지 (날짜 파싱 실패): {title[:50]}...")
            except Exception as e:
                print(f"[DEBUG] ✅ 신규 기사 감지 (날짜 처리 오류): {title[:50]}... - {str(e)}")

            # URL에서 매체명 추출
            press = _publisher_from_link(url)

            # 검색 키워드 추출
            keyword = str(row.get("검색키워드", "")).strip()

            new_articles.append({
                "title": title if title and title != "nan" else "제목 없음",
                "link": url,
                "date": article_date_str,
                "press": press,
                "keyword": keyword
            })

        print(f"[DEBUG] 총 {len(new_articles)}건의 진짜 신규 기사 감지 (DB+캐시 중복 제거, 시간 제한 없음)")
        return new_articles

    except Exception as e:
        print(f"[DEBUG] 신규 기사 감지 오류: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류:\n{traceback.format_exc()}")
        return []


def send_telegram_notification(new_articles: list):
    """
    새로운 기사가 발견되면 텔레그램으로 알림 전송 (기사별 개별 메시지)
    """
    global _sent_articles_cache

    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        print(f"[DEBUG] 텔레그램 알림 시도 - 기사 수: {len(new_articles) if new_articles else 0}")
        print(f"[DEBUG] 봇 토큰 존재: {bool(bot_token)}, Chat ID 존재: {bool(chat_id)}")
        print(f"[DEBUG] 현재 캐시 크기: {len(_sent_articles_cache)}건")

        # 환경변수가 없으면 알림 스킵
        if not bot_token or not chat_id:
            print("[DEBUG] ⚠️ 텔레그램 설정 없음 - 알림 스킵")
            print("[DEBUG] 💡 GitHub Secrets에서 TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID 설정 필요")
            return

        if not new_articles:
            print("[DEBUG] 신규 기사 없음 - 알림 스킵")
            return

        # 이미 전송된 기사 필터링 (캐시 기반, URL 정규화)
        articles_to_send = []
        for article in new_articles:
            url_key = article.get("link", "")
            url_normalized = _normalize_url(url_key)

            # 원본 URL과 정규화 URL 모두 체크
            if url_key and url_key not in _sent_articles_cache and url_normalized not in _sent_articles_cache:
                articles_to_send.append(article)
            else:
                print(f"[DEBUG] 캐시에 이미 존재하여 스킵: {article.get('title', '')[:30]}...")

        if not articles_to_send:
            print("[DEBUG] 모든 기사가 이미 전송됨 - 알림 스킵")
            return

        print(f"[DEBUG] 전송 대상: {len(articles_to_send)}건 (캐시 중복 제외: {len(new_articles) - len(articles_to_send)}건)")

        # 최대 10개까지만 알림
        articles_to_notify = articles_to_send[:10]

        # 텔레그램 API URL
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # 각 기사마다 개별 메시지 전송
        success_count = 0
        for article in articles_to_notify:
            title = article.get("title", "제목 없음")
            link = article.get("link", "")
            date = article.get("date", "")
            press = article.get("press", "")
            keyword = article.get("keyword", "")

            # 단문 메시지 구성
            message = f"🚨 *새 뉴스*\n\n"

            # 검색 키워드 해시태그 추가
            if keyword:
                # 공백을 제거하여 해시태그로 변환
                hashtag = keyword.replace(" ", "")
                message += f"#{hashtag}\n"

            # 제목 앞에 [언론사] 추가
            if press:
                message += f"*[{press}]* {title}\n"
            else:
                message += f"*{title}*\n"

            # 날짜와 링크
            if date:
                message += f"🕐 {date}\n"
            if link:
                message += f"🔗 {link}"

            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }

            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    success_count += 1
                    print(f"[DEBUG] ✅ 메시지 전송 성공: {title[:30]}...")

                    # 전송 성공한 기사는 캐시에 추가 (원본 + 정규화 URL 모두)
                    _sent_articles_cache.add(link)
                    _sent_articles_cache.add(_normalize_url(link))
                else:
                    print(f"[DEBUG] ❌ 메시지 전송 실패: {response.status_code} - {title[:30]}...")

                # 텔레그램 Rate Limit 방지 (초당 30개 메시지 제한)
                import time
                time.sleep(0.05)  # 50ms 대기

            except Exception as e:
                print(f"[DEBUG] ❌ 개별 메시지 전송 오류: {str(e)}")

        print(f"[DEBUG] ✅ 총 {success_count}/{len(articles_to_notify)}건 전송 완료")
        print(f"[DEBUG] 전송 후 캐시 크기: {len(_sent_articles_cache)}건")

        # 캐시를 파일에 저장 (영구 보관)
        save_sent_cache(_sent_articles_cache)

        # 5개 이상 남은 기사가 있으면 요약 메시지
        if len(new_articles) > 10:
            summary_message = f"📢 _외 {len(new_articles) - 10}건의 뉴스가 더 있습니다._"
            payload = {
                "chat_id": chat_id,
                "text": summary_message,
                "parse_mode": "Markdown"
            }
            requests.post(url, json=payload, timeout=10)

    except Exception as e:
        print(f"[DEBUG] ❌ 텔레그램 알림 예외 발생: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류:\n{traceback.format_exc()}")


def safe_print(text: str):
    """Windows 콘솔 인코딩 오류 방지"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 이모지 제거하고 재시도
        text_clean = text.encode('ascii', 'ignore').decode('ascii')
        print(text_clean)


def main():
    """
    백그라운드 뉴스 모니터링 메인 함수
    """
    global _sent_articles_cache

    try:
        safe_print("=" * 80)
        safe_print(f"[MONITOR] 뉴스 수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        safe_print("=" * 80)

        # 전송 캐시 로드 (이전 실행에서 전송한 기사 정보)
        _sent_articles_cache = load_sent_cache()

        # 키워드 설정
        keywords = [
            "포스코인터내셔널",
            "POSCO INTERNATIONAL",
            "포스코인터",
            "삼척블루파워",
            "구동모터코아",
            "구동모터코어",
            "미얀마 LNG",
            "포스코모빌리티솔루션",
            "포스코"
        ]
        exclude_keywords = ["포스코인터내셔널", "POSCO INTERNATIONAL", "포스코인터",
                           "삼척블루파워", "포스코모빌리티솔루션"]
        max_items = 30  # API 사용량 최적화

        # API 키 체크
        headers = _naver_headers()
        api_ok = bool(headers.get("X-Naver-Client-Id") and headers.get("X-Naver-Client-Secret"))

        if not api_ok:
            print("[MONITOR] ❌ API 키가 없어 수집을 건너뜁니다.")
            return

        # 기존 DB 로드
        existing_db = load_news_db()
        safe_print(f"[MONITOR] 기존 DB 로드 완료: {len(existing_db)}건")

        # 뉴스 수집
        all_news = []
        quota_exceeded = False

        for kw in keywords:
            safe_print(f"[MONITOR] 키워드 '{kw}' 검색 중...")
            df_kw = crawl_naver_news(kw, max_items=max_items // len(keywords), sort="date")

            # API 할당량 초과 체크
            if df_kw.attrs.get('quota_exceeded', False):
                safe_print(f"[MONITOR] [WARNING] API 할당량 초과 감지 - 뉴스 수집 중단")
                quota_exceeded = True
                break

            if not df_kw.empty:
                # "포스코인터내셔널" 정확한 매칭 강화
                if kw == "포스코인터내셔널":
                    def should_include_posco_intl(row):
                        title = str(row.get("기사제목", ""))
                        description = str(row.get("주요기사 요약", ""))

                        # 정확히 "포스코인터내셔널"이 포함되어야 함
                        if "포스코인터내셔널" not in title and "포스코인터내셔널" not in description:
                            return False

                        # 제외 키워드 체크 제거 - 정확한 회사명이므로 모든 기사 수집
                        return True

                    mask = df_kw.apply(should_include_posco_intl, axis=1)
                    df_kw = df_kw[mask].reset_index(drop=True)
                    if not df_kw.empty:
                        safe_print(f"[MONITOR] '포스코인터내셔널' 정확 매칭 필터링 완료: {len(df_kw)}건 추가")

                # "포스코모빌리티솔루션" 정확한 매칭 강화
                elif kw == "포스코모빌리티솔루션":
                    def should_include_posco_mobility(row):
                        title = str(row.get("기사제목", ""))
                        description = str(row.get("주요기사 요약", ""))

                        # 정확히 "포스코모빌리티솔루션"이 포함되어야 함
                        if "포스코모빌리티솔루션" not in title and "포스코모빌리티솔루션" not in description:
                            return False

                        # 제외 키워드 체크 제거 - 정확한 회사명이므로 모든 기사 수집
                        return True

                    mask = df_kw.apply(should_include_posco_mobility, axis=1)
                    df_kw = df_kw[mask].reset_index(drop=True)
                    if not df_kw.empty:
                        safe_print(f"[MONITOR] '포스코모빌리티솔루션' 정확 매칭 필터링 완료: {len(df_kw)}건 추가")

                # "포스코" 키워드의 경우 특별 처리
                elif kw == "포스코":
                    def should_include_posco(row):
                        title = str(row.get("기사제목", ""))
                        title_lower = title.lower()
                        description = str(row.get("주요기사 요약", ""))

                        if "포스코" not in title and "posco" not in title_lower:
                            return False

                        for exclude_kw in exclude_keywords:
                            if exclude_kw.lower() in title_lower:
                                return False

                        exclude_words = ["청약", "분양", "입주", "재건축", "정비구역", "인테리어"]
                        for exclude_word in exclude_words:
                            if exclude_word in title or exclude_word in description:
                                return False

                        return True

                    mask_posco = df_kw.apply(should_include_posco, axis=1)
                    df_kw = df_kw[mask_posco].reset_index(drop=True)
                    if not df_kw.empty:
                        safe_print(f"[MONITOR] '포스코' 필터링 완료: {len(df_kw)}건 추가")

                else:
                    # 다른 키워드는 제목과 요약 모두에서 부동산 관련 키워드 제거
                    exclude_words = ["분양", "청약", "입주", "재건축", "정비구역"]
                    def should_include_general(row):
                        title = str(row.get("기사제목", ""))
                        description = str(row.get("주요기사 요약", ""))

                        # 제목과 요약 모두 체크
                        for exclude_word in exclude_words:
                            if exclude_word in title or exclude_word in description:
                                return False
                        return True

                    mask_general = df_kw.apply(should_include_general, axis=1)
                    df_kw = df_kw[mask_general].reset_index(drop=True)

                if not df_kw.empty:
                    all_news.append(df_kw)
                    safe_print(f"[MONITOR] '{kw}': {len(df_kw)}건 수집")

        # API 할당량 초과 시 처리
        if quota_exceeded:
            safe_print(f"[MONITOR] [ERROR] API 할당량 초과로 뉴스 수집 실패")
            safe_print(f"[MONITOR] [TIP] 해결 방법:")
            safe_print(f"[MONITOR]    1. 새로운 네이버 개발자 계정으로 API 키 재발급")
            safe_print(f"[MONITOR]    2. 매일 자정(KST) 이후 할당량 재설정")
            return

        # 통합 정리 & 저장
        df_new = pd.concat(all_news, ignore_index=True) if all_news else pd.DataFrame()
        if not df_new.empty:
            safe_print(f"[MONITOR] 총 수집: {len(df_new)}건")

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
            new_articles = detect_new_articles(existing_db, df_new)

            # DB 먼저 저장 (race condition 방지)
            save_news_db(merged)
            safe_print(f"[MONITOR] [SUCCESS] DB 저장 완료: 총 {len(merged)}건")

            # 기존 DB가 비어있지 않을 때만 알림 전송 (첫 실행 스팸 방지)
            if new_articles and not existing_db.empty:
                safe_print(f"[MONITOR] [SUCCESS] 신규 기사 {len(new_articles)}건 감지 - 텔레그램 알림 전송")
                send_telegram_notification(new_articles)
            elif new_articles:
                safe_print(f"[MONITOR] [SKIP] 신규 기사 {len(new_articles)}건 감지 - 첫 실행이므로 알림 스킵")
                # 첫 실행에서도 캐시에 추가하여 다음 실행 시 중복 방지
                for article in new_articles:
                    url = article.get("link", "")
                    if url:
                        _sent_articles_cache.add(url)
                        _sent_articles_cache.add(_normalize_url(url))
                print(f"[DEBUG] 신규 기사 {len(new_articles)}건을 캐시에 추가 (알림 미전송)")
                save_sent_cache(_sent_articles_cache)

            safe_print(f"[MONITOR] [SUCCESS] 뉴스 수집 완료")
        else:
            safe_print(f"[MONITOR] [INFO] 새로 수집된 기사가 없습니다.")

        # 🔧 항상 캐시 저장 (신규 기사 없어도)
        safe_print(f"[MONITOR] 캐시 저장 중... (현재 {len(_sent_articles_cache)}건)")
        save_sent_cache(_sent_articles_cache)

        safe_print("=" * 80)
        safe_print(f"[MONITOR] 작업 종료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        safe_print("=" * 80)

    except Exception as e:
        safe_print(f"[MONITOR] [ERROR] 뉴스 수집 오류: {str(e)}")
        import traceback
        safe_print(f"[MONITOR] 상세 오류:\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
