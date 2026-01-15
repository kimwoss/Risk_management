# streamlit_app.py
# Version: 2025-12-02-10:45 (Publisher mapping update trigger)
"""
포스코인터내셔널 언론대응 보고서 생성 시스템
- 상단 네비: 순수 Streamlit 버튼 기반 (iFrame/JS 제거, 확실한 리런)
- 중복된 로더/스타일 정리
"""
import os, json, re, time, base64, mimetypes, urllib.parse, requests
from datetime import datetime, timezone, timedelta
import threading
import atexit

# 공통 뉴스 수집 모듈 import
from news_collector import (
    KEYWORDS,
    EXCLUDE_KEYWORDS,
    MAX_ITEMS_PER_RUN,
    crawl_naver_news,
    load_news_db,
    _publisher_from_link,
    _clean_text,
    _naver_headers,
)

# APScheduler import with error handling
# 🚨 DISABLED: GitHub Actions로 대체 - 중복 알림 방지
SCHEDULER_AVAILABLE = False
print("[INFO] 백그라운드 스케줄러 비활성화 (GitHub Actions 사용)")

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from PIL import Image
from html import unescape
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # NEW

from data_based_llm import DataBasedLLM
from components.status_dashboard import render_status_dashboard
from components.publisher_dashboard import render_publisher_dashboard
from components.news_dashboard import render_news_dashboard

# 지원 여부 플래그
SUPPORTS_FRAGMENT = hasattr(st, "fragment")
# from llm_manager import LLMManager  # 사용하지 않아 주석처리 (원하면 복구)

# 안전한 print 함수 정의
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except (UnicodeEncodeError, OSError):
        try:
            print("[DEBUG] Print encoding issue")
        except:
            pass

# .env 파일 로드 및 디버깅
env_loaded = load_dotenv()
try:
    print("[DEBUG] .env file loaded:", env_loaded)
    print("[DEBUG] Environment variables loaded from:", os.getcwd())

    # 환경변수 직접 확인
    naver_id = os.getenv("NAVER_CLIENT_ID", "")
    naver_secret = os.getenv("NAVER_CLIENT_SECRET", "")
    print("[DEBUG] Initial env check - ID exists:", bool(naver_id), "Secret exists:", bool(naver_secret))
except Exception as e:
    print("DEBUG print error:", str(e))

# ----------------------------- 기본 설정 -----------------------------
st.set_page_config(
    page_title="위기관리커뮤니케이션 AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------- 전역 CSS (iframe 전체 폭 강제) -----------------------------
st.markdown("""
<style>
/* Streamlit components.html iframe을 전체 폭으로 강제 */
iframe[title] {
    width: 100% !important;
    max-width: 100% !important;
}

/* 대시보드 iframe을 위한 추가 스타일 */
.stApp iframe {
    width: 100% !important;
}

/* Block 컨테이너 전체 폭 사용 */
.block-container {
    max-width: 100%;
    padding-left: 2rem;
    padding-right: 2rem;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------- 인증 설정 -----------------------------
ACCESS_CODE = "pointl"  # 비밀코드
import hashlib

def get_auth_token():
    """인증 토큰 생성 (보안을 위해 해시 사용)"""
    return hashlib.sha256(f"{ACCESS_CODE}_secret_salt".encode()).hexdigest()

def check_cookie_auth():
    """쿠키에서 인증 정보 확인"""
    auth_token = get_auth_token()

    # JavaScript로 쿠키 확인
    cookie_script = f"""
    <script>
        function getCookie(name) {{
            const value = `; ${{document.cookie}}`;
            const parts = value.split(`; ${{name}}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }}

        const authToken = getCookie('posco_auth_token');
        const authTokenValue = '{auth_token}';

        if (authToken === authTokenValue) {{
            // 인증 성공 - URL 파라미터로 전달
            if (!window.location.search.includes('auto_login=1')) {{
                const url = new URL(window.location);
                url.searchParams.set('auto_login', '1');
                window.location.href = url.toString();
            }}
        }}
    </script>
    """
    st.components.v1.html(cookie_script, height=0)

    # URL 파라미터 확인
    if st.query_params.get("auto_login") == "1":
        st.session_state.authenticated = True
        # 파라미터 제거 (깔끔한 URL 유지)
        st.query_params.clear()
        return True

    return False

def check_authentication():
    """인증 확인 함수 (쿠키 + 세션)"""
    # 이미 세션에서 인증됨
    if st.session_state.get("authenticated", False):
        return True

    # 쿠키에서 인증 확인
    if check_cookie_auth():
        return True

    return False

def show_login_page():
    """로그인 페이지 표시 - Genesis 스타일"""
    # 베이스 CSS 로드
    st.markdown("""
    <style>
      /* 배경/폰트 */
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700&display=swap');
      [data-testid="stAppViewContainer"]{
        background: linear-gradient(180deg,#0c0d10 0%, #0a0b0d 100%) !important;
        color:#eee; font-family:'Inter','Noto Sans KR',system-ui,Segoe UI,Roboto,Apple SD Gothic Neo,Pretendard,sans-serif;
      }
      [data-testid="stHeader"]{background:transparent; height:0;}
      section[data-testid="stSidebar"] {display:none !important;}

      /* 중앙 고정 오버레이 */
      .login-overlay {
        position: fixed;
        inset: 0;
        display: grid;
        place-items: center;
        padding: 24px;
        z-index: 1;
        pointer-events: none;
      }
      .login-box {
        background: linear-gradient(135deg, rgba(24,24,28,.75), rgba(16,16,20,.9));
        border: 1px solid rgba(212,175,55,.25);
        border-radius: 16px;
        padding: 48px 40px;
        max-width: 520px;
        width: 100%;
        box-shadow: 0 12px 48px rgba(0,0,0,.4), 0 1px 0 rgba(255,255,255,.06) inset;
        backdrop-filter: blur(12px);
        text-align: center;
        pointer-events: auto;
        position: relative;
        z-index: 2;
      }

      /* 입력/버튼 폭 제한 컨테이너 */
      .login-form-wrapper {
        max-width: 420px;
        margin: 0 auto;
      }
      .login-logo {
        font-size: 56px;
        margin-bottom: 16px;
        filter: drop-shadow(0 4px 12px rgba(212,175,55,.2));
      }
      .login-title {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 8px;
        color: #fff;
        letter-spacing: -0.02em;
      }
      .login-subtitle {
        font-size: 15px;
        color: rgba(255,255,255,.6);
        margin-bottom: 36px;
        font-weight: 400;
      }

      /* 입력 필드 스타일 */
      .stTextInput>div>div>input {
        background: rgba(0,0,0,.4) !important;
        border: 1px solid rgba(255,255,255,.2) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
        padding: 14px 16px !important;
        font-size: 15px !important;
        transition: all 0.25s ease !important;
        position: relative !important;
        z-index: 3 !important;
        caret-color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
      }
      .stTextInput>div>div>input:focus {
        border-color: rgba(212,175,55,.6) !important;
        box-shadow: 0 0 0 2px rgba(212,175,55,.15) !important;
        background: rgba(0,0,0,.5) !important;
        color: #ffffff !important;
      }
      .stTextInput>div>div>input::placeholder {
        color: rgba(255,255,255,.4) !important;
      }
      .stTextInput>div>div>input:-webkit-autofill,
      .stTextInput>div>div>input:-webkit-autofill:hover,
      .stTextInput>div>div>input:-webkit-autofill:focus {
        -webkit-text-fill-color: #ffffff !important;
        -webkit-box-shadow: 0 0 0px 1000px rgba(0,0,0,.5) inset !important;
        transition: background-color 5000s ease-in-out 0s !important;
      }
      .stTextInput {
        position: relative !important;
        z-index: 3 !important;
      }

      /* 로그인 버튼 */
      .stButton>button {
        background: linear-gradient(135deg, #D4AF37, #B8941F) !important;
        border: 1px solid rgba(212,175,55,.4) !important;
        border-radius: 10px !important;
        color: #000 !important;
        font-weight: 700 !important;
        padding: 14px 24px !important;
        font-size: 16px !important;
        letter-spacing: 0.02em !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 16px rgba(212,175,55,.2) !important;
        position: relative !important;
        z-index: 3 !important;
        cursor: pointer !important;
      }
      .stButton>button:hover {
        background: linear-gradient(135deg, #E6C55A, #D4AF37) !important;
        border-color: rgba(212,175,55,.8) !important;
        box-shadow: 0 6px 24px rgba(212,175,55,.35) !important;
        transform: translateY(-1px) !important;
      }
      .stButton {
        position: relative !important;
        z-index: 3 !important;
      }

      /* 에러 메시지 */
      .stAlert {
        background: rgba(220,38,38,.15) !important;
        border: 1px solid rgba(220,38,38,.3) !important;
        border-radius: 8px !important;
        color: #fca5a5 !important;
      }

      /* 모바일 최적화 (로그인 페이지) */
      @media (max-width: 768px) {
        .login-box {
          padding: 32px 24px !important;
          max-width: 90% !important;
        }
        .login-logo {
          font-size: 48px !important;
        }
        .login-title {
          font-size: 24px !important;
        }
        .login-subtitle {
          font-size: 14px !important;
        }
      }

      @media (max-width: 480px) {
        .login-box {
          padding: 24px 20px !important;
        }
        .login-logo {
          font-size: 40px !important;
        }
        .login-title {
          font-size: 20px !important;
        }
        .login-subtitle {
          font-size: 13px !important;
          margin-bottom: 24px !important;
        }
      }
    </style>
    """, unsafe_allow_html=True)

    # 중앙 고정 오버레이로 감싸기
    st.markdown('<div class="login-overlay">', unsafe_allow_html=True)

    # 컬럼 없이 바로 박스 렌더링
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<div class="login-logo">🛡️</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-title">위기관리커뮤니케이션 AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">포스코인터내셔널 언론대응 시스템</div>', unsafe_allow_html=True)

    # 폼 래퍼로 입력/버튼 폭 제한
    st.markdown('<div class="login-form-wrapper">', unsafe_allow_html=True)

    # st.form을 사용하여 엔터 키로 제출 가능하도록 개선
    with st.form(key="login_form", clear_on_submit=False):
        st.markdown('<div style="margin-bottom: 12px; text-align: left; color: rgba(255,255,255,.7); font-size: 13px; font-weight: 600;">비밀코드</div>', unsafe_allow_html=True)
        code_input = st.text_input(
            "비밀코드",
            type="password",
            placeholder="비밀코드를 입력하세요",
            label_visibility="collapsed",
            key="login_code_input"
        )

        st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
        submit_button = st.form_submit_button("로그인", use_container_width=True)

    # 폼 제출 처리 (엔터 키 또는 버튼 클릭)
    if submit_button:
        if code_input == ACCESS_CODE:
            # 1단계: 세션 상태 즉시 설정 (우선순위 최상위)
            st.session_state.authenticated = True
            st.session_state.login_pending_cookie = True

            # 2단계: 쿠키 설정 (백그라운드, 비동기)
            auth_token = get_auth_token()
            set_cookie_script = f"""
            <script>
                (function() {{
                    const days = 30;
                    const date = new Date();
                    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
                    const expires = "expires=" + date.toUTCString();
                    document.cookie = "posco_auth_token={auth_token}; " + expires + "; path=/; SameSite=Lax";
                }})();
            </script>
            """
            st.components.v1.html(set_cookie_script, height=0)

            # 3단계: 즉시 리런 (세션 상태 기반으로 메인 화면 표시)
            st.rerun()
        else:
            st.error("잘못된 비밀코드입니다. 다시 시도해주세요.")

    st.markdown('</div>', unsafe_allow_html=True)  # </div class="login-form-wrapper">
    st.markdown('</div>', unsafe_allow_html=True)  # </div class="login-box">
    st.markdown('</div>', unsafe_allow_html=True)  # </div class="login-overlay">

DATA_FOLDER = os.path.abspath("data")
MASTER_DATA_FILE = os.path.join(DATA_FOLDER, "master_data.json")
MEDIA_RESPONSE_FILE = os.path.join(DATA_FOLDER, "언론대응내역.csv")
NEWS_DB_FILE = os.path.join(DATA_FOLDER, "news_monitor.csv")
try:
    print("[DEBUG] NEWS_DB_FILE:", NEWS_DB_FILE)
except:
    pass

# ----------------------------- 캐시 로더(단일) -----------------------------
@st.cache_data
def _load_json_with_key(path: str, _cache_key: float) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_master_data():
    try:
        mtime = os.path.getmtime(MASTER_DATA_FILE)
    except OSError:
        mtime = 0.0
    return _load_json_with_key(MASTER_DATA_FILE, mtime)

def load_master_data_fresh():
    """캐시 없이 항상 최신 데이터를 로드"""
    try:
        print(f"[DEBUG] 캐시 없이 직접 로드: {MASTER_DATA_FILE}")
        with open(MASTER_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[DEBUG] 로드된 데이터 키: {list(data.keys())}")
        print(f"[DEBUG] 언론사 수: {len(data.get('media_contacts', {}))}")
        return data
    except Exception as e:
        print(f"[DEBUG] 직접 로드 실패: {e}")
        return {}

def clear_data_cache():
    """캐시를 클리어하는 함수"""
    try:
        # Streamlit 캐시 완전 초기화
        st.cache_data.clear()
        st.cache_resource.clear()
        
        # 개별 함수 캐시도 클리어
        if hasattr(_load_json_with_key, 'clear'):
            _load_json_with_key.clear()
        if hasattr(_load_csv_with_key, 'clear'):
            _load_csv_with_key.clear()
            
        # 세션 상태도 초기화
        if 'master_data_cache' in st.session_state:
            del st.session_state['master_data_cache']
            
        print("[DEBUG] 캐시가 완전히 클리어되었습니다.")
        
    except Exception as e:
        print(f"[DEBUG] 캐시 클리어 중 오류: {e}")

@st.cache_data
def _load_csv_with_key(path: str, _cache_key: float) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="utf-8")
    except Exception:
        return pd.DataFrame()

def load_media_response_data():
    try:
        mtime = os.path.getmtime(MEDIA_RESPONSE_FILE)
        fsize = os.path.getsize(MEDIA_RESPONSE_FILE)
        # 파일 크기와 수정 시간을 조합하여 캐시 키 생성 (더 강력한 캐시 무효화)
        cache_key = mtime + (fsize / 1000000.0)  # 크기를 MB 단위로 변환하여 추가
    except OSError:
        cache_key = 0.0
    return _load_csv_with_key(MEDIA_RESPONSE_FILE, cache_key)

# ----------------------------- 데이터 API -----------------------------
def get_media_contacts():
    return load_master_data().get("media_contacts", {})

def search_media_info(media_name: str):
    try:
        # 최신 데이터 로드 (캐시 없이)
        master_data = load_master_data_fresh()
        media_contacts = master_data.get("media_contacts", {})
        
        if not media_contacts:
            return None

        # 1차: 완전 일치
        if media_name in media_contacts:
            md = media_contacts[media_name]
        else:
            # 2차: 부분 일치 검색
            matched_key = None
            for key in media_contacts.keys():
                if media_name in key or key in media_name:
                    matched_key = key
                    break
            
            if matched_key:
                md = media_contacts[matched_key]
                media_name = matched_key  # 매치된 키로 업데이트
            else:
                return None
        
        # 출입기자 데이터 처리 (새로운 구조와 기존 구조 모두 지원)
        reporters = md.get("출입기자", [])
        processed_reporters = []
        
        for reporter in reporters:
            if isinstance(reporter, dict):
                # 새로운 구조 (딕셔너리) - 빈 필드는 공백으로 처리
                processed_reporter = {
                    "이름": reporter.get("이름", ""),
                    "직책": reporter.get("직책", ""),
                    "연락처": reporter.get("연락처", ""),
                    "이메일": reporter.get("이메일", "")
                }
                processed_reporters.append(processed_reporter)
            else:
                # 기존 구조 (문자열)
                processed_reporters.append({
                    "이름": reporter,
                    "직책": "",
                    "연락처": "", 
                    "이메일": ""
                })
        
        return {
            "name": media_name,
            "type": md.get("구분", "N/A"),
            "contact_person": md.get("담당자", "N/A"),
            "main_phone": md.get("대표연락처", "N/A"),
            "fax": md.get("팩스", "N/A"),
            "address": md.get("주소", "N/A"),
            "desk": md.get("DESK", []),
            "reporters": processed_reporters,
            "raw_data": md,
        }
    except Exception as e:
        st.error(f"언론사 정보 검색 오류: {e}")
        return None

def generate_issue_report(media_name, reporter_name, issue_description):
    try:
        data_llm = DataBasedLLM()
        return data_llm.generate_issue_report(media_name, reporter_name, issue_description)
    except Exception as e:
        return f"보고서 생성 중 오류: {str(e)}"

# ----------------------------- 뉴스 유틸 -----------------------------
def _naver_headers():
    cid = os.getenv("NAVER_CLIENT_ID", "")
    csec = os.getenv("NAVER_CLIENT_SECRET", "")
    print(f"[DEBUG] NAVER_CLIENT_ID: '{cid[:10]}...' (length: {len(cid)})")
    print(f"[DEBUG] NAVER_CLIENT_SECRET: '{csec[:5]}...' (length: {len(csec)})")
    if not cid or not csec:
        st.error("네이버 API 키가 없습니다. .env를 확인해주세요.")
        print(f"[DEBUG] Missing API keys - ID: {bool(cid)}, Secret: {bool(csec)}")
    return {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec}

def _clean_text(s: str) -> str:
    if not s:
        return ""
    s = unescape(s)
    s = re.sub(r"</?b>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _publisher_from_link(u: str) -> str:
    """뉴스 원문 URL에서 매체명을 통일해서 반환한다."""
    try:
        host = urllib.parse.urlparse(u).netloc.lower().replace("www.", "")
        if not host:
            return ""

        # 1) 서브도메인까지 정확 매핑(서브도메인 자체가 매체인 케이스 우선)
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

        # 2) 기본 도메인(eTLD+1) 추출: *.co.kr 등 한국형 2레벨 도메인 처리
        parts = host.split(".")
        if len(parts) >= 3 and parts[-1] == "kr" and parts[-2] in {
            "co","or","go","ne","re","pe","ac","hs","kg","sc",
            "seoul","busan","incheon","daegu","daejeon","gwangju","ulsan",
            "gyeonggi","gangwon","chungbuk","chungnam","jeonbuk","jeonnam",
            "gyeongbuk","gyeongnam","jeju"
        }:
            base = ".".join(parts[-3:])   # 예) en.yna.co.kr → yna.co.kr
        else:
            base = ".".join(parts[-2:])   # 예) starnewskorea.com → starnewskorea.com

        # 3) 기본 도메인 → 매체명 매핑
        base_map = {
            # 주요 종합지 / 방송
            "chosun.com": "조선일보",
            "donga.com": "동아일보",
            "joongang.co.kr": "중앙일보",
            "joins.com": "중앙일보",
            "hani.co.kr": "한겨레",
            "khan.co.kr": "경향신문",
            "mk.co.kr": "매일경제",
            "fnnews.com": "파이낸셜뉴스",
            "hankyung.com": "한국경제",
            "kmib.co.kr": "국민일보",
            "seoul.co.kr": "서울신문",
            "segye.com": "세계일보",
            "naeil.com": "내일신문",
            "imaeil.com": "매일신문",
            "nongmin.com": "농민신문",
            "yeongnam.com": "영남일보",
            "kwnews.co.kr": "강원일보",
            "kado.net": "강원도민일보",
            "kihoilbo.co.kr": "기호일보",
            "ksmnews.co.kr": "경상매일신문",
            "kbmaeil.com": "경북매일",
            "idaegu.co.kr": "IDN대구신문",
            "hidomin.com": "하이도민",
            "incheonilbo.com": "인천일보",
            "incheonnews.com": "인천뉴스",
            "ggilbo.com": "금강일보",
            "joongdo.co.kr": "중도일보",
            "dnews.co.kr": "대한경제",
            "jeonmae.co.kr": "전국매일신문",

            # 방송사
            "kbs.co.kr": "KBS",
            "mbc.co.kr": "MBC",
            "sbs.co.kr": "SBS",
            "ytn.co.kr": "YTN",
            "yonhapnewstv.co.kr": "연합뉴스TV",
            "ifm.kr": "경인방송",
            "kbsm.net": "KBS부산·경남",
            "spotvnews.co.kr": "스포TV",

            # 통신사
            "yna.co.kr": "연합뉴스",
            "news1.kr": "뉴스1",
            "newsis.com": "뉴시스",
            "nocutnews.co.kr": "노컷뉴스",
            "newspim.com": "뉴스핌",

            # 경제 / 금융
            "asiae.co.kr": "아시아경제",
            "heraldcorp.com": "헤럴드경제",
            "herald.co.kr": "헤럴드경제",
            "sedaily.com": "서울경제",
            "etoday.co.kr": "이투데이",
            "edaily.co.kr": "이데일리",
            "bizwatch.co.kr": "비즈워치",
            "businesspost.co.kr": "비즈니스포스트",
            "businesskorea.co.kr": "비즈니스코리아",
            "finomy.com": "현대경제신문",
            "econovill.com": "이코노빌",
            "econonews.co.kr": "이코노뉴스",
            "ezyeconomy.com": "이지경제",
            "queen.co.kr": "이코노미퀸",
            "widedaily.com": "와이드경제",
            "goodkyung.com": "굿모닝경제",
            "smartfn.co.kr": "스마트경제",
            "megaeconomy.co.kr": "메가경제",
            "pointe.co.kr": "포인트경제",
            "pointdaily.co.kr": "포인트데일리",
            "marketnews.co.kr": "마켓뉴스",
            "womaneconomy.co.kr": "여성경제신문",

            # 조선 계열
            "chosunbiz.com": "조선비즈",
            "investchosun.com": "인베스트조선",
            "futurechosun.com": "더나은미래",
            "it.chosun.com": "IT조선",
            "dizzo.com": "디지틀조선일보",
            "economist.co.kr": "이코노미스트",

            # IT / 테크
            "zdnet.co.kr": "지디넷코리아",
            "ddaily.co.kr": "디지털데일리",
            "bloter.net": "블로터",
            "digitaltoday.co.kr": "디지털투데이",
            "thelec.kr": "더일렉",
            "theguru.co.kr": "더구루",
            "techholic.co.kr": "테크홀릭",
            "e-science.co.kr": "e사이언스",
            "e-platform.net": "e플랫폼",
            "irobotnews.com": "로봇신문사",
            "koit.co.kr": "정보통신신문",

            # 정치 / 시사
            "polinews.co.kr": "폴리뉴스",
            "sisajournal.com": "시사저널",
            "sisajournal-e.com": "시사저널e",
            "sisaweek.com": "시사위크",
            "sisaon.co.kr": "시사ON",
            "sisafocus.co.kr": "시사포커스",
            "sisacast.kr": "시사캐스트",
            "sateconomy.co.kr": "시사경제",
            "straightnews.co.kr": "스트레이트뉴스",
            "thepublic.kr": "더퍼블릭",
            "mediapen.com": "미디어펜",
            "newdaily.co.kr": "뉴데일리",
            "breaknews.com": "브레이크뉴스",

            # 온라인 / 기타
            "wikitree.co.kr": "위키트리",
            "insight.co.kr": "인사이트",
            "insightkorea.co.kr": "인사이트코리아",
            "newstapa.org": "뉴스타파",
            "tf.co.kr": "더팩트",
            "newsway.co.kr": "뉴스웨이",
            "newspost.kr": "뉴스포스트",
            "newswatch.kr": "뉴스워치",
            "newsprime.co.kr": "뉴스프라임",
            "newsinside.kr": "뉴스인사이드",
            "news2day.co.kr": "뉴스2데이",
            "newsquest.co.kr": "뉴스퀘스트",
            "newsworker.co.kr": "뉴스워커",
            "newsdream.kr": "뉴스드림",
            "newsbrite.net": "뉴스브라이트",
            "newsmaker.or.kr": "뉴스메이커",

            # 산업 / 에너지
            "ekn.kr": "에너지경제",
            "energy-news.co.kr": "에너지뉴스",
            "energydaily.co.kr": "에너지데일리",
            "todayenergy.kr": "투데이에너지",
            "gasnews.com": "가스신문",
            "epj.co.kr": "일렉트릭파워",
            "amenews.kr": "신소재경제신문",
            "ferrotimes.com": "철강금속신문",

            # 스포츠 / 엔터
            "sportsseoul.com": "스포츠서울",
            "xportsnews.com": "엑스포츠뉴스",
            "starnewskorea.com": "스타뉴스",
            "topstarnews.net": "탑스타뉴스",
            "isplus.com": "일간스포츠",
            "swtvnews.com": "스포츠W",

            # 종교 / 특수
            "bbsi.co.kr": "불교방송",
            "bzeronews.com": "불교공뉴스",

            # 기타
            "kpinews.kr": "KPI뉴스",
            "nbnews.kr": "NBN뉴스",
            "nbntv.co.kr": "NBN뉴스",
            "dkilbo.com": "대경일보",
            "asiatime.co.kr": "아시아타임즈",
            "kukinews.com": "쿠키뉴스",
            "wikileaks-kr.org": "위키리크스한국",
            "thepowernews.co.kr": "더파워",
            "shinailbo.co.kr": "신아일보",
            "pinpointnews.co.kr": "핀포인트뉴스",
            "newsworks.co.kr": "뉴스웍스",
            "newstomato.com": "뉴스토마토",
            "munhwa.com": "문화일보",
            "mt.co.kr": "머니투데이",
            "metroseoul.co.kr": "메트로서울",
            "m-i.kr": "매일일보",
            "lawissue.co.kr": "법률저널",
            "joongangenews.com": "중앙이코노미뉴스",
            "hellot.net": "헬로티",
            "enewstoday.co.kr": "이뉴스투데이",
            "dt.co.kr": "디지털타임스",
            "bokuennews.com": "복지뉴스",
            "snmnews.com": "철강금속신문",
            "whitepaper.co.kr": "화이트페이퍼",
            "theviewers.co.kr": "더뷰어스",
            "thevaluenews.co.kr": "더밸류뉴스",
            "thebigdata.co.kr": "더빅데이터",
            "stardailynews.co.kr": "스타데일리뉴스",
            "smedaily.co.kr": "SME데일리",
            "smarttoday.co.kr": "스마트투데이",
            "pressian.com": "프레시안",
            "ntoday.co.kr": "엔투데이",
            "nspna.com": "NSP통신",
            "moneys.co.kr": "머니S",
            "klnews.co.kr": "물류신문",
            "job-post.co.kr": "잡포스트",
            "ilyosisa.co.kr": "일요시사",
            "greened.kr": "녹색경제신문",
            "globalepic.co.kr": "글로벌이코노믹",
            "electimes.com": "전기신문",
            "einfomax.co.kr": "연합인포맥스",
            "dealsite.co.kr": "딜사이트",
            "dailycar.co.kr": "데일리카",
            "cnbnews.com": "CNB뉴스",
            "ceoscoredaily.com": "CEO스코어데일리",
            "autodaily.co.kr": "오토데일리",
            "weeklytoday.com": "위클리투데이",
            "viva100.com": "브릿지경제",
            "veritas-a.com": "베리타스알파",
            "thetracker.co.kr": "더트래커",
            "sportschosun.com": "스포츠조선",
            "seoulfn.com": "서울파이낸스",
            "nextdaily.co.kr": "넥스트데일리",
            "newscj.com": "천지일보",
            "newscape.co.kr": "뉴스스케이프",
            "mhj21.com": "문화저널21",
            "kpenews.com": "한국정치경제신문",
            "iminju.net": "경기민주언론시민연합",
            "ilyoseoul.co.kr": "일요서울",
            "ibabynews.com": "베이비뉴스",
            "hansbiz.co.kr": "한스경제",
            "gukjenews.com": "국제뉴스",
            "ftoday.co.kr": "퓨쳐데일리",
            "financialpost.co.kr": "파이낸셜포스트",
            "fetv.co.kr": "FETV",
            "etnews.com": "전자신문",
            "dailian.co.kr": "데일리안",
            "cstimes.com": "컨슈머타임스",
            "bizwork.co.kr": "비즈웍스",
            "betanews.net": "베타뉴스",
            "banronbodo.com": "반론보도닷컴",
            "topdaily.kr": "톱데일리",
            "thebell.co.kr": "더벨",
            "the-pr.co.kr": "더피알",
            "stoo.com": "스포츠투데이",
            "sportsworldi.com": "스포츠월드",
            "seoulwire.com": "서울와이어",
            "press9.kr": "프레스나인",
            "newstown.co.kr": "뉴스타운",
            "mhnse.com": "MHN스포츠(경제)",
            "koreastocknews.com": "코리아스탁뉴스",
            "fntimes.com": "파이낸셜뉴스타임즈",
            "choicenews.co.kr": "초이스경제",
            "asiatoday.co.kr": "아시아투데이",
        }

        return base_map.get(base, base)  # 모르는 도메인은 '기본 도메인'으로 통일
    except Exception:
        return ""

# --- OpenAI 키 조회 (OPENAI_API_KEY 또는 OPEN_API_KEY 둘 다 지원) ---
def _get_openai_key():
    return os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY") or ""

def _openai_chat(messages, model=None, temperature=0.2, max_tokens=400):
    """경량 OpenAI Chat 호출 (연결 누수 방지)"""
    api_key = _get_openai_key()
    if not api_key:
        return None, "OPENAI_API_KEY not set"
    model = model or os.getenv("OPENAI_GPT_MODEL", "gpt-4o-mini")
    r = None
    try:
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "n": 1},
            timeout=25,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip(), None
    except Exception as e:
        return None, str(e)
    finally:
        # 연결 누수 방지
        if r is not None:
            r.close()

# --- 기사 본문/제목 추출 (가벼운 크롤러, 연결 누수 방지) ---
def _extract_article_text_and_title(url: str):
    """기사 크롤링 (연결 누수 방지)"""
    html = ""
    resp = None
    try:
        resp = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text
    except Exception:
        pass
    finally:
        # 연결 누수 방지: 응답 객체 명시적으로 닫기
        if resp is not None:
            resp.close()

    title = ""
    text = ""
    if html:
        soup = BeautifulSoup(html, "html.parser")
        # 제목
        og = soup.find("meta", property="og:title")
        if og and og.get("content"): title = og["content"].strip()
        elif soup.title: title = soup.title.get_text(strip=True)

        # 본문 (네이버 등 우선 시도 → 일반 article/p → 전체 텍스트)
        candidates = ["#dic_area", "article", "div#newsEndContents", "div#articeBody", "div#content", "div.article_body"]
        node = None
        for sel in candidates:
            node = soup.select_one(sel)
            if node: break
        if node:
            ps = node.find_all(["p", "div"])
            text = " ".join(p.get_text(" ", strip=True) for p in ps) or node.get_text(" ", strip=True)
        if not text:
            text = soup.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()

    return title, text

# --- 35자 이내 불릿 압축 (백업용) ---
def _short_bullets(text: str, max_lines: int = 4, max_chars: int = 35):
    if not text: return []
    parts = re.split(r'[•\-\u2022\*\n\r\.!?]+', text)
    out = []
    for p in parts:
        s = re.sub(r"\s+", " ", p).strip()
        if not s: continue
        if len(s) > max_chars: s = s[:max_chars-1] + "…"
        out.append(s)
        if len(out) >= max_lines: break
    return out

# --- 핵심 문장 추출 (전처리) ---
def _build_evidence_pack(full_text: str, max_sentences: int = 20) -> str:
    """
    기사 전문에서 핵심 문장만 추출하여 모델 입력 토큰 최소화 + 응답속도 향상
    """
    if not full_text:
        return ""

    # 문장 분리 (마침표, 느낌표, 물음표 기준)
    sentences = re.split(r'[.!?]+', full_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    if not sentences:
        return full_text[:4000]

    # 핵심 키워드 (포스코 + 비즈니스 핵심어)
    core_keywords = [
        "포스코", "POSCO", "포스코인터", "삼척블루파워", "포스코모빌리티",
        "공장", "수주", "양산", "매출", "영업이익", "순이익", "실적",
        "전망", "투자", "지분", "협회", "공급망", "계약", "MOU",
        "생산", "판매", "수출", "착공", "준공", "가동", "증설"
    ]

    # 숫자 패턴 (억, 조, %, 톤 등)
    number_pattern = r'\d+[.,]?\d*\s*(?:억|조|만|천|%|톤|MW|GW|건|개|명|달러|\$|원)'

    selected = []

    # 1) 첫 문장 (리드 문장)
    if sentences:
        selected.append(sentences[0])

    # 2) 마지막 문장 (결론/향후계획)
    if len(sentences) > 1:
        selected.append(sentences[-1])

    # 3) 키워드 포함 문장
    for sent in sentences[1:-1]:
        if any(kw in sent for kw in core_keywords):
            selected.append(sent)

    # 4) 숫자 포함 문장 (중복 제거)
    for sent in sentences:
        if re.search(number_pattern, sent) and sent not in selected:
            selected.append(sent)

    # 5) 중복 제거 및 순서 유지
    seen = set()
    final = []
    for s in selected:
        if s not in seen and len(s) > 15:
            seen.add(s)
            final.append(s)
            if len(final) >= max_sentences:
                break

    # 결과 조합 (4000자 제한)
    result = ". ".join(final)
    return result[:4000]

# --- 링크를 직접 읽어 GPT로 '카톡 보고 메시지' 생성 (개선 버전) ---
def make_kakao_report_from_url(url: str, fallback_media="", fallback_title="", fallback_summary=""):
    media = fallback_media or _publisher_from_link(url)
    title, body = _extract_article_text_and_title(url)
    title = title or fallback_title or "제목 미확인"

    # ✅ 핵심 문장만 추출 (전처리 - 속도 향상)
    evidence = _build_evidence_pack(body or fallback_summary or "", max_sentences=20)

    # ✅ 개선된 프롬프트 (순수 텍스트 출력 강화)
    sys_prompt = """너는 포스코인터내셔널 홍보그룹 전용 '뉴스 보고 메시지 생성 봇'이야.
사용자가 입력한 뉴스 링크의 기사를 요약해 보고 메시지로 작성하는 것이 목적이야.

[보고 메시지 작성 규칙]
1. **형식**:
   - 기사링크 제공
   - 한줄 띠우고(enter)
   - "매체명 : 기사 제목"
   - 하단에 핵심 요약 4~6줄 (각 문장은 50~100자 이내, 단문 중심)
2. **톤앤매너**:
   - 비즈니스 톤
   - 간결, 명확, 빠른 정보 전달
   - 카카오톡 보고용으로 한눈에 보이도록 구성
3. **포함 요소**:
   - 기사 출처(매체명)
   - 기사 핵심 주제(제목 변형하지 말 것)
   - 주요 내용은 각 문단별로 요약을 하고, 이를 포괄하는 주요 내용 4~7블릿으로 정리할 것
   - 포스코인터내셔널 및 포스코그룹 관련 내용 강조
4. **제외 요소**:
   - 불필요한 기자명, 작성일시 등 본문 외 정보


사용자 프롬프트 예시
https://n.news.naver.com/article/215/0001235269?sid=101

출력 예시:
https://n.news.naver.com/article/215/0001235269?sid=101

한국경제 TV : 포스코인터, 알래스카 가스관 뚫는다…"내년 1분기 본계약"

- 알래스카 액화천연가스(LNG) 공급계약을 이르면 내년 1분기 체결할 것으로 전망

- 트럼프 행정부의 역점 사업에 최초로 참여하는 한국 기업일 뿐만 아니라, 글로벌 경쟁국 기업들 중에서도 가장 먼저 본계약을 체결할 가능성이 높다고 언급

- 마이크 던리비 미 알래스카 주지사는 알래스카 LNG 프로젝트 참여 기업에 세금 감면 혜택을 주는 법안을 발의 했다고 외신 보도 인용 언급"""

    user_prompt = f"""링크: {url}
매체명: {media}
제목: {title}

[핵심 내용]
{evidence}

위 내용을 바탕으로 카카오톡 보고 메시지를 작성해줘."""

    out, err = _openai_chat(
        [{"role":"system","content":sys_prompt},{"role":"user","content":user_prompt}],
        temperature=0.0,  # 정확성 최대화
        max_tokens=950
    )
    if out:
        return out

    # 실패 시 백업 포맷 (기존 유지)
    bullets = _short_bullets(evidence or fallback_summary, 4, 35)
    if len(bullets) < 3:
        bullets = [
            "포스코인터내셔널 관련 주요 내용 확인 필요",
            "상세 정보는 원문 기사 참고",
            "비즈니스 임팩트 분석 후 추가 보고"
        ]

    # 백업 보고서도 새 형식에 맞춤 (URL-제목 직결, 블릿 사이 빈 줄, 마침표)
    bullets_formatted = '\n\n'.join(f"- {b}." for b in bullets[:4])
    backup_report = f"""{url}
{media} : {title}
{bullets_formatted}"""
    return backup_report

# --- 카운트다운 전용 프래그먼트(지원 시) + 폴백 ---
def _countdown_badge_html(secs_left: int) -> str:
    return f"""
    <div style="
        padding:8px 12px; background:rgba(212,175,55,0.28);
        border-radius:10px; text-align:center;
        color:#F6D47A; font-weight:800; font-size:1.15rem;">
        {secs_left}
    </div>"""

if SUPPORTS_FRAGMENT:
    @st.fragment
    def countdown_fragment(refresh_interval: int):
        now = time.time()
        secs_left = max(0, int(st.session_state.next_refresh_at - now))
        st.markdown(_countdown_badge_html(secs_left), unsafe_allow_html=True)
        # 5초 간격으로 리프레시 (성능 최적화)
        st_autorefresh(interval=5000, key="countdown_tick")
        # 0초 되면 트리거 플래그 설정하고 즉시 페이지 리런
        if secs_left == 0 and not st.session_state.get("trigger_news_update", False):
            st.session_state.trigger_news_update = True
            st.rerun()
else:
    # 구버전 폴백: 보고서 생성 중이면 카운트다운 정지
    def countdown_fragment(refresh_interval: int):
        now = time.time()
        secs_left = max(0, int(st.session_state.next_refresh_at - now))
        st.markdown(_countdown_badge_html(secs_left), unsafe_allow_html=True)

        # 보고서 생성 중이 아닐 때만 자동 리프레시 (5초 간격으로 성능 최적화)
        if not any(key.startswith("report_generating_") and st.session_state.get(key, False) for key in st.session_state.keys()):
            st_autorefresh(interval=5000, key="countdown_fallback")

        # 0초 되면 트리거 플래그 설정하고 즉시 페이지 리런
        if secs_left == 0 and not st.session_state.get("trigger_news_update", False):
            st.session_state.trigger_news_update = True
            st.rerun()

def fetch_naver_news(query: str, start: int = 1, display: int = 50, sort: str = "date"):
    """뉴스 API 호출 (연결 누수 방지)"""
    r = None
    try:
        url = "https://openapi.naver.com/v1/search/news.json"
        params = {"query": query, "start": start, "display": display, "sort": sort}
        headers = _naver_headers()

        print(f"[DEBUG] API Request - Query: {query}, Params: {params}")
        print(f"[DEBUG] Headers present: ID={bool(headers.get('X-Naver-Client-Id'))}, Secret={bool(headers.get('X-Naver-Client-Secret'))}")

        if not headers.get("X-Naver-Client-Id") or not headers.get("X-Naver-Client-Secret"):
            print("[DEBUG] Missing API keys, returning empty result")
            return {"items": [], "error": "missing_keys"}

        print(f"[DEBUG] Starting API request...")
        r = requests.get(url, headers=headers, params=params, timeout=5)
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
            status_code = e.response.status_code
            print(f"[WARNING] Response status: {status_code}, body: {e.response.text[:200]}")
            if status_code == 429:
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
    print(f"[DEBUG] Starting crawl_naver_news for query: {query}, max_items: {max_items}")
    items, start, total = [], 1, 0
    display = min(50, max_items)  # 한 번에 최대 50개로 제한
    max_attempts = 2  # 최대 2번 시도로 제한하여 빠른 실패
    attempt_count = 0
    quota_exceeded = False

    while total < max_items and start <= 100 and attempt_count < max_attempts:  # 시작 위치도 100으로 제한
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
                    # ✅ GMT → KST 변환 후 tz 제거
                    dt = pd.to_datetime(pub, utc=True).tz_convert("Asia/Seoul").tz_localize(None)
                    date_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    date_str = ""
                items.append({"날짜": date_str, "매체명": _publisher_from_link(link),
                              "검색키워드": query, "기사제목": title, "주요기사 요약": desc, "URL": link, "sentiment": "pos"})
            
            got = len(arr)
            total += got
            if got == 0:
                break
            start += got
            
        except Exception as e:
            print(f"[WARNING] Error in crawl_naver_news attempt {attempt_count}: {e}")
            break
    
    print(f"[DEBUG] crawl_naver_news completed for {query}: {len(items)} items")
    df = pd.DataFrame(items, columns=["날짜", "매체명", "검색키워드", "기사제목", "주요기사 요약", "URL", "sentiment"])

    # API 할당량 초과 정보를 DataFrame 속성으로 저장
    if quota_exceeded:
        df.attrs['quota_exceeded'] = True
        print(f"[ERROR] API 할당량 초과로 뉴스 수집 실패")

    if not df.empty:
        # 최신순 정렬 먼저 수행
        df["날짜_datetime"] = pd.to_datetime(df["날짜"], errors="coerce")
        df = df.sort_values("날짜_datetime", ascending=False, na_position="last").reset_index(drop=True)
        df = df.drop("날짜_datetime", axis=1)

        # 중복 제거 (URL 우선, 없으면 제목+날짜)
        key = df["URL"].where(df["URL"].astype(bool), df["기사제목"] + "|" + df["날짜"])
        df = df.loc[~key.duplicated()].reset_index(drop=True)
    return df

def load_news_db(force_refresh: bool = False) -> pd.DataFrame:
    """뉴스 DB 로드 (GitHub 직접 로드 - Streamlit Cloud 캐시 우회)

    Args:
        force_refresh: True면 즉시 최신 데이터 로드 (캐시 무시)
    """
    # GitHub raw URL에서 직접 로드 (Streamlit Cloud 캐시 문제 해결)
    GITHUB_RAW_URL = "https://raw.githubusercontent.com/kimwoss/Risk_management/main/data/news_monitor.csv"

    try:
        # 1차 시도: GitHub에서 직접 로드 (캐시 우회)
        # 캐시 버스팅을 위해 타임스탬프 추가
        import time
        if force_refresh:
            # 강제 새로고침: 초 단위 타임스탬프 (즉시 최신 데이터)
            cache_buster = int(time.time())
        else:
            # 일반 로드: 30초 단위로 갱신 (빠른 업데이트)
            cache_buster = int(time.time() // 30)
        url_with_cache_buster = f"{GITHUB_RAW_URL}?t={cache_buster}"

        print(f"[DEBUG] GitHub에서 직접 로드 시도: {url_with_cache_buster}")
        response = requests.get(url_with_cache_buster, timeout=10)
        response.raise_for_status()

        from io import StringIO
        df = pd.read_csv(StringIO(response.text), encoding="utf-8")
        response.close()

        # sentiment 컬럼이 없으면 추가
        if "sentiment" not in df.columns:
            df["sentiment"] = "pos"

        # 디버그: 최신 기사 시간 출력
        if not df.empty and "날짜" in df.columns:
            latest_date = df["날짜"].iloc[0] if len(df) > 0 else "N/A"
            print(f"[DEBUG] ✅ GitHub에서 로드 완료: {len(df)}건, 최신 기사: {latest_date}")
        return df

    except Exception as e:
        print(f"[WARNING] GitHub 로드 실패, 로컬 파일 시도: {e}")

        # 2차 시도: 로컬 파일에서 로드
        try:
            df = pd.read_csv(NEWS_DB_FILE, encoding="utf-8")
            # sentiment 컬럼이 없으면 추가
            if "sentiment" not in df.columns:
                df["sentiment"] = "pos"
            if not df.empty and "날짜" in df.columns:
                latest_date = df["날짜"].iloc[0] if len(df) > 0 else "N/A"
                print(f"[DEBUG] ⚠️ 로컬 파일에서 로드: {len(df)}건, 최신 기사: {latest_date}")
            return df
        except Exception as e2:
            print(f"[ERROR] 모든 로드 시도 실패: {e2}")
            return pd.DataFrame(columns=["날짜","매체명","검색키워드","기사제목","주요기사 요약","URL","sentiment"])

def save_news_db(df: pd.DataFrame):
    if df.empty:
        print("[DEBUG] save_news_db skipped: empty dataframe")
        return
    # 매체명 정리 (URL 기반)
    if "매체명" in df.columns and "URL" in df.columns:
        for idx, row in df.iterrows():
            if pd.notna(row["URL"]):
                df.at[idx, "매체명"] = _publisher_from_link(row["URL"])

    # 날짜 컬럼이 이미 정렬되어 있으므로 추가 정렬 생략
    # 상위 200개 저장 (50개에서 증가 - 중복 알림 방지)
    out = df.head(200)
    out.to_csv(NEWS_DB_FILE, index=False, encoding="utf-8")
    safe_print("[DEBUG] news saved:", len(out), "rows ->", NEWS_DB_FILE)

# ----------------------------- 공용 UI 유틸 -----------------------------
def show_table(df: pd.DataFrame, label: str):
    st.markdown(f"#### {label}")
    st.dataframe(df, use_container_width=True, height=min(560, 44 + min(len(df), 12) * 38))

_PHONE_PATTERNS = [r'(?:0?1[016789])[ .-]?\d{3,4}[ .-]?\d{4}']
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+')

def _extract_phone(text: str) -> str:
    s = text or ""
    for p in _PHONE_PATTERNS:
        m = re.search(p, s)
        if m:
            num = re.sub(r"\D", "", m.group(0))
            if len(num) == 11 and num.startswith("010"):
                return f"010-{num[3:7]}-{num[7:]}"
            if len(num) == 10 and num.startswith("10"):
                return f"010-{num[2:6]}-{num[6:]}"
            return m.group(0)
    return ""

def parse_reporters_to_df(reporters) -> pd.DataFrame:
    if not reporters:
        return pd.DataFrame(columns=["이름","직책","연락처","이메일","소속/팀","비고"])
    rows = []
    for item in reporters:
        if isinstance(item, dict):
            rows.append([
                item.get("이름") or item.get("name") or item.get("기자") or "",
                item.get("직책") or item.get("직급") or item.get("role") or "",
                item.get("연락처") or item.get("mobile") or item.get("phone") or "",
                item.get("이메일") or item.get("email") or "",
                item.get("팀") or item.get("소속") or "",
                item.get("비고") or item.get("note") or ""
            ])
            continue
        s = " ".join([str(x).strip() for x in item]) if isinstance(item, (list, tuple)) else str(item).strip()
        email_match = EMAIL_RE.search(s)
        email = email_match.group(0) if email_match else ""
        phone = _extract_phone(s)
        parts = [p.strip() for p in re.split(r"[·\|,\t]+", s) if p.strip()]
        name = parts[0] if parts else s
        team = ""
        m = re.search(r"(.+?)\s*\((.+?)\)", name)
        if m:
            name, team = m.group(1).strip(), m.group(2).strip()
        role = ""
        for p in parts[1:]:
            if any(k in p for k in ["팀장","차장","기자","부장","에디터","데스크","CFO","국장"]):
                role = p; break
        rows.append([name, role, phone, email, team, ""])
    df = pd.DataFrame(rows, columns=["이름","직책","연락처","이메일","소속/팀","비고"]).fillna("")
    if not df.empty:
        df = df.drop_duplicates(subset=["이름","연락처","이메일"], keep="first").reset_index(drop=True)
    return df

def _to_people_df(lines, tag: str) -> pd.DataFrame:
    if not lines:
        return pd.DataFrame(columns=["구분","이름","직책","연락처","이메일","소속/팀","비고"])
    df = parse_reporters_to_df(lines)
    if not df.empty and "이름" in df.columns:
        df = df[~df["이름"].str.fullmatch(r"\s*<.*>\s*", na=False)]
    df.insert(0, "구분", tag)
    return df

# ----------------------------- 텔레그램 알림 -----------------------------
def send_telegram_notification(new_articles: list):
    """
    새로운 기사가 발견되면 텔레그램으로 알림 전송 (기사별 개별 메시지)

    - 모든 신규 기사를 텔레그램으로 전송 (개수 제한 없음)
    - 각 기사마다 재시도 로직 포함
    - 텔레그램 API Rate Limit 준수 (초당 약 28개)
    - 전송 성공한 기사만 캐시에 추가하여 재전송 방지

    Args:
        new_articles: 새로운 기사 정보 리스트 [{"title": ..., "link": ..., "date": ...}, ...]
    """
    global _sent_articles_cache

    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        print(f"[DEBUG] 텔레그램 알림 시도 - 기사 수: {len(new_articles) if new_articles else 0}")
        print(f"[DEBUG] 봇 토큰 존재: {bool(bot_token)}, Chat ID 존재: {bool(chat_id)}")

        # 환경변수가 없으면 알림 스킵
        if not bot_token or not chat_id:
            print("[DEBUG] ⚠️ 텔레그램 설정 없음 - 알림 스킵")
            print("[DEBUG] 💡 Streamlit Cloud → Settings → Secrets에서 TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID 설정 필요")
            return

        if not new_articles:
            print("[DEBUG] 신규 기사 없음 - 알림 스킵")
            return

        # 이미 전송된 기사 필터링
        with _sent_articles_lock:
            articles_to_send = []
            for article in new_articles:
                url_key = article.get("link", "")
                if url_key and url_key not in _sent_articles_cache:
                    articles_to_send.append(article)

            if not articles_to_send:
                print("[DEBUG] 모든 기사가 이미 전송됨 - 알림 스킵")
                return

            print(f"[DEBUG] 전송 대상: {len(articles_to_send)}건 (중복 제외: {len(new_articles) - len(articles_to_send)}건)")

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
                        with _sent_articles_lock:
                            _sent_articles_cache.add(link)
                            # 캐시 크기 제한
                            if len(_sent_articles_cache) > _MAX_SENT_CACHE:
                                # 오래된 항목 제거 (set이므로 임의 제거)
                                _sent_articles_cache.pop()
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
        print(f"[DEBUG] 전송 캐시 크기: {len(_sent_articles_cache)}건")

    except Exception as e:
        print(f"[DEBUG] ❌ 텔레그램 알림 예외 발생: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류:\n{traceback.format_exc()}")

def detect_new_articles(old_df: pd.DataFrame, new_df: pd.DataFrame) -> list:
    """
    기존 DB와 새로운 데이터를 비교하여 신규 기사 감지

    - URL을 우선 식별자로 사용
    - 최근 6시간 이내 기사만 알림 대상
    - 정확한 중복 체크

    Args:
        old_df: 기존 뉴스 데이터
        new_df: 새로 수집한 뉴스 데이터

    Returns:
        신규 기사 정보 리스트
    """
    try:
        # 기존 DB가 비어있으면 신규 기사 없음으로 처리 (첫 실행 스팸 방지)
        if old_df.empty:
            print(f"[DEBUG] 기존 DB 비어있음 - 첫 실행이므로 알림 스킵")
            return []

        if new_df.empty:
            return []

        # 현재 시간 기준 (KST)
        KST = timezone(timedelta(hours=9))
        now = datetime.now(KST).replace(tzinfo=None)  # KST 시간을 naive datetime으로

        # 기존 DB의 URL 세트 생성 (가장 정확한 식별자)
        old_urls = set()
        for _, row in old_df.iterrows():
            url = str(row.get("URL", "")).strip()
            if url and url != "nan" and url != "":
                old_urls.add(url)

        print(f"[DEBUG] 기존 DB URL 수: {len(old_urls)}")
        print(f"[DEBUG] 수집된 신규 데이터 수: {len(new_df)}")

        # 신규 기사 감지
        new_articles = []
        for _, row in new_df.iterrows():
            url = str(row.get("URL", "")).strip()
            title = str(row.get("기사제목", "")).strip()

            # URL이 없거나 비어있으면 스킵
            if not url or url == "nan" or url == "":
                continue

            # URL이 기존 DB에 없으면 신규
            if url not in old_urls:
                # 날짜 파싱 시도
                article_date_str = row.get("날짜", "")
                try:
                    # 날짜 형식: "YYYY-MM-DD HH:MM"
                    article_date = pd.to_datetime(article_date_str, errors="coerce")

                    # 날짜가 유효하면 최근 6시간 이내인지 확인
                    if pd.notna(article_date):
                        time_diff = now - article_date
                        hours_diff = time_diff.total_seconds() / 3600

                        # 6시간 이내의 기사만 알림
                        if hours_diff > 6:
                            print(f"[DEBUG] 오래된 기사 스킵: {title[:30]}... ({hours_diff:.1f}시간 전)")
                            continue
                        else:
                            print(f"[DEBUG] 신규 기사 감지: {title[:50]}... ({hours_diff:.1f}시간 전)")
                    else:
                        # 날짜 파싱 실패 시에도 포함 (안전장치)
                        print(f"[DEBUG] 날짜 파싱 실패 (알림 포함): {title[:50]}...")

                except Exception as e:
                    print(f"[DEBUG] 날짜 처리 오류: {str(e)}")

                # URL에서 매체명 추출 (Streamlit과 동일한 방식)
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

        print(f"[DEBUG] 총 {len(new_articles)}건의 신규 기사 감지 (최근 6시간 이내)")
        return new_articles

    except Exception as e:
        print(f"[DEBUG] 신규 기사 감지 오류: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류:\n{traceback.format_exc()}")
        return []

# ----------------------------- 백그라운드 뉴스 모니터링 -----------------------------
def background_news_monitor():
    """
    백그라운드에서 자동으로 뉴스를 수집하고 텔레그램 알림을 보내는 함수
    브라우저 연결 여부와 관계없이 3분마다 자동 실행됨
    """
    try:
        print(f"[BACKGROUND] 뉴스 수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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
            print("[BACKGROUND] API 키가 없어 수집을 건너뜁니다.")
            return

        # 기존 DB 로드
        existing_db = load_news_db()

        # 뉴스 수집
        all_news = []
        quota_exceeded = False

        for kw in keywords:
            df_kw = crawl_naver_news(kw, max_items=max_items // len(keywords), sort="date")

            # API 할당량 초과 체크
            if df_kw.attrs.get('quota_exceeded', False):
                print(f"[BACKGROUND] ⚠️ API 할당량 초과 감지 - 뉴스 수집 중단")
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

                        # 제외 키워드 체크
                        exclude_words = ["청약", "분양", "입주", "재건축", "정비구역"]
                        for exclude_word in exclude_words:
                            if exclude_word in title or exclude_word in description:
                                return False

                        return True

                    mask = df_kw.apply(should_include_posco_intl, axis=1)
                    df_kw = df_kw[mask].reset_index(drop=True)
                    if not df_kw.empty:
                        print(f"[BACKGROUND] '포스코인터내셔널' 정확 매칭 필터링 완료: {len(df_kw)}건 추가")

                # "포스코모빌리티솔루션" 정확한 매칭 강화
                elif kw == "포스코모빌리티솔루션":
                    def should_include_posco_mobility(row):
                        title = str(row.get("기사제목", ""))
                        description = str(row.get("주요기사 요약", ""))

                        # 정확히 "포스코모빌리티솔루션"이 포함되어야 함
                        if "포스코모빌리티솔루션" not in title and "포스코모빌리티솔루션" not in description:
                            return False

                        # 제외 키워드 체크
                        exclude_words = ["청약", "분양", "입주", "재건축", "정비구역"]
                        for exclude_word in exclude_words:
                            if exclude_word in title or exclude_word in description:
                                return False

                        return True

                    mask = df_kw.apply(should_include_posco_mobility, axis=1)
                    df_kw = df_kw[mask].reset_index(drop=True)
                    if not df_kw.empty:
                        print(f"[BACKGROUND] '포스코모빌리티솔루션' 정확 매칭 필터링 완료: {len(df_kw)}건 추가")

                # "포스코" 키워드의 경우 특별 처리
                elif kw == "포스코":
                    def should_include_posco(row):
                        title = str(row.get("기사제목", ""))
                        title_lower = title.lower()
                        description = str(row.get("주요기사 요약", ""))
                        content_lower = description.lower()

                        # 기존 조건: 타이틀에 "포스코" 포함
                        title_has_posco = "포스코" in title or "posco" in title_lower

                        # 새 조건: 타이틀에 "[단독]" 포함 AND 내용에 "포스코" 포함
                        is_exclusive_with_posco_in_content = "[단독]" in title and "포스코" in description

                        # 둘 중 하나라도 만족하면 포함
                        if not (title_has_posco or is_exclusive_with_posco_in_content):
                            return False

                        for exclude_kw in exclude_keywords:
                            if exclude_kw.lower() in title_lower:
                                return False

                        exclude_words = ["청약", "분양", "입주", "재건축", "정비구역"]
                        for exclude_word in exclude_words:
                            if exclude_word in title or exclude_word in description:
                                return False

                        return True

                    mask_posco = df_kw.apply(should_include_posco, axis=1)
                    df_kw = df_kw[mask_posco].reset_index(drop=True)
                    if not df_kw.empty:
                        print(f"[BACKGROUND] '포스코' 필터링 완료: {len(df_kw)}건 추가")

                else:
                    # 다른 키워드는 기존처럼 제목에서만 부동산 관련 키워드 제거
                    exclude_words = ["분양", "청약", "입주", "재건축", "정비구역"]
                    def should_include_general(row):
                        title = str(row.get("기사제목", ""))
                        for exclude_word in exclude_words:
                            if exclude_word in title:
                                return False
                        return True

                    mask_general = df_kw.apply(should_include_general, axis=1)
                    df_kw = df_kw[mask_general].reset_index(drop=True)

                if not df_kw.empty:
                    all_news.append(df_kw)

        # API 할당량 초과 시 처리
        if quota_exceeded:
            print(f"[BACKGROUND] ❌ API 할당량 초과로 뉴스 수집 실패")
            print(f"[BACKGROUND] 💡 해결 방법:")
            print(f"[BACKGROUND]    1. 새로운 네이버 개발자 계정으로 API 키 재발급")
            print(f"[BACKGROUND]    2. 매일 자정(KST) 이후 할당량 재설정")
            print(f"[BACKGROUND]    3. 기존 저장된 뉴스 데이터는 유지됩니다")
            return

        # 통합 정리 & 저장
        df_new = pd.concat(all_news, ignore_index=True) if all_news else pd.DataFrame()
        if not df_new.empty:
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
            print(f"[BACKGROUND] ✅ DB 저장 완료: 총 {len(merged)}건")

            # 기존 DB가 비어있지 않을 때만 알림 전송 (첫 실행 스팸 방지)
            if new_articles and not existing_db.empty:
                print(f"[BACKGROUND] ✅ 신규 기사 {len(new_articles)}건 감지 - 텔레그램 알림 전송")
                send_telegram_notification(new_articles)
            elif new_articles:
                print(f"[BACKGROUND] ⏭️ 신규 기사 {len(new_articles)}건 감지 - 첫 실행이므로 알림 스킵")

            print(f"[BACKGROUND] ✅ 뉴스 수집 완료")
        else:
            print(f"[BACKGROUND] ℹ️ 새로 수집된 기사가 없습니다.")

    except Exception as e:
        print(f"[BACKGROUND] ❌ 뉴스 수집 오류: {str(e)}")
        import traceback
        print(f"[BACKGROUND] 상세 오류:\n{traceback.format_exc()}")

# 백그라운드 스케줄러 전역 변수
_scheduler = None
_scheduler_lock = threading.Lock()

# 전송된 기사 URL 추적 (메모리 기반, 최근 1000개)
_sent_articles_cache = set()
_sent_articles_lock = threading.Lock()
_MAX_SENT_CACHE = 1000

def start_background_scheduler():
    """
    백그라운드 스케줄러를 시작하는 함수
    앱 시작 시 한 번만 실행됨
    """
    global _scheduler

    # APScheduler가 없으면 스킵
    if not SCHEDULER_AVAILABLE:
        print("[BACKGROUND] ⚠️ APScheduler가 설치되지 않아 백그라운드 모니터링이 비활성화되었습니다.")
        print("[BACKGROUND] 브라우저에서 '뉴스 모니터링' 메뉴를 열어두면 수동 새로고침이 작동합니다.")
        return

    with _scheduler_lock:
        # 이미 스케줄러가 실행 중이면 스킵
        if _scheduler is not None and _scheduler.running:
            print("[BACKGROUND] 스케줄러가 이미 실행 중입니다.")
            return

        try:
            # BackgroundScheduler 생성
            _scheduler = BackgroundScheduler(timezone="Asia/Seoul")

            # 3분(180초)마다 background_news_monitor 실행
            _scheduler.add_job(
                background_news_monitor,
                'interval',
                seconds=180,
                id='news_monitor',
                replace_existing=True,
                max_instances=1  # 동시 실행 방지
            )

            # 스케줄러 시작
            _scheduler.start()
            print(f"[BACKGROUND] ✅ 백그라운드 스케줄러 시작 완료 (3분마다 자동 실행)")

            # 앱 종료 시 스케줄러도 종료
            atexit.register(lambda: _scheduler.shutdown() if _scheduler else None)

        except Exception as e:
            print(f"[BACKGROUND] ❌ 스케줄러 시작 오류: {str(e)}")
            import traceback
            print(f"[BACKGROUND] 상세 오류:\n{traceback.format_exc()}")

# ----------------------------- 스타일 -----------------------------
# CSS 캐시 비활성화 - 즉시 반영
@st.cache_data(ttl=0)
def load_base_css():
    st.markdown("""
    <style>
      /* 컨테이너 폭 + 상단 여백 (Streamlit 정책 준수) */
      .block-container {max-width:1360px !important; padding: 24px 20px 0 !important; margin-top: 16px !important;}

      /* 배경/폰트 */
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700&display=swap');
      [data-testid="stAppViewContainer"]{
        background: linear-gradient(180deg,#0c0d10 0%, #0a0b0d 100%) !important;
        color:#eee; font-family:'Inter','Noto Sans KR',system-ui,Segoe UI,Roboto,Apple SD Gothic Neo,Pretendard,sans-serif;
      }
      [data-testid="stHeader"]{background:transparent; height:0;}
      section[data-testid="stSidebar"] {display:none !important;}

      /* 카드 */
      .card{
        background: linear-gradient(135deg, rgba(24,24,28,.65), rgba(16,16,20,.85));
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 12px; padding: 24px; margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,.3), 0 1px 0 rgba(255,255,255,.05) inset;
        backdrop-filter: blur(10px);
      }
      .input-card{ border-color: rgba(212,175,55,.25); }
      .result-card{ border-color: rgba(189,189,189,.2); }

      /* 버튼 (제네시스 톤) */
      .stButton>button{
        border-radius:8px; font-weight:700; border:1px solid rgba(255,255,255,.18);
        background: linear-gradient(180deg, #2a2b2f, #1a1b1f); color:#fff;
        padding:10px 16px; letter-spacing:.01em;
      }
      /* 로고 영역 스타일 */
      .nav-container a:hover {
        opacity: 0.9;
      }
      .stButton>button:hover{
        border-color: rgba(212,175,55,.6) !important;
        background: linear-gradient(135deg, rgba(32,34,40,.9), rgba(24,26,32,.95)) !important;
        box-shadow: 0 4px 20px rgba(212,175,55,.12), 0 2px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px) !important;
        color: #fff !important;
      }
      .stButton>button:disabled{
        color:#fff; border-color:#fff; background:linear-gradient(135deg, rgba(255,255,255,.12), rgba(255,255,255,.04));
      }

      /* 다운로드 버튼 특별 스타일 */
      .stDownloadButton>button{
        background: linear-gradient(135deg, #D4AF37, #B8941F) !important;
        border: 1px solid rgba(212,175,55,.4) !important;
        color: #000 !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        letter-spacing: 0.01em !important;
        transition: all 0.25s ease !important;
      }
      .stDownloadButton>button:hover{
        background: linear-gradient(135deg, #E6C55A, #D4AF37) !important;
        border-color: rgba(212,175,55,.8) !important;
        box-shadow: 0 4px 20px rgba(212,175,55,.25) !important;
        transform: translateY(-1px) !important;
        color: #000 !important;
      }

      /* 데이터프레임 */
      div[data-testid="stDataFrame"]{ background: rgba(255,255,255,.03) !important; border:1px solid rgba(255,255,255,.08); border-radius:10px; }
      div[data-testid="stDataFrame"] *{ color:#e7e7e7 !important; }

      /* 페이지 전환 애니메이션 개선 */
      @keyframes stFadeSlide { from{opacity:0; transform:translateY(8px)} to{opacity:1; transform:none} }
      @keyframes stFadeIn { from{opacity:0} to{opacity:1} }
      [data-testid="stAppViewContainer"] .block-container{ 
        animation: stFadeSlide .25s ease-out; 
        will-change: transform, opacity;
      }
      
      /* 입력 요소 전환 최적화 */
      .stTextInput, .stTextArea, .stSelectbox, .stButton {
        transition: all 0.2s ease;
        will-change: auto;
      }

      /* 메뉴 전환 시 부드러운 효과 */
      .card {
        animation: stFadeIn 0.3s ease-out;
        will-change: opacity;
      }

      /* 모바일 최적화 (전역) */
      @media (max-width: 768px) {
        .card {
          padding: 16px !important;
          border-radius: 10px !important;
          margin-bottom: 16px !important;
        }
        .main-copy {
          left: 24px !important;
          padding-right: 24px !important;
        }
        .stButton>button {
          font-size: 0.9rem !important;
          padding: 10px 14px !important;
        }
        .stDownloadButton>button {
          font-size: 0.9rem !important;
          padding: 10px 14px !important;
        }
      }

      @media (max-width: 480px) {
        .card {
          padding: 12px !important;
          border-radius: 8px !important;
        }
        .main-copy {
          left: 16px !important;
          padding-right: 16px !important;
        }
        [data-testid="stAppViewContainer"] .block-container {
          padding-left: 1rem !important;
          padding-right: 1rem !important;
        }
      }
    </style>
    """, unsafe_allow_html=True)

# ----------------------------- 자원 로드 (캐싱으로 파일 읽기 최소화) -----------------------------
@st.cache_data
def load_logo_data_uri():
    """로고 이미지 로드 (캐시됨)"""
    candidates = [
        os.path.join(DATA_FOLDER, "POSCO_INTERNATIONAL_Korean_Signature.svg"),
        os.path.join(DATA_FOLDER, "POSCO_INTERNATIONAL_Korean_Signature.png"),
        os.path.join(DATA_FOLDER, "logo.png"),
    ]
    for p in candidates:
        if os.path.exists(p):
            mt = mimetypes.guess_type(p)[0] or "image/png"
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:{mt};base64,{b64}"
    return ""

@st.cache_data
def load_main_background_uri():
    """메인 배경 이미지 로드 (캐시됨)"""
    p = os.path.join(DATA_FOLDER, "Image_main.jpg")
    if os.path.exists(p):
        with open(p, "rb") as f:
            return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    return ""

# ----------------------------- 네비게이션 -----------------------------
MENU_ITEMS = ["뉴스 모니터링", "이슈발생보고 생성", "언론사 정보 검색", "담당자 정보 검색", "기존대응이력 검색"]

def set_active_menu_from_url(default_label="메인"):
    try:
        raw = st.query_params.get("menu") or default_label
        label = urllib.parse.unquote(str(raw))
        st.session_state["top_menu"] = label
        return label
    except Exception:
        return st.session_state.get("top_menu", default_label)

def render_top_nav(active_label: str):
    logo_uri = load_logo_data_uri()
    st.markdown("""
    <style>
      /* 네비게이션 컨테이너 */
      .nav-container {
        background: linear-gradient(135deg, rgba(16,18,24,.4), rgba(12,14,20,.6));
        border: 1px solid rgba(255,255,255,.06);
        border-radius: 16px;
        padding: 16px 20px;
        margin: 8px 0 20px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,.2);
        backdrop-filter: blur(12px);
      }

      /* 네비게이션 버튼 전용 스타일 - 제네시스 톤 */
      .nav-container .stButton>button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: 1px solid rgba(255,255,255,.12) !important;
        background: linear-gradient(135deg, rgba(28,30,36,.8), rgba(20,22,28,.9)) !important;
        color: #e8e8e8 !important;
        padding: 12px 20px !important;
        letter-spacing: 0.02em !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 48px !important;
        min-height: 48px !important;
        font-size: 0.95rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
      }
      .nav-container .stButton>button:hover {
        border-color: rgba(212,175,55,.6) !important;
        background: linear-gradient(135deg, rgba(32,34,40,.9), rgba(24,26,32,.95)) !important;
        box-shadow: 0 4px 20px rgba(212,175,55,.12), 0 2px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px) !important;
        color: #fff !important;
      }
      .nav-container .stButton>button:disabled {
        color: #D4AF37 !important;
        border-color: rgba(212,175,55,.8) !important;
        background: linear-gradient(135deg, rgba(212,175,55,.15), rgba(212,175,55,.08)) !important;
        box-shadow: 0 0 0 1px rgba(212,175,55,.3) inset, 0 4px 16px rgba(212,175,55,.08) !important;
        transform: none !important;
        font-weight: 700 !important;
      }

      /* 모바일 최적화 (768px 이하) */
      @media (max-width: 768px) {
        .nav-container .stButton>button {
          font-size: 0.75rem !important;
          padding: 8px 6px !important;
          height: auto !important;
          min-height: 42px !important;
          line-height: 1.3 !important;
          white-space: normal !important;
          word-break: keep-all !important;
        }
        .nav-container {
          padding: 12px 10px !important;
          margin: 6px 0 16px 0 !important;
        }
        .nav-container img {
          height: 36px !important;
        }
      }

      /* 더 작은 화면 (480px 이하) */
      @media (max-width: 480px) {
        .nav-container .stButton>button {
          font-size: 0.7rem !important;
          padding: 6px 4px !important;
          min-height: 38px !important;
        }
        .nav-container {
          padding: 10px 8px !important;
          border-radius: 12px !important;
        }
        .nav-container img {
          height: 32px !important;
        }
      }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    with st.container():
        c1, c2 = st.columns([1.2, 4.0], gap="medium")
        with c1:
            if logo_uri:
                # 로고를 클릭 가능한 HTML로 직접 구현 (메뉴 버튼과 높이 정렬)
                st.markdown(f'''
                <div style="width: 100%; height: 48px; display: flex; align-items: center; justify-content: center;">
                    <a href="?home=1" style="display: block; cursor: pointer; transition: all 0.2s ease;">
                        <img src="{logo_uri}" alt="POSCO 메인으로" title="메인 페이지로 이동"
                             style="height: 42px; max-width: 100%; transition: transform 0.2s ease;"
                             onmouseover="this.style.transform='scale(1.05)'"
                             onmouseout="this.style.transform='scale(1)'">
                    </a>
                </div>
                ''', unsafe_allow_html=True)

                # URL 파라미터로 클릭 감지
                if st.query_params.get("home") == "1":
                    st.session_state.authenticated = True
                    st.query_params.clear()
                    st.rerun()
        with c2:
            cols = st.columns(len(MENU_ITEMS))
            for i, label in enumerate(MENU_ITEMS):
                with cols[i]:
                    clicked = st.button(label, key=f"nav_{label}", use_container_width=True, disabled=(label==active_label))
                    if clicked:
                        st.query_params["menu"] = label
                        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------- 메인 히어로 -----------------------------
def render_main_page():
    bg_uri = load_main_background_uri()
    st.markdown(f"""
    <style>
      .main-hero {{
        position:relative; width:100%; height:72vh; min-height:480px; border-radius:16px; overflow:hidden; margin:20px 0;
        box-shadow:0 20px 60px rgba(0,0,0,.4);
        background:
          linear-gradient(90deg, rgba(0,0,0,.78) 0%, rgba(0,0,0,.45) 42%, rgba(0,0,0,0) 75%),
          url('{bg_uri}') right center / contain no-repeat, #000;
      }}
      @media (max-width:900px){{
        .main-hero {{
          background:
            linear-gradient(180deg, rgba(0,0,0,.72) 0%, rgba(0,0,0,.35) 60%),
            url('{bg_uri}') center 65% / cover no-repeat, #000;
        }}
      }}
      .main-copy {{ position:absolute; left:48px; top:50%; transform:translateY(-50%); color:#fff; max-width:720px; text-shadow:0 4px 20px rgba(0,0,0,.45); }}
      .t {{ font-size:3.2rem; line-height:1.15; font-weight:300; margin:0 0 8px; letter-spacing:-.02em; }}
      .s {{ font-size:1.4rem; margin:4px 0 18px; color:rgba(255,255,255,.95); }}
      .d {{ font-size:1.05rem; color:rgba(255,255,255,.85); line-height:1.55; max-width:560px; }}
      @media (max-width:900px){{ .t{{font-size:2.2rem;}} .s{{font-size:1.1rem;}} }}
    </style>
    <section class="main-hero">
      <div class="main-copy">
        <div class="t">위기관리커뮤니케이션</div>
        <div class="s">AI 자동화 솔루션</div>
        <div class="d">포스코인터내셔널의 스마트한 언론대응 시스템입니다.<br/>AI 기반 분석으로 신속하고 정확한 위기관리 솔루션을 제공합니다.</div>
      </div>
    </section>
    """, unsafe_allow_html=True)

# ----------------------------- 페이지들 -----------------------------
def page_issue_report():
    # GPT봇 버튼만 표시
    st.markdown("""
<div style="display:flex; justify-content:flex-end; margin-bottom:16px;">
    <a href="https://chatgpt.com/g/g-68d89a8acda88191b246fd6b813160a3-pointeo-wigigwanrikeom-cinjeolhan-gaideu-ver-2"
       target="_blank" rel="noopener noreferrer"
       style="display:inline-block; padding:10px 16px; border-radius:8px; font-weight:700; text-decoration:none;
              background:linear-gradient(135deg, #D4AF37, #B8941F); border:1px solid rgba(212,175,55,.4); color:#000;">
      GPT봇 사용하기
    </a>
</div>
""", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown('<div class="card input-card"><div style="font-weight:600; margin-bottom:8px;">이슈 정보 입력</div>', unsafe_allow_html=True)
        media = st.text_input("언론사명", placeholder="예: 조선일보, 동아일보, 한국경제 등", key="issue_media")
        reporter = st.text_input("기자명", placeholder="담당 기자명을 입력하세요", key="issue_reporter")
        issue = st.text_area("발생 이슈", placeholder="발생한 이슈에 대해 상세히 기술해주세요...", height=150, key="issue_content")
        gen = st.button("이슈발생보고 생성", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        if gen:
            if not media.strip():
                st.error("언론사명을 입력해주세요.")
            elif not reporter.strip():
                st.error("기자명을 입력해주세요.")
            elif not issue.strip():
                st.error("발생 이슈를 입력해주세요.")
            else:
                with st.spinner("AI가 분석하고 있습니다..."):
                    report = generate_issue_report(media, reporter, issue)
                    st.markdown("### 생성된 이슈 발생 보고서")
                    edited = st.text_area("보고서 내용(수정 가능)", value=report, height=300, key="issue_report_edit")
                    if st.button("저장하기", use_container_width=True):
                        with open("temp_issue_report.txt", "w", encoding="utf-8") as f:
                            f.write(edited)
                        st.success("보고서가 저장되었습니다. (temp_issue_report.txt)")
                    payload = f"""포스코인터내셔널 언론대응 이슈 발생 보고서
================================

생성일시: {datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')}
언론사: {media}
기자명: {reporter}
발생 이슈: {issue}

보고서 내용:
{edited}
"""
                    st.download_button("보고서 다운로드", data=payload,
                                       file_name=f"이슈발생보고서_{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M%S')}.txt",
                                       mime="text/plain", use_container_width=True)
        else:
            st.markdown('<p style="color: white;">좌측에서 정보를 입력하고 버튼을 눌러주세요.</p>', unsafe_allow_html=True)

def page_media_search():
    # 출입매체 현황 대시보드
    media_contacts = get_media_contacts()
    render_publisher_dashboard(media_contacts, show_live=True)

    q = st.text_input("언론사명을 입력하세요:", placeholder="예: 조선일보, 중앙일보, 한국경제 등", key="media_search_query")
    
    if st.button("🔍 언론사 정보 조회", use_container_width=True):
        if q:
            with st.spinner("언론사 정보를 검색하고 있습니다..."):
                # 디버그: 로드된 데이터 확인
                master_data = load_master_data()
                media_contacts = master_data.get("media_contacts", {})
                
                
                info = search_media_info(q)
                if info:
                    st.success(f"✅ '{info.get('name','')}' 언론사 정보를 찾았습니다.")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("#### 📋 기본 정보")
                        st.markdown(f"**언론사명**: {info.get('name','N/A')}")
                        st.markdown(f"**분류**: {info.get('type','N/A')}")
                        st.markdown(f"**담당자(社內)**: {info.get('contact_person','N/A')}")
                        
                        # 연락처 정보 추가
                        if info.get('main_phone', 'N/A') != 'N/A':
                            st.markdown(f"**대표전화**: {info.get('main_phone','N/A')}")
                        if info.get('fax', 'N/A') != 'N/A':
                            st.markdown(f"**팩스**: {info.get('fax','N/A')}")
                        if info.get('address', 'N/A') != 'N/A':
                            st.markdown(f"**주소**: {info.get('address','N/A')}")
                    
                    with c2:
                        reporters = info.get("reporters", [])
                        if reporters:
                            # 연락처 정보를 구분별로 정렬 (DESK/부서담당자를 상단에 배치)
                            reporters_data = []
                            for reporter in reporters:
                                # 빈 문자열은 "-"로 표시
                                reporters_data.append({
                                    "이름": reporter.get("이름", "") or "-",
                                    "직책": reporter.get("직책", "") or "-",
                                    "연락처": reporter.get("연락처", "") or "-",
                                    "이메일": reporter.get("이메일", "") or "-",
                                    "구분": reporter.get("구분", "기자")
                                })
                            
                            if reporters_data:
                                # 직책별 계층 정렬: 국장 → 부장 → 팀장 → 차장 → 기타
                                def sort_key(reporter):
                                    position = reporter.get("직책", "").lower()
                                    category = reporter.get("구분", "")
                                    
                                    # 직책 우선순위 결정
                                    if "국장" in position:
                                        priority = 0
                                    elif "부장" in position:
                                        priority = 1
                                    elif "팀장" in position:
                                        priority = 2
                                    elif "차장" in position:
                                        priority = 3
                                    elif category == "DESK/부서담당자":
                                        priority = 1  # 부장급으로 처리
                                    else:
                                        priority = 4  # 기타
                                    
                                    return (priority, reporter.get("이름", ""))
                                
                                sorted_reporters = sorted(reporters_data, key=sort_key)
                                
                                # 구분 필드를 제외하고 DataFrame 생성
                                display_data = [{k: v for k, v in reporter.items() if k != "구분"} for reporter in sorted_reporters]
                                df_reporters = pd.DataFrame(display_data)
                                show_table(df_reporters, "👥 출입기자 상세정보")
                        else:
                            st.info("등록된 출입기자 정보가 없습니다.")
                    with st.expander("🔍 상세 데이터 (개발자용)"):
                        st.json(info.get("raw_data", {}))
                else:
                    st.warning(f"❌ '{q}' 언론사 정보를 찾을 수 없습니다.")
                    with st.expander("📋 등록된 언론사 목록 확인"):
                        try:
                            contacts = get_media_contacts()
                            lst = list(contacts.keys())
                            cols = st.columns(3)
                            for i, name in enumerate(lst):
                                cols[i % 3].write(f"• {name}")
                        except Exception as e:
                            st.error(f"언론사 목록 로드 실패: {e}")
        else:
            st.error("언론사명을 입력해주세요.")

def page_contact_search():
    departments = load_master_data_fresh().get("departments", {})

    search_query = st.text_input("검색어 입력 (부서명, 담당자명, 연락처, 이메일, 담당이슈):", placeholder="예) 김우현, 식량, 홍보그룹", key="contact_search_name")
    if st.button("🔍 담당자 검색", use_container_width=True):
        rows = []
        # 홍보그룹을 먼저 처리
        if "홍보그룹" in departments:
            dept = departments["홍보그룹"]
            if "담당자들" in dept:
                for p in dept["담당자들"]:
                    담당이슈_str = ", ".join(dept.get("담당이슈", []))
                    rows.append({"부서명": "홍보그룹", "성명": p.get("담당자",""), "직급": p.get("직급",""),
                                 "연락처": p.get("연락처",""), "이메일": p.get("이메일",""), "담당이슈": 담당이슈_str})
        # 나머지 부서들 처리
        for dept_name, dept in departments.items():
            if dept_name == "홍보그룹":  # 이미 처리했으므로 스킵
                continue
            if "담당자들" in dept:
                for p in dept["담당자들"]:
                    담당이슈_str = ", ".join(dept.get("담당이슈", []))
                    rows.append({"부서명": dept_name, "성명": p.get("담당자",""), "직급": p.get("직급",""),
                                 "연락처": p.get("연락처",""), "이메일": p.get("이메일",""), "담당이슈": 담당이슈_str})
            else:
                담당이슈_str = ", ".join(dept.get("담당이슈", []))
                rows.append({"부서명": dept_name, "성명": dept.get("담당자",""), "직급": dept.get("직급",""),
                             "연락처": dept.get("연락처",""), "이메일": dept.get("이메일",""), "담당이슈": 담당이슈_str})

        # 확장된 검색 로직: 부서명, 성명, 연락처, 이메일, 담당이슈에서 검색
        if search_query.strip():
            filtered = []
            for r in rows:
                if (search_query.strip() in r["부서명"] or
                    search_query.strip() in r["성명"] or
                    search_query.strip() in r["연락처"] or
                    search_query.strip() in r["이메일"] or
                    search_query.strip() in r["담당이슈"]):
                    filtered.append(r)
        else:
            filtered = rows

        if filtered:
            show_table(pd.DataFrame(filtered), "👥 담당자 검색 결과")
        else:
            st.warning("❌ 해당 조건에 맞는 담당자를 찾을 수 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    rows = []
    # 홍보그룹을 먼저 처리
    if "홍보그룹" in departments:
        dept = departments["홍보그룹"]
        if "담당자들" in dept:
            for p in dept["담당자들"]:
                rows.append(["홍보그룹", p.get("담당자",""), p.get("직급","")])
    # 나머지 부서들 처리
    for dept_name, dept in departments.items():
        if dept_name == "홍보그룹":  # 이미 처리했으므로 스킵
            continue
        if "담당자들" in dept:
            for p in dept["담당자들"]:
                rows.append([dept_name, p.get("담당자",""), p.get("직급","")])
        else:
            rows.append([dept_name, dept.get("담당자",""), dept.get("직급","")])
    df = pd.DataFrame(rows, columns=["부서명","담당자","직급"])
    show_table(df, "🔷 전체 부서 담당자 정보")
    st.markdown('</div>', unsafe_allow_html=True)

def page_history_search():
    # 60초마다 자동으로 파일 변경 체크 (백그라운드) - 성능 최적화
    st_autorefresh(interval=60000, key="history_autorefresh")

    # 파일 변경 감지 및 자동 새로고침
    try:
        current_mtime = os.path.getmtime(MEDIA_RESPONSE_FILE)
        if 'media_response_mtime' not in st.session_state:
            st.session_state.media_response_mtime = current_mtime
        elif st.session_state.media_response_mtime != current_mtime:
            st.session_state.media_response_mtime = current_mtime
            clear_all_caches()  # 캐시 클리어
            st.toast("✅ 언론대응내역 파일이 업데이트되어 자동 반영되었습니다!", icon="🔄")
            st.rerun()
    except Exception:
        pass

    # 데이터 로드 및 검증
    df_all = load_media_response_data()

    if df_all.empty:
        st.warning("❌ 데이터가 없습니다. 'data/언론대응내역.csv'를 확인해 주세요.")
        st.info("""
        **CSV 파일 형식:**
        ```
        순번,발생 일시,발생 유형,현업 부서,단계,이슈 발생 보고,대응 결과
        1,2024-01-15,기획기사,홍보팀,관심,포스코인터 관련 기사,연합뉴스
        ```
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # 필수 컬럼 검증
    required = ["발생 일시", "단계", "발생 유형", "현업 부서", "이슈 발생 보고", "대응 결과"]
    missing = [c for c in required if c not in df_all.columns]
    if missing:
        st.error(f"❌ 필수 컬럼이 없습니다: {', '.join(missing)}")
        st.info(f"**현재 컬럼:** {', '.join(df_all.columns.tolist())}")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # 날짜 파싱
    df_all["발생 일시"] = pd.to_datetime(df_all["발생 일시"], errors="coerce")
    valid_dates = df_all["발생 일시"].dropna()

    # 발생 유형 표준화 (유사한 카테고리 통합)
    type_mapping = {
        # 기사 게재 통합
        '기사게재': '기사 게재',
        '기사 게재': '기사 게재',

        # 기자 문의 통합
        '기자문의': '기자 문의',
        '기자 문의': '기자 문의',
        '언론 문의': '기자 문의',
        '언론문의': '기자 문의',

        # 기획기사 통합
        '기획기사': '기획기사',
        '기획자료': '기획기사',
        '기획자료 게재': '기획기사',
        '기획자료게재': '기획기사',

        # 잠재이슈 통합
        '잠재이슈': '잠재이슈',
        '잠재 이슈': '잠재이슈',

        # 보도자료 통합
        '보도자료': '보도자료',
        '보도자료 게재': '보도자료',
        '보도자료게재': '보도자료',
    }

    # 발생 유형 컬럼 표준화 적용
    if "발생 유형" in df_all.columns:
        df_all["발생 유형"] = df_all["발생 유형"].astype(str).str.strip()
        # nan, None, 빈 문자열 제거
        df_all["발생 유형"] = df_all["발생 유형"].replace(['nan', 'None', '', 'NaN', 'NAN'], pd.NA)
        df_all["발생 유형"] = df_all["발생 유형"].replace(type_mapping)

    # 2025년 데이터 필터링
    df_2025 = df_all[df_all["발생 일시"].dt.year == 2025].copy()

    # 2025년 통계 정보 표시 (상단에 바로 표시)
    stage_counts = df_2025["단계"].value_counts().to_dict()
    관심_count = stage_counts.get('관심', 0)
    주의_count = stage_counts.get('주의', 0)
    위기_count = stage_counts.get('위기', 0)
    비상_count = stage_counts.get('비상', 0)

    total = len(df_2025)
    관심_pct = (관심_count / total * 100) if total > 0 else 0
    주의_pct = (주의_count / total * 100) if total > 0 else 0
    위기_pct = (위기_count / total * 100) if total > 0 else 0
    비상_pct = (비상_count / total * 100) if total > 0 else 0

    # 전문적인 대시보드 카드 렌더링
    render_status_dashboard(
        total=total,
        status_counts={
            '관심': 관심_count,
            '주의': 주의_count,
            '위기': 위기_count,
            '비상': 비상_count
        },
        year=2025,
        show_live=True
    )

    st.markdown("---")

    # 검색 필터
    years = sorted(valid_dates.dt.year.unique().tolist()) if not valid_dates.empty else []
    # 발생 유형 옵션 생성 (nan, None, 빈 문자열 제외)
    type_options = ["전체"] + sorted([
        t for t in df_all["발생 유형"].dropna().unique().tolist()
        if t and str(t).lower() not in ['nan', 'none', '']
    ])

    st.markdown("### 🔍 검색 조건")
    with st.container():
        col_period, col_stage, col_type = st.columns([1, 1, 1])
        with col_period:
            period_mode = st.selectbox("기간", ["전체", "연도", "연월"], index=0, key="hist_period")
            sel_year = sel_month = None
            if period_mode == "연도" and years:
                sel_year = st.selectbox("연도 선택", options=years, index=len(years)-1, key="hist_year")
            elif period_mode == "연월" and years:
                sel_year = st.selectbox("연도 선택", options=years, index=len(years)-1, key="hist_year2")
                months = sorted(valid_dates[valid_dates.dt.year == sel_year].dt.month.unique().tolist())
                sel_month = st.selectbox("월 선택", options=months if months else [], key="hist_month")
        with col_stage:
            stage_option = st.selectbox("단계", ["전체", "관심", "주의", "위기", "비상"], index=0, key="hist_stage")
        with col_type:
            type_option = st.selectbox("발생 유형", type_options, index=0, key="hist_type")

    col_kw, col_btn = st.columns([4, 1])
    with col_kw:
        keyword = st.text_input("검색어", value="", placeholder="예) 포스코, 실적발표, IR (여러 단어 공백 → AND)", key="history_search_keyword")
    with col_btn:
        st.markdown('<div style="height: 1.6rem;"></div>', unsafe_allow_html=True)
        do_search = st.button("🔍 검색", use_container_width=True, type="primary")

    # 검색 실행
    if do_search:
        result_df = df_all.copy()

        # 기간 필터
        if period_mode == "연도" and sel_year is not None:
            result_df = result_df[result_df["발생 일시"].dt.year == sel_year]
        elif period_mode == "연월" and sel_year is not None and sel_month is not None:
            result_df = result_df[(result_df["발생 일시"].dt.year == sel_year) &
                                  (result_df["발생 일시"].dt.month == int(sel_month))]

        # 단계 필터
        if stage_option != "전체":
            result_df = result_df[result_df["단계"].astype(str).str.contains(stage_option, case=False, na=False)]

        # 발생 유형 필터
        if type_option != "전체":
            result_df = result_df[result_df["발생 유형"].astype(str).str.contains(type_option, case=False, na=False)]

        # 키워드 검색 (AND 조건)
        if keyword.strip():
            terms = [t for t in keyword.split() if t.strip()]
            target_cols = ["발생 유형", "현업 부서", "이슈 발생 보고", "대응 결과"]
            for t in terms:
                mask_any = result_df[target_cols].astype(str).apply(
                    lambda col: col.str.contains(t, case=False, na=False)
                ).any(axis=1)
                result_df = result_df[mask_any]

        # 결과 표시
        if not result_df.empty:
            try:
                result_df = result_df.sort_values("발생 일시", ascending=False)
            except Exception:
                pass

            st.markdown("---")
            st.markdown(f"### 📈 검색 결과: 총 **{len(result_df):,}건**")

            # 결과 테이블 표시 (순번 제외, 날짜 포맷팅)
            display_df = result_df.copy()
            if "발생 일시" in display_df.columns:
                display_df["발생 일시"] = display_df["발생 일시"].dt.strftime("%Y-%m-%d").fillna("")

            # 순번 컬럼 제외
            display_cols = [c for c in display_df.columns if c != "순번"]
            display_df = display_df[display_cols]

            # 컬럼명 한글화
            display_df = display_df.rename(columns={
                "발생 일시": "📅 발생일시",
                "발생 유형": "📑 유형",
                "현업 부서": "🏢 부서",
                "단계": "⚠️ 단계",
                "이슈 발생 보고": "📰 이슈 내용",
                "대응 결과": "✅ 대응 결과"
            })

            show_table(display_df, "")
        else:
            st.warning("❌ 검색 조건에 맞는 내역이 없습니다.")

def page_news_monitor():
    # ===== 기본 파라미터 =====
    keywords = [
        "포스코인터내셔널",
        "POSCO INTERNATIONAL",
        "포스코인터",
        "삼척블루파워",
        "구동모터코아",
        "구동모터코어",
        "미얀마 LNG",
        "포스코모빌리티솔루션",
        "포스코"  # 일반 포스코 기사 (기존 키워드 제외 필터링 적용)
    ]
    # 포스코 검색 결과에서 제외할 키워드 (중복 방지)
    exclude_keywords = ["포스코인터내셔널", "POSCO INTERNATIONAL", "포스코인터",
                       "삼척블루파워", "포스코모빌리티솔루션"]

    refresh_interval = 180  # 180초 카운트다운 (3분) - 빠른 업데이트
    max_items = 100  # 키워드당 약 11개 수집 (필터링 후 충분한 기사 확보)

    # ===== 세션 상태 기본값 =====
    now = time.time()
    if "next_refresh_at" not in st.session_state:
        st.session_state.next_refresh_at = now + refresh_interval
    if "last_news_fetch" not in st.session_state:
        st.session_state.last_news_fetch = 0.0   # 마지막 수집 시각
    if "initial_loaded" not in st.session_state:
        st.session_state.initial_loaded = False  # 첫 렌더 이후 True
    if "trigger_news_update" not in st.session_state:
        st.session_state.trigger_news_update = False

    # ===== 당일 뉴스 현황 대시보드 (최상단 배치) =====
    # 세션에 최신 수집 데이터가 있으면 우선 사용 (즉시 반영)
    db_for_dashboard = st.session_state.get('news_display_data', load_news_db())
    render_news_dashboard(db_for_dashboard, show_live=True)

    # ===== 상단 UI (카운트다운/상태/수동 새로고침) =====
    c_count, c_status, c_btn = st.columns([1, 2.5, 1])
    with c_btn:
        manual_refresh = st.button("🔄 지금 새로고침", use_container_width=True)
    with c_status:
        status = st.empty()

    # 카운트다운 프래그먼트 (1초 단위 업데이트)
    with c_count:
        countdown_fragment(refresh_interval)

    # 최소 간격의 구분선
    st.markdown('<div style="margin: 8px 0;"></div>', unsafe_allow_html=True)

    # ===== 새로고침 방식 결정 =====
    # 수동 새로고침: Naver API 직접 호출 (실시간 최신 뉴스)
    # 자동 새로고침/초기 로드: Naver API 호출 (최신 데이터)
    if manual_refresh:
        # 수동 새로고침: Naver API 직접 호출하여 실시간 뉴스 수집
        should_fetch = True
        st.session_state.trigger_news_update = True

        # 보고서 초기화
        report_keys = [key for key in st.session_state.keys() if key.startswith('report_state_')]
        for key in report_keys:
            del st.session_state[key]
        if report_keys:
            print(f"[DEBUG] 수동 새로고침: {len(report_keys)}개 보고서 초기화")

        # 타이머 리셋
        st.session_state.next_refresh_at = time.time() + refresh_interval
    else:
        # 자동 새로고침 또는 초기 로드: Naver API 호출
        should_fetch = st.session_state.trigger_news_update or (not st.session_state.initial_loaded)

        # 자동 새로고침 시 보고서 초기화
        if st.session_state.trigger_news_update:
            report_keys = [key for key in st.session_state.keys() if key.startswith('report_state_')]
            for key in report_keys:
                del st.session_state[key]
            if report_keys:
                print(f"[DEBUG] 자동 새로고침: {len(report_keys)}개 보고서 초기화")

    # ===== 뉴스 수집 로직 =====
    if should_fetch:
        # 수집 직전 상태 메시지
        status.info("🔄 최신 기사를 가져오는 중…")

        # API 키 유효성 체크
        headers = _naver_headers()
        api_ok = bool(headers.get("X-Naver-Client-Id") and headers.get("X-Naver-Client-Secret"))

        # 초기엔 DB가 있으면 먼저 보여주고(끊김 없는 화면), 백그라운드처럼 바로 수집 시도
        existing_db = load_news_db()

        try:
            all_news = []
            quota_exceeded = False

            if api_ok:
                # 키워드별 최신순 수집
                for kw in keywords:
                    df_kw = crawl_naver_news(kw, max_items=max_items // len(keywords), sort="date")

                    # API 할당량 초과 체크
                    if df_kw.attrs.get('quota_exceeded', False):
                        print(f"[DEBUG] ⚠️ API 할당량 초과 감지 - 뉴스 수집 중단")
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

                                # 제외 키워드 체크
                                exclude_words = ["청약", "분양", "입주", "재건축", "정비구역"]
                                for exclude_word in exclude_words:
                                    if exclude_word in title or exclude_word in description:
                                        return False

                                return True

                            mask = df_kw.apply(should_include_posco_intl, axis=1)
                            df_kw = df_kw[mask].reset_index(drop=True)
                            if not df_kw.empty:
                                print(f"[DEBUG] '포스코인터내셔널' 정확 매칭 필터링 완료: {len(df_kw)}건 추가")

                        # "포스코모빌리티솔루션" 정확한 매칭 강화
                        elif kw == "포스코모빌리티솔루션":
                            def should_include_posco_mobility(row):
                                title = str(row.get("기사제목", ""))
                                description = str(row.get("주요기사 요약", ""))

                                # 정확히 "포스코모빌리티솔루션"이 포함되어야 함
                                if "포스코모빌리티솔루션" not in title and "포스코모빌리티솔루션" not in description:
                                    return False

                                # 제외 키워드 체크
                                exclude_words = ["청약", "분양", "입주", "재건축", "정비구역"]
                                for exclude_word in exclude_words:
                                    if exclude_word in title or exclude_word in description:
                                        return False

                                return True

                            mask = df_kw.apply(should_include_posco_mobility, axis=1)
                            df_kw = df_kw[mask].reset_index(drop=True)
                            if not df_kw.empty:
                                print(f"[DEBUG] '포스코모빌리티솔루션' 정확 매칭 필터링 완료: {len(df_kw)}건 추가")

                        # "포스코" 키워드의 경우 특별 처리
                        elif kw == "포스코":
                            def should_include_posco(row):
                                title = str(row.get("기사제목", ""))
                                title_lower = title.lower()
                                description = str(row.get("주요기사 요약", ""))  # 내용 필드
                                content_lower = description.lower()

                                # 기존 조건: 타이틀에 "포스코" 포함
                                title_has_posco = "포스코" in title or "posco" in title_lower

                                # 새 조건: 타이틀에 "[단독]" 포함 AND 내용에 "포스코" 포함
                                is_exclusive_with_posco_in_content = "[단독]" in title and "포스코" in description

                                # 둘 중 하나라도 만족하면 포함 (1단계)
                                if not (title_has_posco or is_exclusive_with_posco_in_content):
                                    return False

                                # 2단계: 제목에 제외 키워드(포스코인터내셔널 등)가 없는가?
                                for exclude_kw in exclude_keywords:
                                    if exclude_kw.lower() in title_lower:
                                        return False

                                # 3단계: 제목 또는 내용에 부동산 키워드가 없는가?
                                exclude_words = ["청약", "분양", "입주", "재건축", "정비구역"]
                                for exclude_word in exclude_words:
                                    if exclude_word in title or exclude_word in description:
                                        return False

                                return True

                            # 포스코 전용 필터링 적용
                            mask_posco = df_kw.apply(should_include_posco, axis=1)
                            df_kw = df_kw[mask_posco].reset_index(drop=True)
                            if not df_kw.empty:
                                print(f"[DEBUG] '포스코' 필터링 완료: {len(df_kw)}건 추가")

                        else:
                            # 다른 키워드는 기존처럼 제목에서만 부동산 관련 키워드 제거
                            exclude_words = ["분양", "청약", "입주", "재건축", "정비구역"]
                            def should_include_general(row):
                                title = str(row.get("기사제목", ""))
                                for exclude_word in exclude_words:
                                    if exclude_word in title:
                                        return False
                                return True

                            mask_general = df_kw.apply(should_include_general, axis=1)
                            df_kw = df_kw[mask_general].reset_index(drop=True)

                        if not df_kw.empty:
                            all_news.append(df_kw)

                # API 할당량 초과 시 처리
                if quota_exceeded:
                    status.error("❌ API 할당량 초과 (일일 25,000회 제한)\n\n"
                                "💡 해결 방법:\n"
                                "1. 새로운 네이버 개발자 계정으로 API 키 재발급\n"
                                "2. 매일 자정(KST) 이후 할당량 재설정\n"
                                "3. 기존 저장된 뉴스 데이터는 유지됩니다")
                    # 플래그 리셋
                    st.session_state.trigger_news_update = False
                    st.session_state.next_refresh_at = time.time() + refresh_interval
                    st.session_state.initial_loaded = True
                else:
                    # 통합 정리 & 저장
                    df_new = pd.concat(all_news, ignore_index=True) if all_news else pd.DataFrame()
                    if not df_new.empty:
                        df_new["날짜_datetime"] = pd.to_datetime(df_new["날짜"], errors="coerce")
                        df_new = df_new.sort_values("날짜_datetime", ascending=False, na_position="last").reset_index(drop=True)
                        df_new = df_new.drop("날짜_datetime", axis=1)

                        # 중복 제거 (URL 우선, 없으면 제목+날짜)
                        key = df_new["URL"].where(df_new["URL"].astype(bool), df_new["기사제목"] + "|" + df_new["날짜"])
                        df_new = df_new.loc[~key.duplicated()].reset_index(drop=True)

                        # 기존 DB와 병합해 최신순 정렬
                        merged = pd.concat([df_new, existing_db], ignore_index=True) if not existing_db.empty else df_new
                        merged = merged.drop_duplicates(subset=["URL", "기사제목"], keep="first").reset_index(drop=True)
                        if not merged.empty:
                            merged["날짜"] = pd.to_datetime(merged["날짜"], errors="coerce")
                            merged = merged.sort_values("날짜", ascending=False, na_position="last").reset_index(drop=True)
                            merged["날짜"] = merged["날짜"].dt.strftime("%Y-%m-%d %H:%M")

                        # 신규 기사 감지 (참고용)
                        new_articles = detect_new_articles(existing_db, df_new)

                        # 🔒 Streamlit은 읽기 전용 모드 - DB 저장 비활성화
                        # DB 저장과 텔레그램 알림은 GitHub Actions에서만 담당
                        # save_news_db(merged)  # 비활성화

                        # 세션 상태에만 저장 (UI 표시용)
                        st.session_state.news_display_data = merged

                        # 🔒 텔레그램 알림 비활성화 - GitHub Actions 전용
                        # send_telegram_notification(new_articles)  # 비활성화

                        if new_articles:
                            print(f"[STREAMLIT] 신규 기사 {len(new_articles)}건 감지 (텔레그램은 GitHub Actions에서 발송)")
                        st.session_state.last_news_fetch = now

                        # 상태 메시지에 신규 기사 수 표시
                        if new_articles:
                            status.success(f"✅ 기사 업데이트 완료! 신규 {len(new_articles)}건 (총 {len(merged)}건 저장)")
                        else:
                            status.success(f"✅ 기사 업데이트 완료! 현재 저장된 건수: {len(merged)}")
                    else:
                        # 결과 없음이어도 조용히 다음 라운드(180초 뒤)로 넘어감
                        status.info("ℹ️ 새로 수집된 기사가 없어요. 다음 라운드에서 다시 시도할게.")
            else:
                # API 키 없으면 그냥 DB만 유지 표시
                if existing_db.empty:
                    status.warning("⚠️ API 키가 없고, 저장된 데이터도 없어요. 키 설정 후 다시 시도해줘.")
                else:
                    status.info("ℹ️ API 키가 없어 저장된 데이터만 표시 중이에요.")

        except Exception as e:
            # 오류 메시지를 간단히만 (초기 데이터 불가 문구는 제거)
            status.error(f"❌ 뉴스 수집 오류: {e}")

        # 플래그 먼저 리셋하고 다음 라운드 타임스탬프 갱신
        st.session_state.trigger_news_update = False
        st.session_state.next_refresh_at = time.time() + refresh_interval
        st.session_state.initial_loaded = True

    # ===== 화면 표시 (저장된 최신 데이터 기준) =====
    st.markdown("---")
    # 세션에 최신 수집 데이터가 있으면 우선 사용 (즉시 반영)
    db = st.session_state.get('news_display_data', load_news_db())

    # 🔍 디버그 정보 표시
    if not db.empty and "날짜" in db.columns:
        latest_article = db["날짜"].iloc[0] if len(db) > 0 else "N/A"
        load_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f'<div style="background: #1e1e1e; padding: 8px; border-radius: 4px; margin-bottom: 12px; font-size: 12px; color: #888;">'
                   f'📊 DB 로드: {load_time} | 총 {len(db)}건 | 최신 기사: {latest_article}</div>',
                   unsafe_allow_html=True)

    if db.empty:
        st.markdown('<p style="color: white;">📰 저장된 뉴스 데이터가 없습니다.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # 키워드 필터 & 정렬
    pattern = "|".join(keywords)
    df_show = db[db["검색키워드"].astype(str).str.contains(pattern, case=False, na=False)].copy()
    if df_show.empty:
        st.markdown('<p style="color: white;">📰 POSCO 관련 기사가 없습니다.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    df_show = df_show.sort_values(by="날짜", ascending=False, na_position="last").reset_index(drop=True).head(50)
    if "URL" in df_show.columns:
        df_show["매체명"] = df_show["URL"].apply(_publisher_from_link)
    if "매체명" in df_show.columns:
        df_show["매체명"] = df_show.apply(
            lambda row: _publisher_from_link(row["URL"]) if pd.notna(row["URL"]) else row["매체명"], axis=1
        )

    ch1, ch2 = st.columns([3, 1])
    with ch1:
        st.markdown(f"**포스코인터내셔널 관련 기사: 최신 {len(df_show)}건**")
    with ch2:
        st.download_button(
            "⬇ CSV 다운로드",
            df_show.to_csv(index=False).encode("utf-8"),
            file_name=f"posco_news_{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    st.markdown('<p style="color: white; font-weight: 600; margin-bottom: 8px;">표시 방식</p>', unsafe_allow_html=True)
    
    # 라디오 버튼 텍스트 색상을 하얀색으로 변경
    st.markdown("""
    <style>
    div[data-testid="stRadio"] > div {
        color: white !important;
    }
    div[data-testid="stRadio"] label {
        color: white !important;
    }
    div[data-testid="stRadio"] label > div {
        color: white !important;
    }
    div[data-testid="stRadio"] span {
        color: white !important;
    }
    div[data-testid="stRadio"] p {
        color: white !important;
    }
    .stRadio > label > div[data-testid="stMarkdownContainer"] > p {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    view = st.radio("", ["카드형 뷰", "테이블 뷰"], index=0, horizontal=True, key="news_view", label_visibility="collapsed")

    if view == "카드형 뷰":
        st.markdown("""
<style>
  /* 컴팩트한 뉴스 카드 스타일 */
  .news-card{
    background: #1E1E1E;
    border: 1px solid #2A2A2A;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: all 0.2s ease;
    position: relative;
  }
  .news-card:hover{
    background: #252525;
    border-color: #3A3A3A;
  }

  /* 상단: 출처 태그와 날짜 */
  .news-header{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  .news-left{
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .news-media{
    background: rgba(212,175,55,.2);
    color: #D4AF37;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
  }
  .news-key{
    background: rgba(135,206,235,.12);
    color: #87CEEB;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
  }
  .news-date{
    color: #AAAAAA;
    font-size: 12px;
    font-weight: 400;
  }

  /* 중간: 제목과 요약 */
  .news-title{
    color: #FFFFFF;
    font-size: 16px;
    font-weight: 600;
    line-height: 1.4;
    margin: 0 0 8px 0;
    word-break: break-word;
  }
  .news-summary{
    color: #CCCCCC;
    font-size: 13px;
    line-height: 1.5;
    margin: 0 0 12px 0;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }

  /* 하단: 링크와 버튼 좌측 정렬 */
  .news-footer{
    display: flex;
    justify-content: flex-start;
    align-items: center;
    gap: 8px;
  }
  .news-link a{
    color: #55b7ff;
    text-decoration: none;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s ease;
    word-break: break-all;
  }
  .news-link a:hover{
    text-decoration: underline;
  }

  /* 보고서 생성 버튼 - 작고 컴팩트하게 */
  button[kind="secondary"] {
    height: auto !important;
    min-height: auto !important;
    padding: 4px 10px !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    transition: all 0.2s ease !important;
    background-color: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
  }
  button[kind="secondary"]:hover {
    background-color: #D4AF37 !important;
    border-color: #D4AF37 !important;
    color: #1E1E1E !important;
  }

  /* 생성된 보고서 스타일 */
  .report-container {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    color: #e0e0e0;
    font-family: monospace;
    white-space: pre-wrap;
    line-height: 1.5;
    font-size: 13px;
  }
</style>
""", unsafe_allow_html=True)

        for i, (_, row) in enumerate(df_show.iterrows()):
            title   = str(row.get("기사제목", "")).strip('"')
            summary = str(row.get("주요기사 요약", ""))
            summary = (summary[:150] + "...") if len(summary) > 150 else summary
            media   = str(row.get("매체명", ""))
            keyword = str(row.get("검색키워드", ""))
            url = str(row.get("URL", ""))
            dt = str(row.get("날짜", ""))
            sentiment = str(row.get("sentiment", "pos"))
            if " " in dt:
                d, t = dt.split(" ", 1)
                formatted_dt = f"📅 {d}  🕐 {t}"
            else:
                formatted_dt = f"📅 {dt}"

            # 감성 dot 설정
            if sentiment == "neg":
                sentiment_dot = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#ef4444;margin-right:6px;vertical-align:middle;"></span>'
            else:
                sentiment_dot = '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:#22c55e;margin-right:6px;vertical-align:middle;"></span>'

            # 파일명에 사용할 안전한 제목 생성
            safe_name = re.sub(r'[^\w가-힣\s]', '', title)[:30]

            # 컨테이너로 카드 전체 감싸기
            with st.container():
                # 뉴스 카드 렌더링
                st.markdown(f"""
                <div class="news-card">
                  <!-- 상단: 출처 태그와 날짜 -->
                  <div class="news-header">
                    <div class="news-left">
                      {sentiment_dot}<span class="news-media">{media}</span>
                      <span class="news-key">#{keyword}</span>
                    </div>
                    <span class="news-date">{formatted_dt}</span>
                  </div>

                  <!-- 제목 (한 줄, 말줄임) -->
                  <div class="news-title">{title}</div>

                  <!-- 요약 (최대 2줄) -->
                  <div class="news-summary">{summary}</div>

                  <!-- 하단: 링크와 버튼 우측 정렬 -->
                  <div class="news-footer">
                    <div class="news-link">
                      <a href="{url}" target="_blank">🔗 {url}</a>
                    </div>
                """, unsafe_allow_html=True)

                # 보고서 생성 버튼
                report_key = f"report_btn_{i}"
                report_state_key = f"report_state_{i}"

                # 보고서 상태 초기화
                if report_state_key not in st.session_state:
                    st.session_state[report_state_key] = {"generated": False, "content": ""}

                # 버튼만 배치 (우측 정렬)
                if st.button("📄 보고서 생성", key=report_key, type="secondary"):
                    with st.spinner("기사 요약 생성 중..."):
                        try:
                            report_txt = make_kakao_report_from_url(
                                url, fallback_media=media, fallback_title=title, fallback_summary=summary
                            )
                            st.session_state[report_state_key]["generated"] = True
                            st.session_state[report_state_key]["content"] = report_txt
                            st.rerun()
                        except Exception as e:
                            backup_report = f"{url}\n\n{media} : \"{title}\"\n- 핵심 요약은 원문 참고\n- 상세 내용은 링크 확인 필요"
                            st.session_state[report_state_key]["generated"] = True
                            st.session_state[report_state_key]["content"] = backup_report
                            st.rerun()

                # 카드 닫기
                st.markdown("""
                  </div>
                </div>
                """, unsafe_allow_html=True)
            
            # 보고서가 생성된 경우 하단에 표시
            if st.session_state[report_state_key]["generated"]:
                st.code(
                    st.session_state[report_state_key]["content"],
                    language=None
                )

    else:
        df_table = df_show[["날짜","매체명","검색키워드","기사제목","주요기사 요약","URL"]].rename(columns={
            "날짜":"📅 발행일시","매체명":"📰 언론사","검색키워드":"🔍 키워드","기사제목":"📰 제목","주요기사 요약":"📝 요약","URL":"🔗 링크"
        })
        st.dataframe(
            df_table,
            use_container_width=True,
            height=min(700, 44 + max(len(df_table), 12)*35),
            column_config={
                "🔗 링크": st.column_config.LinkColumn("🔗 링크", help="기사 원문 링크", display_text="기사보기"),
                "📝 요약": st.column_config.TextColumn("📝 요약", help="기사 요약", max_chars=100)
            }
        )

# ----------------------------- 메인 루틴 -----------------------------
def main():
    # 백그라운드 스케줄러 비활성화 (GitHub Actions에서 자동 알림 처리)
    # if "background_scheduler_started" not in st.session_state:
    #     start_background_scheduler()
    #     st.session_state["background_scheduler_started"] = True

    # 인증 체크 - 인증되지 않은 경우 로그인 페이지 표시
    if not check_authentication():
        show_login_page()
        return

    load_base_css()
    if "data_loaded" not in st.session_state:
        st.session_state["data_loaded"] = True

    active = set_active_menu_from_url()
    # 메뉴 변경 감지 및 입력 상태 초기화 (개선됨)
    if "current_menu" not in st.session_state:
        st.session_state.current_menu = active
    elif st.session_state.current_menu != active:
        # 메뉴가 변경되었을 때 모든 입력 관련 세션 상태 정리 (최적화됨)
        prefixes = ('issue_', 'media_search_', 'contact_search_', 'history_search_',
                   'news_view', 'widget_', 'text_input_', 'text_area_', 'selectbox_')
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith(prefixes)]

        # 삭제할 키가 있을 때만 삭제 및 rerun (성능 최적화)
        if keys_to_clear:
            for key in keys_to_clear:
                st.session_state.pop(key, None)  # KeyError 방지

            # 메뉴 상태 즉시 업데이트
            st.session_state.current_menu = active
            st.rerun()
        else:
            # 삭제할 키가 없으면 메뉴 상태만 업데이트 (rerun 생략)
            st.session_state.current_menu = active
    
    render_top_nav(active)

    if active == "메인":
        render_main_page()
    elif active == "이슈발생보고 생성":
        page_issue_report()
    elif active == "언론사 정보 검색":
        page_media_search()
    elif active == "담당자 정보 검색":
        page_contact_search()
    elif active == "기존대응이력 검색":
        page_history_search()
    elif active == "뉴스 모니터링":
        page_news_monitor()
    else:
        # 잘못된 파라미터면 메인으로 보냄
        st.query_params["menu"] = "메인"
        st.rerun()

    # 버전 정보 표시 (하단, 작게)
    st.markdown(
        f'<div style="text-align: center; color: rgba(255,255,255,0.3); font-size: 11px; margin-top: 40px; padding-bottom: 20px;">'
        f'v2.0.1 | 2025-11-28 | 로그인/타이머 수정'
        f'</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()