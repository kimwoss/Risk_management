"""
뉴스 수집 공통 모듈
Streamlit App과 Standalone Monitor가 공유하는 뉴스 수집 로직
"""
import os
import re
import urllib.parse
import json
from datetime import datetime, timezone, timedelta
from html import unescape
import pandas as pd
import requests

# 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ======================== 유틸리티 함수 ========================

# 원본 print 저장
_original_print = print

def safe_print(*args, **kwargs):
    """Windows cp949 인코딩 에러 방지용 안전한 print"""
    try:
        _original_print(*args, **kwargs)
    except (UnicodeEncodeError, OSError):
        # 이모지 제거 후 재시도
        try:
            safe_args = []
            for arg in args:
                if isinstance(arg, str):
                    # 이모지 및 특수문자 제거
                    safe_arg = arg.encode('ascii', 'ignore').decode('ascii')
                    safe_args.append(safe_arg)
                else:
                    safe_args.append(arg)
            _original_print(*safe_args, **kwargs)
        except:
            # 그래도 실패하면 무시
            pass

# 전역 print를 safe_print로 오버라이드
print = safe_print

# ======================== 상수 설정 ========================

DATA_FOLDER = os.path.abspath("data")
NEWS_DB_FILE = os.path.join(DATA_FOLDER, "news_monitor.csv")
SENT_CACHE_FILE = os.path.join(DATA_FOLDER, "sent_articles_cache.json")
API_USAGE_FILE = os.path.join(DATA_FOLDER, "api_usage.json")
STATE_FILE = os.path.join(DATA_FOLDER, "monitor_state.json")
MAX_SENT_CACHE = 10000  # 캐시 크기 제한 (약 4-5일분 커버, 기존 500개에서 확대)
MAX_API_CALLS_PER_DAY = 25000  # 네이버 API 일일 할당량
API_QUOTA_WARNING_THRESHOLD = 20000  # 80% 도달 시 경고 (25000의 80%)

# 모니터링 키워드 설정 (단일 진실 공급원)
KEYWORDS = [
    "포스코인터내셔널",
    "POSCO INTERNATIONAL",
    "포스코인터",
    "삼척블루파워",
    "구동모터코아",
    "구동모터코어",
    "미얀마 LNG",
    "포스코모빌리티솔루션",
    "포스코플로우",  # 추가
    "포스코"
]

# "포스코" 키워드 제외 필터
EXCLUDE_KEYWORDS = [
    "포스코인터내셔널",
    "POSCO INTERNATIONAL",
    "포스코인터",
    "삼척블루파워",
    "포스코모빌리티솔루션"
]

# 수집 설정
MAX_ITEMS_PER_RUN = 300  # 키워드당 약 30개 수집 (필터링 후 충분한 기사 확보)

# 전송된 기사 URL 추적 (메모리 캐시)
_sent_articles_cache = set()


# ======================== 헬퍼 함수 ========================

def _naver_headers():
    """Naver API 인증 헤더"""
    cid = os.getenv("NAVER_CLIENT_ID", "")
    csec = os.getenv("NAVER_CLIENT_SECRET", "")
    if not cid or not csec:
        print(f"[WARNING] 네이버 API 키가 없습니다. 환경변수를 확인해주세요.")
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
    - 쿼리 파라미터 보존 (중요! 많은 뉴스 사이트가 쿼리로 기사 구분)
    - 프로토콜 통일 (http → https)
    - 끝 슬래시 제거
    """
    try:
        if not url:
            return ""
        parsed = urllib.parse.urlparse(url)

        # 1. 프로토콜 통일 (http → https)
        scheme = "https" if parsed.scheme in ["http", "https"] else parsed.scheme

        # 2. 쿼리 파라미터 보존 (기사 ID 구분을 위해 필수)
        query = f"?{parsed.query}" if parsed.query else ""

        # 3. 끝 슬래시 제거
        path = parsed.path.rstrip("/")

        # 4. 정규화된 URL 생성
        normalized = f"{scheme}://{parsed.netloc}{path}{query}"
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

        # 서브도메인 정확 매핑
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

        # 기본 도메인(eTLD+1) 추출
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

        # 기본 도메인 → 매체명 매핑
        base_map = {
            "yna.co.kr": "연합뉴스", "kbs.co.kr": "KBS", "joins.com": "중앙일보",
            "donga.com": "동아일보", "heraldcorp.com": "헤럴드경제", "edaily.co.kr": "이데일리",
            "ajunews.com": "아주경제", "newspim.com": "뉴스핌", "news1.kr": "뉴스1",
            "etoday.co.kr": "이투데이", "asiae.co.kr": "아시아경제", "nocutnews.co.kr": "노컷뉴스",
            "munhwa.com": "문화일보", "segye.com": "세계일보", "hankooki.com": "한국일보",
            "dt.co.kr": "디지털타임스", "ekn.kr": "에너지경제", "businesskorea.co.kr": "비즈니스코리아",
            "ferrotimes.com": "철강금속신문", "thepublic.kr": "더퍼블릭", "tf.co.kr": "더팩트",
            "straightnews.co.kr": "스트레이트뉴스", "smartfn.co.kr": "스마트경제", "sisacast.kr": "시사캐스트",
            "sateconomy.co.kr": "시사경제", "safetynews.co.kr": "안전신문", "rpm9.com": "RPM9",
            "pointdaily.co.kr": "포인트데일리", "newsworker.co.kr": "뉴스워커", "newsdream.kr": "뉴스드림",
            "nbntv.co.kr": "NBN뉴스", "megaeconomy.co.kr": "메가경제", "mediapen.com": "미디어펜",
            "job-post.co.kr": "잡포스트", "irobotnews.com": "로봇신문사", "ifm.kr": "경인방송",
            "gpkorea.com": "글로벌오토뉴스", "energydaily.co.kr": "에너지데일리",
            "cstimes.com": "컨슈머타임스", "bizwatch.co.kr": "비즈워치", "autodaily.co.kr": "오토데일리",
            # 추가 언론사 (2025-11-20)
            "newslock.co.kr": "뉴스락", "mbn.co.kr": "MBN", "kpenews.com": "KPE",
            "koreatimes.co.kr": "코리아타임스", "korea.kr": "대한민국 정책브리핑",
            "investchosun.com": "인베스트조선", "goodnews1.com": "GOODTV", "aitimes.kr": "AI타임스",
            # 추가 언론사 (2025-12-02)
            "worklaw.co.kr": "워크로", "vop.co.kr": "민중의소리", "thefairnews.co.kr": "더페어뉴스",
            "newsway.co.kr": "뉴스웨이", "newsfreezone.co.kr": "뉴스프리존", "mtn.co.kr": "머니투데이방송",
            "kyongbuk.co.kr": "경북일보", "klnews.co.kr": "물류신문", "geconomy.co.kr": "G경제",
            "enetnews.co.kr": "이넷뉴스", "dkilbo.com": "대경일보", "dailysportshankook.co.kr": "데일리스포츠한국",
            "dailysecu.com": "데일리시큐", "ceoscoredaily.com": "CEO스코어데일리", "apparelnews.co.kr": "어패럴뉴스",
        }
        if base in base_map:
            return base_map[base]

        return ""
    except Exception:
        return ""


# ======================== 네이버 API 함수 ========================

def fetch_naver_news(query: str, start: int = 1, display: int = 50, sort: str = "date"):
    """Naver 뉴스 API 호출 (연결 누수 방지)"""
    r = None
    try:
        url = "https://openapi.naver.com/v1/search/news.json"
        params = {"query": query, "start": start, "display": display, "sort": sort}
        headers = _naver_headers()

        if not headers.get("X-Naver-Client-Id") or not headers.get("X-Naver-Client-Secret"):
            return {"items": [], "error": "missing_keys"}

        r = requests.get(url, headers=headers, params=params, timeout=10)

        # API 할당량 초과 처리
        if r.status_code == 429:
            error_data = r.json() if r.text else {}
            error_msg = error_data.get("errorMessage", "API quota exceeded")
            print(f"[ERROR] API 할당량 초과 (429): {error_msg}")
            return {"items": [], "error": "quota_exceeded", "error_message": error_msg}

        r.raise_for_status()
        return r.json()

    except requests.exceptions.Timeout:
        print(f"[WARNING] Naver API timeout for query: {query}")
        return {"items": [], "error": "timeout"}
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Naver API request failed for query: {query}, error: {e}")
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
            return {"items": [], "error": "quota_exceeded"}
        return {"items": [], "error": "request_failed"}
    except Exception as e:
        print(f"[WARNING] Unexpected error in fetch_naver_news: {e}")
        return {"items": [], "error": "unexpected"}
    finally:
        # 연결 누수 방지: 응답 객체 명시적으로 닫기
        if r is not None:
            r.close()


def crawl_naver_news(query: str, max_items: int = 200, sort: str = "date") -> pd.DataFrame:
    """Naver 뉴스 수집"""
    items, start, total = [], 1, 0
    display = min(50, max_items)
    max_attempts = 2
    attempt_count = 0
    quota_exceeded = False

    while total < max_items and start <= 100 and attempt_count < max_attempts:
        attempt_count += 1

        try:
            data = fetch_naver_news(query, start=start, display=min(display, max_items - total), sort=sort)

            # API 할당량 초과 체크
            if data.get("error") == "quota_exceeded":
                print(f"[ERROR] API 할당량 초과 감지 - 뉴스 수집 중단")
                quota_exceeded = True
                break

            arr = data.get("items", [])
            if not arr:
                break

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
                items.append({
                    "날짜": date_str,
                    "매체명": _publisher_from_link(link),
                    "검색키워드": query,
                    "기사제목": title,
                    "주요기사 요약": desc,
                    "URL": link
                })

            got = len(arr)
            total += got
            if got == 0:
                break
            start += got

        except Exception as e:
            print(f"[WARNING] Error in crawl_naver_news attempt {attempt_count}: {e}")
            break

    df = pd.DataFrame(items, columns=["날짜", "매체명", "검색키워드", "기사제목", "주요기사 요약", "URL"])

    # API 할당량 초과 정보 저장
    if quota_exceeded:
        df.attrs['quota_exceeded'] = True

    if not df.empty:
        # 최신순 정렬
        df["날짜_datetime"] = pd.to_datetime(df["날짜"], errors="coerce")
        df = df.sort_values("날짜_datetime", ascending=False, na_position="last").reset_index(drop=True)
        df = df.drop("날짜_datetime", axis=1)

        # 중복 제거
        key = df["URL"].where(df["URL"].astype(bool), df["기사제목"] + "|" + df["날짜"])
        df = df.loc[~key.duplicated()].reset_index(drop=True)
    return df


# ======================== DB 함수 ========================

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

    # 상위 200개만 저장
    out = df.head(200).copy()

    # data 폴더 생성
    os.makedirs(DATA_FOLDER, exist_ok=True)

    out.to_csv(NEWS_DB_FILE, index=False, encoding="utf-8")
    print(f"[DEBUG] news saved: {len(out)} rows -> {NEWS_DB_FILE}")


# ======================== 캐시 함수 ========================

def load_sent_cache() -> set:
    """전송된 기사 캐시를 파일에서 로드 (TTL 적용)"""
    if os.path.exists(SENT_CACHE_FILE):
        try:
            with open(SENT_CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # TTL 지원 여부 확인
                if "url_timestamps" in data:
                    # TTL 기반 캐시 (타임스탬프 포함)
                    from datetime import timedelta
                    url_timestamps = data.get("url_timestamps", {})
                    ttl_days = data.get("ttl_days", 7)
                    now = datetime.now()
                    cutoff_time = now - timedelta(days=ttl_days)

                    # 유효한 URL만 로드
                    valid_urls = set()
                    expired_count = 0
                    for url, timestamp_str in url_timestamps.items():
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                            if timestamp > cutoff_time:
                                valid_urls.add(url)
                            else:
                                expired_count += 1
                        except Exception:
                            # 타임스탬프 파싱 실패 시 포함 (안전 장치)
                            valid_urls.add(url)

                    if expired_count > 0:
                        print(f"[DEBUG] TTL 만료 URL 제거: {expired_count}건")

                    print(f"[DEBUG] 전송 캐시 로드 완료: {len(valid_urls)}건 (TTL: {ttl_days}일)")
                    return valid_urls
                else:
                    # 레거시 캐시 (타임스탬프 없음)
                    cache = set(data.get("urls", []))
                    print(f"[DEBUG] 전송 캐시 로드 완료 (레거시): {len(cache)}건")
                    return cache

        except Exception as e:
            print(f"[WARNING] 전송 캐시 로드 실패: {e}")
            return set()
    else:
        print(f"[DEBUG] 전송 캐시 파일 없음 - 새로 생성")
        return set()


def save_sent_cache(cache: set, ttl_days: int = 7):
    """
    전송된 기사 캐시를 파일에 저장 (TTL 기반, 원자적 쓰기)

    Args:
        cache: 저장할 URL 캐시
        ttl_days: TTL (Time To Live) 일수 (기본: 7일)
    """
    try:
        from datetime import timedelta
        import tempfile
        os.makedirs(DATA_FOLDER, exist_ok=True)

        # 기존 캐시 로드 (타임스탬프 유지)
        existing_timestamps = {}
        if os.path.exists(SENT_CACHE_FILE):
            try:
                with open(SENT_CACHE_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_timestamps = existing_data.get("url_timestamps", {})
            except Exception:
                pass

        # 현재 시간
        now = datetime.now()
        cutoff_time = now - timedelta(days=ttl_days)

        # URL 타임스탬프 업데이트
        url_timestamps = {}
        for url in cache:
            if url in existing_timestamps:
                # 기존 타임스탬프 유지
                try:
                    timestamp = datetime.fromisoformat(existing_timestamps[url])
                    if timestamp > cutoff_time:
                        url_timestamps[url] = existing_timestamps[url]
                    else:
                        # 만료된 경우 현재 시간으로 갱신
                        url_timestamps[url] = now.isoformat()
                except Exception:
                    url_timestamps[url] = now.isoformat()
            else:
                # 신규 URL은 현재 시간
                url_timestamps[url] = now.isoformat()

        # 최신 MAX_SENT_CACHE개만 유지 (타임스탬프 기준)
        if len(url_timestamps) > MAX_SENT_CACHE:
            sorted_urls = sorted(url_timestamps.items(), key=lambda x: x[1], reverse=True)
            url_timestamps = dict(sorted_urls[:MAX_SENT_CACHE])

        data = {
            "url_timestamps": url_timestamps,
            "urls": list(url_timestamps.keys()),  # 하위 호환성
            "last_updated": now.strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(url_timestamps),
            "ttl_days": ttl_days
        }

        # 원자적 쓰기 (임시 파일 + rename)
        # 동시 쓰기 시에도 파일 손상 방지
        temp_fd, temp_path = tempfile.mkstemp(dir=DATA_FOLDER, suffix='.tmp')
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # Windows에서는 기존 파일 삭제 필요
            if os.path.exists(SENT_CACHE_FILE):
                try:
                    os.remove(SENT_CACHE_FILE)
                except Exception:
                    pass

            # 임시 파일을 최종 파일로 이동 (원자적 연산)
            os.replace(temp_path, SENT_CACHE_FILE)

            print(f"[DEBUG] 전송 캐시 저장 완료: {len(url_timestamps)}건 (TTL: {ttl_days}일) -> {SENT_CACHE_FILE}")
        except Exception as e:
            # 임시 파일 정리
            try:
                os.remove(temp_path)
            except Exception:
                pass
            raise e
    except Exception as e:
        print(f"[WARNING] 전송 캐시 저장 실패: {e}")


# ======================== API 할당량 관리 ========================

def load_api_usage() -> int:
    """오늘 API 사용량 로드"""
    if os.path.exists(API_USAGE_FILE):
        try:
            with open(API_USAGE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                today = datetime.now().strftime("%Y-%m-%d")
                if data.get("date") == today:
                    return data.get("count", 0)
        except Exception as e:
            print(f"[WARNING] API 사용량 로드 실패: {e}")
    return 0


def save_api_usage(count: int):
    """오늘 API 사용량 저장"""
    try:
        os.makedirs(DATA_FOLDER, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        data = {
            "date": today,
            "count": count,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "quota_remaining": MAX_API_CALLS_PER_DAY - count,
            "quota_percentage": (count / MAX_API_CALLS_PER_DAY) * 100
        }
        with open(API_USAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] API 사용량 저장: {count}/{MAX_API_CALLS_PER_DAY} ({data['quota_percentage']:.1f}%)")
    except Exception as e:
        print(f"[WARNING] API 사용량 저장 실패: {e}")


def increment_api_usage(calls: int = 1) -> int:
    """API 사용량 증가 및 현재 사용량 반환"""
    current = load_api_usage()
    new_count = current + calls
    save_api_usage(new_count)
    return new_count


def check_api_quota(required_calls: int = 1) -> bool:
    """
    API 할당량 확인

    Args:
        required_calls: 필요한 API 호출 횟수

    Returns:
        True: 할당량 여유 있음, False: 할당량 부족
    """
    current = load_api_usage()
    remaining = MAX_API_CALLS_PER_DAY - current

    if remaining < required_calls:
        print(f"[WARNING] ⚠️ API 할당량 부족: 남은 호출 {remaining}회, 필요 {required_calls}회")
        return False

    if current >= API_QUOTA_WARNING_THRESHOLD:
        print(f"[WARNING] ⚠️ API 할당량 80% 도달: {current}/{MAX_API_CALLS_PER_DAY} ({(current/MAX_API_CALLS_PER_DAY)*100:.1f}%)")

    return True


# ======================== 초기화 상태 관리 ========================

def is_first_run() -> bool:
    """첫 실행 여부 확인 (상태 파일 기준)"""
    if not os.path.exists(STATE_FILE):
        return True

    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
            return not state.get("initialized", False)
    except Exception as e:
        print(f"[WARNING] 상태 파일 로드 실패: {e}")
        return True


def mark_initialized():
    """초기화 완료 표시"""
    try:
        os.makedirs(DATA_FOLDER, exist_ok=True)
        state = {
            "initialized": True,
            "first_run_date": datetime.now().isoformat(),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] 시스템 초기화 완료 표시")
    except Exception as e:
        print(f"[WARNING] 상태 파일 저장 실패: {e}")


# ======================== 신규 기사 감지 ========================

def detect_new_articles(old_df: pd.DataFrame, new_df: pd.DataFrame, sent_cache: set) -> list:
    """
    기존 DB와 새로운 데이터를 비교하여 신규 기사 감지
    - URL을 우선 식별자로 사용
    - 캐시와 DB 중복 체크
    """
    try:
        # 첫 실행 체크 (상태 파일 기준)
        if is_first_run():
            print(f"[DEBUG] 첫 실행 감지 - 알림 스킵하고 초기화")
            mark_initialized()
            return []

        # DB가 비어있지만 첫 실행이 아니면 경고 (데이터 손실 가능성)
        if old_df.empty and not is_first_run():
            print(f"[WARNING] ⚠️ DB가 비어있지만 첫 실행이 아님 - 데이터 손실 가능성")
            # 이 경우에도 신규 기사로 처리 (복구 목적)

        if new_df.empty:
            return []

        # 현재 시간 기준 (KST)
        KST = timezone(timedelta(hours=9))
        now = datetime.now(KST).replace(tzinfo=None)  # KST 시간을 naive datetime으로

        # 기존 DB의 URL 세트 생성 (정규화된 URL 사용)
        old_urls = set()
        old_urls_normalized = set()
        for _, row in old_df.iterrows():
            url = str(row.get("URL", "")).strip()
            if url and url != "nan" and url != "":
                old_urls.add(url)
                old_urls_normalized.add(_normalize_url(url))

        print(f"[DEBUG] 기존 DB URL 수: {len(old_urls)} (정규화: {len(old_urls_normalized)})")
        print(f"[DEBUG] 캐시 크기: {len(sent_cache)}건")
        print(f"[DEBUG] 수집된 신규 데이터 수: {len(new_df)}")

        # 신규 기사 감지 (시간 필터링 추가)
        new_articles = []
        MAX_ARTICLE_AGE_HOURS = 48  # 최근 48시간 이내 기사만 알림

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
            is_in_cache = url in sent_cache or url_normalized in sent_cache

            if is_in_db or is_in_cache:
                continue

            # 신규 기사 - 날짜 필터링 (개선됨)
            article_date_str = row.get("날짜", "")
            should_notify = True  # 기본값: 신규 기사면 알림
            hours_diff = None

            try:
                article_date = pd.to_datetime(article_date_str, errors="coerce")
                if pd.notna(article_date):
                    time_diff = now - article_date
                    hours_diff = time_diff.total_seconds() / 3600

                    # 시간 기반 필터링: 최근 48시간 이내만 알림
                    if hours_diff <= MAX_ARTICLE_AGE_HOURS:
                        print(f"[DEBUG] ✅ 신규 기사 감지: {title[:50]}... ({hours_diff:.1f}시간 전)")
                    else:
                        print(f"[DEBUG] ⏭️ 오래된 기사 스킵: {title[:50]}... ({hours_diff:.1f}시간 전, {hours_diff/24:.1f}일 전)")
                        continue  # 너무 오래된 기사는 알림 스킵
                else:
                    # 날짜 파싱 실패 시에도 신규 기사로 처리 (개선!)
                    print(f"[DEBUG] ⚠️ 날짜 파싱 실패, 하지만 신규 기사로 알림: {title[:50]}... (날짜: {article_date_str})")
            except Exception as e:
                # 예외 발생 시에도 신규 기사로 처리 (개선!)
                print(f"[DEBUG] ⚠️ 날짜 처리 오류, 하지만 신규 기사로 알림: {title[:50]}... - {str(e)}")

            # 매체명과 키워드 추출
            press = _publisher_from_link(url)
            keyword = str(row.get("검색키워드", "")).strip()

            new_articles.append({
                "title": title if title and title != "nan" else "제목 없음",
                "link": url,
                "date": article_date_str,
                "press": press,
                "keyword": keyword
            })

        print(f"[DEBUG] 총 {len(new_articles)}건의 신규 기사 감지 (DB+캐시 중복 제거)")
        return new_articles

    except Exception as e:
        print(f"[DEBUG] 신규 기사 감지 오류: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류:\n{traceback.format_exc()}")
        return []


# ======================== 텔레그램 알림 ========================

def send_telegram_notification(new_articles: list, sent_cache: set) -> set:
    """
    새로운 기사를 텔레그램으로 알림 전송 (기사별 개별 메시지)

    - 모든 신규 기사를 텔레그램으로 전송 (개수 제한 없음)
    - 각 기사마다 3회까지 재시도
    - 텔레그램 API Rate Limit 준수 (초당 약 28개)
    - 전송 성공한 기사만 캐시에 추가하여 재전송 방지

    Returns: 업데이트된 sent_cache (전송 성공한 기사 URL 포함)
    """
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        print(f"[DEBUG] 텔레그램 알림 시도 - 기사 수: {len(new_articles) if new_articles else 0}")

        # 환경변수가 없으면 알림 스킵
        if not bot_token or not chat_id:
            print("[DEBUG] ⚠️ 텔레그램 설정 없음 - 알림 스킵")
            return sent_cache

        if not new_articles:
            print("[DEBUG] 신규 기사 없음 - 알림 스킵")
            return sent_cache

        # 이미 전송된 기사 필터링
        articles_to_send = []
        skipped_already_sent = 0
        for article in new_articles:
            url_key = article.get("link", "")
            url_normalized = _normalize_url(url_key)

            if url_key and url_key not in sent_cache and url_normalized not in sent_cache:
                articles_to_send.append(article)
            else:
                skipped_already_sent += 1
                print(f"[DEBUG] 📤 이미 전송된 기사 스킵: {article.get('title', '')[:50]}...")

        if not articles_to_send:
            print(f"[DEBUG] 모든 기사가 이미 전송됨 - 알림 스킵 (스킵된 기사: {skipped_already_sent}건)")
            return sent_cache

        print(f"[DEBUG] 전송 대상: {len(articles_to_send)}건 (이미 전송: {skipped_already_sent}건)")

        # 모든 신규 기사를 텔레그램으로 전송 (제한 없음)
        articles_to_notify = articles_to_send
        print(f"[DEBUG] 📤 총 {len(articles_to_notify)}건의 기사를 텔레그램으로 전송합니다.")

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

            # 메시지 구성
            message = f"🚨 *새 뉴스*\n\n"
            if keyword:
                hashtag = keyword.replace(" ", "")
                message += f"#{hashtag}\n"
            if press:
                message += f"*[{press}]* {title}\n"
            else:
                message += f"*{title}*\n"
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

            response = None
            # 재시도 로직 (최대 3회)
            max_retries = 3
            retry_delay = 1  # 초

            for attempt in range(max_retries):
                try:
                    response = requests.post(url, json=payload, timeout=10)
                    if response.status_code == 200:
                        success_count += 1
                        print(f"[DEBUG] ✅ 메시지 전송 성공: {title[:30]}...")

                        # 전송 성공한 기사는 캐시에 추가
                        sent_cache.add(link)
                        sent_cache.add(_normalize_url(link))
                        break  # 성공하면 재시도 루프 탈출
                    else:
                        print(f"[DEBUG] ❌ 메시지 전송 실패 (시도 {attempt + 1}/{max_retries}): {response.status_code}")
                        if attempt < max_retries - 1:
                            import time
                            time.sleep(retry_delay * (attempt + 1))  # 지수 백오프

                except Exception as e:
                    print(f"[DEBUG] ❌ 개별 메시지 전송 오류 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay * (attempt + 1))  # 지수 백오프
                    else:
                        # 마지막 시도에서도 실패하면 상세 오류 출력
                        import traceback
                        print(f"[DEBUG] 최종 실패 - 상세 오류:\n{traceback.format_exc()}")
                finally:
                    # 연결 누수 방지
                    if response is not None:
                        response.close()

            # Rate Limit 방지 (텔레그램 API: 초당 30개 제한)
            # 35ms 대기 = 초당 약 28개로 안전한 속도 유지
            import time
            time.sleep(0.035)

        # 전송 결과 통계
        failed_count = len(articles_to_notify) - success_count
        if failed_count > 0:
            print(f"[DEBUG] ⚠️ 전송 실패: {failed_count}건")
            print(f"[DEBUG] 실패한 기사는 다음 수집 사이클에 재시도됩니다.")

        print(f"[DEBUG] ✅ 총 {success_count}/{len(articles_to_notify)}건 전송 완료 (성공률: {success_count/len(articles_to_notify)*100:.1f}%)")

        return sent_cache

    except Exception as e:
        print(f"[DEBUG] ❌ 텔레그램 알림 예외 발생: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류:\n{traceback.format_exc()}")
        return sent_cache


# ======================== 시스템 상태 관리 ========================

RUN_STATUS_FILE = os.path.join(DATA_FOLDER, "run_status.json")


def update_run_status(success: bool, articles_collected: int, new_articles: int,
                      telegram_sent: int, error_message: str = None):
    """
    실행 상태 업데이트 및 연속 실패 추적

    Args:
        success: 실행 성공 여부
        articles_collected: 수집된 기사 수
        new_articles: 신규 기사 수
        telegram_sent: 텔레그램 발송 수
        error_message: 에러 메시지 (실패 시)
    """
    try:
        os.makedirs(DATA_FOLDER, exist_ok=True)

        # 기존 상태 로드
        status_data = {
            "consecutive_failures": 0,
            "last_success_time": None,
            "total_runs": 0,
            "total_failures": 0
        }

        if os.path.exists(RUN_STATUS_FILE):
            try:
                with open(RUN_STATUS_FILE, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
            except Exception:
                pass

        # 상태 업데이트
        now = datetime.now()
        status_data["total_runs"] = status_data.get("total_runs", 0) + 1
        status_data["last_run_time"] = now.isoformat()

        if success:
            status_data["consecutive_failures"] = 0
            status_data["last_success_time"] = now.isoformat()
            status_data["last_success_stats"] = {
                "articles_collected": articles_collected,
                "new_articles": new_articles,
                "telegram_sent": telegram_sent
            }
        else:
            status_data["consecutive_failures"] = status_data.get("consecutive_failures", 0) + 1
            status_data["total_failures"] = status_data.get("total_failures", 0) + 1
            status_data["last_error"] = error_message

        # 파일 저장
        with open(RUN_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        # 연속 실패 경고
        if status_data["consecutive_failures"] >= 3:
            send_system_alert(
                f"🚨 *연속 {status_data['consecutive_failures']}회 실패*\n\n"
                f"뉴스 수집 시스템이 연속으로 실패하고 있습니다.\n"
                f"마지막 에러: {error_message or '알 수 없음'}"
            )

        print(f"[DEBUG] 실행 상태 업데이트: 연속 실패 {status_data['consecutive_failures']}회")

    except Exception as e:
        print(f"[WARNING] 실행 상태 업데이트 실패: {e}")


def check_api_quota_and_alert():
    """
    API 할당량 확인 및 경고 알림

    Returns:
        bool: API 사용 가능 여부
    """
    try:
        usage = load_api_usage()
        remaining = MAX_API_CALLS_PER_DAY - usage
        usage_percent = (usage / MAX_API_CALLS_PER_DAY) * 100

        print(f"[DEBUG] API 사용량: {usage:,}/{MAX_API_CALLS_PER_DAY:,} ({usage_percent:.1f}%)")

        # 80% 도달 시 경고
        if usage >= API_QUOTA_WARNING_THRESHOLD and usage < (API_QUOTA_WARNING_THRESHOLD + 100):
            send_system_alert(
                f"⚠️ *API 할당량 경고*\n\n"
                f"Naver API 사용량: {usage:,}/{MAX_API_CALLS_PER_DAY:,}\n"
                f"사용률: {usage_percent:.1f}%\n"
                f"남은 호출 수: {remaining:,}"
            )

        # 95% 도달 시 긴급 경고
        elif usage >= (MAX_API_CALLS_PER_DAY * 0.95):
            send_system_alert(
                f"🚨 *API 할당량 긴급*\n\n"
                f"사용량이 95%를 초과했습니다!\n"
                f"사용: {usage:,}/{MAX_API_CALLS_PER_DAY:,}\n"
                f"일부 키워드 수집이 중단될 수 있습니다."
            )

        return usage < MAX_API_CALLS_PER_DAY

    except Exception as e:
        print(f"[WARNING] API 할당량 확인 실패: {e}")
        return True


def send_system_alert(message: str):
    """
    시스템 알림 전송 (중복 방지 포함)

    Args:
        message: 알림 메시지
    """
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        if not bot_token or not chat_id:
            return

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }

        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[DEBUG] ✅ 시스템 알림 전송 성공")
        else:
            print(f"[DEBUG] ❌ 시스템 알림 전송 실패: {response.status_code}")

        response.close()

    except Exception as e:
        print(f"[DEBUG] ❌ 시스템 알림 예외: {e}")
