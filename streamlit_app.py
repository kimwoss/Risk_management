# streamlit_app.py
# Version: 2025-12-02-10:45 (Publisher mapping update trigger)
"""
포스코인터내셔널 언론대응 보고서 생성 시스템
- 상단 네비: 순수 Streamlit 버튼 기반 (iFrame/JS 제거, 확실한 리런)
- 중복된 로더/스타일 정리
"""
import os, json, re, time, base64, mimetypes, urllib.parse, requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import threading

# 공통 뉴스 수집 모듈 import
from news_collector import (
    KEYWORDS,
    EXCLUDE_KEYWORDS,
    MAX_ITEMS_PER_RUN,
    tag_priority,
    crawl_naver_news,
    crawl_google_news_rss,
    merge_news_sources,
    load_news_db,
    _publisher_from_link,
    _clean_text,
    _naver_headers,
    load_sent_cache,
    save_sent_cache,
    get_article_sentiment,
    load_api_usage,
)

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import extra_streamlit_components as stx
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
    page_title="P-IRIS",
    page_icon="🛡️",
    layout="centered",
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
ACCESS_CODE = os.environ.get("ACCESS_CODE", "")  # 환경 변수에서 로드 (.env 파일 또는 배포 환경 설정)
import hashlib

# secrets.toml 예시 파일의 플레이스홀더 문구 — 실제 비밀번호로 취급하지 않음
_PLACEHOLDER_PW_MARKERS = ("여기에", "비밀번호_입력")


def _resolve_password(role="pr") -> str:
    """역할별 비밀번호 단일 조회 헬퍼 (소스 이원화 지뢰 제거).
    우선순위: Streamlit secrets → 환경변수(.env). 플레이스홀더 값은 무시.
    배포(Cloud Secrets)와 로컬(.env ACCESS_CODE) 어느 쪽만 설정돼 있어도 동작."""
    def _secret(key):
        try:
            return st.secrets.get(key, "")
        except Exception:
            return ""

    if role == "general":
        candidates = [_secret("PASSWORD_GENERAL"), os.environ.get("PASSWORD_GENERAL", "")]
    else:
        candidates = [
            _secret("PASSWORD_PR"),
            os.environ.get("PASSWORD_PR", ""),
            os.environ.get("ACCESS_CODE", ""),
        ]
    for pw in candidates:
        pw = str(pw or "").strip()
        if pw and not any(m in pw for m in _PLACEHOLDER_PW_MARKERS):
            return pw
    return ""


def get_auth_token(role="pr"):
    """인증 토큰 생성 (보안을 위해 해시 사용)"""
    pw = _resolve_password(role)
    return hashlib.sha256(f"{pw}_secret_salt".encode()).hexdigest()

# 로그인 유지 쿠키 이름 / 유효기간(24시간)
AUTH_COOKIE = "posco_auth"
AUTH_COOKIE_TTL = timedelta(hours=24)

# 테마 쿠키 (라이트/다크 토글 상태 1년 유지)
THEME_COOKIE = "piris_theme"
THEME_COOKIE_TTL = timedelta(days=365)


def get_cookie_manager():
    """쿠키 매니저 (세션별 1개 — 양방향 컴포넌트로 Python에서 직접 읽기/쓰기).
    cache_resource를 쓰면 전 세션이 인스턴스를 공유해 쿠키가 섞일 수 있어 세션 상태에 보관한다."""
    if "_piris_cm" not in st.session_state:
        st.session_state["_piris_cm"] = stx.CookieManager(key="piris_cookie_mgr")
    return st.session_state["_piris_cm"]


def set_auth_cookie(role="pr"):
    """로그인 성공 시 인증 토큰을 쿠키에 저장 (24시간 유지)"""
    cm = get_cookie_manager()
    cm.set(
        AUTH_COOKIE,
        get_auth_token(role),
        expires_at=datetime.now() + AUTH_COOKIE_TTL,
        key="piris_auth_set",
    )


def get_current_theme() -> str:
    """현재 테마 반환 (session → 인증 런의 쿠키 스냅샷 → 자체 쿠키 조회 → dark).
    쿠키 동기화가 안 끝난 런에는 세션에 고정하지 않고 dark를 임시 반환해,
    다음 런에서 저장된 테마가 올바르게 복원되도록 한다."""
    theme = st.session_state.get("theme")
    if theme in ("dark", "light"):
        return theme

    # 1) 인증 복원 런에서 저장해 둔 쿠키 스냅샷 재사용 (추가 component 마운트 0)
    snapshot = st.session_state.get("_cookies_snapshot")
    if snapshot is not None:
        theme = snapshot.get(THEME_COOKIE, "dark")
        if theme not in ("dark", "light"):
            theme = "dark"
        st.session_state["theme"] = theme
        return theme

    # 2) 스냅샷 없으면 자체 조회 — 동기화 전(None)이면 세션 고정 없이 임시 dark
    try:
        cm = get_cookie_manager()
        cookies = cm.get_all(key="piris_theme_get")
    except Exception:
        cookies = None
    if cookies is None:
        return "dark"
    theme = cookies.get(THEME_COOKIE, "dark")
    if theme not in ("dark", "light"):
        theme = "dark"
    st.session_state["theme"] = theme
    return theme


def set_theme(theme: str):
    """테마 변경: 세션 갱신 + 쿠키 1년 저장 (기존 CookieManager 재사용, 신규 의존성 0)"""
    st.session_state["theme"] = theme
    try:
        cm = get_cookie_manager()
        cm.set(
            THEME_COOKIE,
            theme,
            expires_at=datetime.now() + THEME_COOKIE_TTL,
            key="piris_theme_set",
        )
    except Exception:
        pass


def apply_theme_attribute(theme: str):
    """<html data-theme='…'> 속성 주입 — Streamlit은 리런마다 DOM을 다시 그리므로
    매 렌더마다 재적용해야 한다. (st.markdown은 <script>를 제거하므로 components.html 사용)"""
    import streamlit.components.v1 as _components
    _components.html(
        f"<script>window.parent.document.documentElement.setAttribute('data-theme', '{theme}');</script>",
        height=0,
    )


def clear_auth_cookie():
    """로그아웃 시 인증 쿠키 삭제"""
    cm = get_cookie_manager()
    try:
        cm.delete(AUTH_COOKIE, key="piris_auth_del")
    except Exception:
        pass


def logout():
    """로그아웃: 세션 정리 + 쿠키 삭제 + 로그인 화면으로.
    쿠키 삭제(컴포넌트)가 브라우저에 반영되기 전 rerun될 수 있으므로
    _logout_requested 플래그로 쿠키 복원을 차단한다 (재로그인 시 해제)."""
    st.session_state.pop("authenticated", None)
    st.session_state.pop("role", None)
    st.session_state["_logout_requested"] = True
    clear_auth_cookie()
    st.rerun()


def check_authentication():
    """인증 확인 (세션 → 쿠키 순). 세션이 끊겨도 24시간 내면 쿠키로 자동 복원."""
    # 로그아웃 직후: 쿠키 삭제가 아직 브라우저에 반영 안 됐어도 복원을 차단
    if st.session_state.get("_logout_requested"):
        clear_auth_cookie()  # 반영될 때까지 재시도 (멱등)
        return False

    # 이미 세션에서 인증됨
    if st.session_state.get("authenticated", False):
        return True

    # 쿠키에서 인증 복원 (컴포넌트가 브라우저 쿠키를 Python으로 동기화)
    cm = get_cookie_manager()
    cookies = cm.get_all(key="piris_auth_get")
    if cookies is not None:
        # 같은 런에서 테마 등 다른 쿠키도 재사용 (컴포넌트 중복 마운트 방지)
        st.session_state["_cookies_snapshot"] = cookies
    token = cookies.get(AUTH_COOKIE) if cookies else None
    if token:
        if token == get_auth_token("pr"):
            st.session_state.authenticated = True
            st.session_state["role"] = "pr"
            return True
        if token == get_auth_token("general"):
            st.session_state.authenticated = True
            st.session_state["role"] = "general"
            return True

    return False

def show_login_page():
    """로그인 페이지 — 에디토리얼 센터 카드 디자인"""
    # ── 배경 이미지 로드 (data/ 또는 스크립트 옆 폴더 모두 탐색) ──
    _candidates = [
        Path(os.path.abspath("data")) / "Image_login.jpg",
        Path(__file__).parent / "Image_login.jpg",
        Path(__file__).parent / "data" / "Image_login.jpg",
    ]
    _img_b64 = ""
    for _p in _candidates:
        if _p.exists():
            _img_b64 = base64.b64encode(_p.read_bytes()).decode()
            break

    # ── CSS 주입 ──────────────────────────────────────────────────
    st.markdown(
        f"""
<meta name="robots" content="noindex, nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css" rel="stylesheet">

<style>
  :root {{
    --ink:        #0A1628;
    --ink-soft:   #1f2a3d;
    --ivory:      #F8F5F0;
    --amber:      #E89547;
    --amber-deep: #B86B2E;
    --line:       #E2DCD2;
    --muted:      #7A7366;
    --body:       "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    --display:    "Instrument Serif", "Pretendard Variable", serif;
  }}

  /* Hide Streamlit chrome */
  #MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}
  .stDeployButton, [data-testid="stToolbar"] {{ display: none !important; }}
  [data-testid="stDecoration"] {{ display: none; }}
  section[data-testid="stSidebar"] {{ display: none !important; }}

  /* Full-viewport background image — 좌측 폼 영역 어둡게 강화 */
  .stApp {{
    background:
      linear-gradient(90deg, rgba(10,22,40,0.55) 0%, rgba(10,22,40,0.15) 35%,
                              rgba(10,22,40,0) 60%,  rgba(10,22,40,0.15) 100%),
      linear-gradient(180deg, rgba(10,22,40,0.35) 0%, rgba(10,22,40,0) 24%,
                               rgba(10,22,40,0) 58%,  rgba(10,22,40,0.62) 100%),
      url("data:image/jpeg;base64,{_img_b64}") center/cover no-repeat fixed;
    font-family: var(--body);
  }}

  /* 구/신 Streamlit 통합 타깃 — 다크 글래스 패널 */
  .main .block-container,
  section.main > div.block-container,
  [data-testid="stMain"] .block-container,
  [data-testid="stMainBlockContainer"],
  .stMainBlockContainer,
  div[class*="block-container"] {{
    max-width: 440px !important;
    width: 440px !important;
    margin-left: 80px !important;
    margin-right: auto !important;
    margin-top: 10vh !important;
    padding: 48px 44px !important;
    background: rgba(10, 22, 40, 0.55) !important;
    backdrop-filter: blur(24px) saturate(1.2) !important;
    -webkit-backdrop-filter: blur(24px) saturate(1.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-top: 1px solid rgba(232, 149, 71, 0.5) !important;
    box-shadow:
      0 1px 0 rgba(255,255,255,0.08) inset,
      0 30px 80px rgba(0,0,0,0.35) !important;
    border-radius: 0 !important;
  }}

  /* st.form 래퍼 */
  [data-testid="stForm"],
  div[data-testid="stForm"] {{
    width: 100% !important;
    max-width: 440px !important;
    border: none !important;
    padding: 0 !important;
  }}

  /* 위젯 폭 초과 방지 */
  .stTextInput, .stButton, .stFormSubmitButton, .stCheckbox {{
    width: 100% !important;
    max-width: 440px !important;
  }}

  /* Fixed overlays */
  .overlay-brand, .overlay-lang, .overlay-caption, .overlay-meta {{
    position: fixed; z-index: 10;
    color: #fff;
    text-shadow: 0 1px 3px rgba(0,0,0,0.25);
  }}
  .overlay-brand {{
    top: 36px; left: 44px;
    display: flex; align-items: center; gap: 14px;
    font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; font-weight: 500;
  }}
  .overlay-brand .mark {{
    width: 22px; height: 22px;
    border: 1px solid rgba(255,255,255,0.8);
    display: grid; place-items: center;
  }}
  .overlay-brand .mark::after {{
    content: ""; width: 6px; height: 6px; background: var(--amber); border-radius: 50%;
  }}
  .overlay-caption {{
    left: 44px; bottom: 44px; max-width: 440px;
    text-shadow: 0 2px 12px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.4) !important;
  }}
  .overlay-caption .rule {{
    width: 48px; height: 1px; background: rgba(255,255,255,0.7); margin-bottom: 18px;
  }}
  .overlay-caption .title {{
    font-family: var(--display); font-weight: 400;
    font-size: 32px; line-height: 1.1; letter-spacing: -0.01em;
  }}
  .overlay-caption .title em {{ font-style: italic; color: #F6C08A; }}
  .overlay-meta {{
    right: 44px; bottom: 46px;
    font-size: 10.5px; letter-spacing: 0.22em; text-transform: uppercase;
    text-align: right; opacity: 0.82; line-height: 1.7;
    text-shadow: 0 2px 12px rgba(0,0,0,0.55), 0 1px 3px rgba(0,0,0,0.4) !important;
  }}

  /* Wordmark */
  .wordmark {{
    font-family: var(--display); font-weight: 400;
    font-size: 58px; line-height: 0.95; letter-spacing: -0.02em;
    color: #fff !important; margin: 0 0 32px 0;
    text-shadow: 0 2px 16px rgba(0,0,0,0.3);
  }}
  .wordmark em {{ font-style: italic; color: #F6C08A !important; }}

  /* Input label */
  .stTextInput > label,
  .stTextInput label p {{
    font-size: 11px !important; letter-spacing: 0.16em !important;
    text-transform: uppercase !important; font-weight: 600 !important;
    margin-bottom: 4px !important;
    color: rgba(255,255,255,0.6) !important;
  }}
  .stTextInput > div > div {{
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    transition: border-color 0.2s ease;
  }}
  .stTextInput > div > div:focus-within {{
    border-bottom-color: #F6C08A !important;
  }}
  .stTextInput input {{
    font-family: var(--body) !important;
    font-size: 15px !important;
    color: #fff !important;
    background: transparent !important;
    padding: 10px 0 12px !important;
    letter-spacing: 0.08em;
    caret-color: #F6C08A !important;
    -webkit-text-fill-color: #fff !important;
  }}
  .stTextInput input::placeholder {{ color: rgba(255,255,255,0.35) !important; letter-spacing: 0.3em; }}
  .stTextInput input:-webkit-autofill,
  .stTextInput input:-webkit-autofill:focus {{
    -webkit-text-fill-color: #fff !important;
    -webkit-box-shadow: 0 0 0 1000px rgba(10,22,40,0.01) inset !important;
  }}
  .stTextInput button svg {{
    color: rgba(255,255,255,0.6) !important;
    fill: rgba(255,255,255,0.6) !important;
  }}

  /* Checkbox */
  .stCheckbox label, .stCheckbox label p {{
    font-size: 12.5px !important;
    color: rgba(255,255,255,0.82) !important;
    font-family: var(--body) !important;
  }}
  .stCheckbox [data-testid="stCheckbox"] > label > div:first-child {{
    border: 1px solid rgba(255,255,255,0.4) !important;
    border-radius: 0 !important;
    background: transparent !important;
  }}
  .stCheckbox input:checked + div,
  .stCheckbox [aria-checked="true"] {{
    background-color: #E89547 !important;
    border-color: #E89547 !important;
  }}

  /* Submit button — 앰버 솔리드 */
  .stButton > button,
  .stFormSubmitButton > button,
  [data-testid="stBaseButton-secondaryFormSubmit"],
  [data-testid="stFormSubmitButton"] button {{
    width: 100% !important;
    background: #E89547 !important;
    color: #0A1628 !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 17px 22px !important;
    font-family: var(--body) !important;
    font-size: 12.5px !important; font-weight: 700 !important;
    letter-spacing: 0.22em !important; text-transform: uppercase !important;
    box-shadow: 0 8px 24px rgba(232,149,71,0.25) !important;
    transition: all 0.2s;
    margin-top: 12px;
  }}
  .stButton > button:hover,
  .stFormSubmitButton > button:hover {{
    background: #F6C08A !important;
    color: #0A1628 !important;
    transform: translateY(-1px);
    box-shadow: 0 12px 32px rgba(232,149,71,0.35) !important;
  }}

  /* Error alert */
  .stAlert {{
    background: rgba(0,0,0,0.35) !important;
    border: 1px solid rgba(255,100,80,0.5) !important;
    border-radius: 0 !important; color: #ffb3a7 !important;
    font-size: 13px !important; margin-top: 12px !important;
  }}

  /* Footer */
  .card-foot {{
    margin-top: 28px; padding-top: 14px;
    border-top: 1px solid rgba(255,255,255,0.12) !important;
    display: flex; justify-content: space-between;
    font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase;
    color: rgba(255,255,255,0.5) !important;
  }}

  /* Mobile */
  @media (max-width: 768px) {{
    /* base 규칙(width:440px; margin-left:80px)과 동일한 selector 우선순위로 확실히 덮어쓰기 */
    .main .block-container,
    section.main > div.block-container,
    [data-testid="stMain"] .block-container,
    [data-testid="stMainBlockContainer"],
    .stMainBlockContainer,
    div[class*="block-container"] {{
      width: auto !important;
      max-width: calc(100% - 32px) !important;
      margin-left: 16px !important;
      margin-right: 16px !important;
      margin-top: 12vh !important;
      padding: 30px 22px !important;
    }}
    [data-testid="stForm"], div[data-testid="stForm"],
    .stTextInput, .stButton, .stFormSubmitButton, .stCheckbox {{ max-width: 100% !important; }}
    .overlay-brand {{ top: 16px; left: 16px; right: 16px; font-size: 9px; letter-spacing: 0.10em; gap: 8px; }}
    .overlay-brand .mark {{ width: 18px; height: 18px; }}
    .overlay-meta, .overlay-caption {{ display: none !important; }}
  }}
</style>
""",
        unsafe_allow_html=True,
    )

    # ── 배경 위 오버레이 (고정 레이어) ───────────────────────────
    _now_kst  = datetime.now(ZoneInfo("Asia/Seoul"))
    _time_str = _now_kst.strftime("%I : %M %p").lstrip("0")

    st.markdown(
        f"""
<div class="overlay-brand">
  <div class="mark"></div>
  <span>POSCO INTERNATIONAL &nbsp;·&nbsp; Communications</span>
</div>

<div class="overlay-meta">
  Songdo HQ<br>{_time_str} KST
</div>
""",
        unsafe_allow_html=True,
    )

    # ── 카드 콘텐츠 (폼 위 텍스트) ──────────────────────────────
    st.markdown(
        """
<h1 class="wordmark">P<em>·</em>IRIS</h1>
""",
        unsafe_allow_html=True,
    )

    # ── 로그인 폼 ────────────────────────────────────────────────
    with st.form("piris_login", clear_on_submit=False, border=False):
        code_input = st.text_input(
            "비밀번호 / Password",
            type="password",
            placeholder="••••••••••",
            label_visibility="visible",
        )
        remember = st.checkbox("이 기기 기억하기", value=True)
        submitted = st.form_submit_button("Sign in to P-IRIS", use_container_width=True)

    # ── 카드 하단 ────────────────────────────────────────────────
    st.markdown(
        """
<div class="card-foot">
  <span>Feb 2026 Release</span>
  <span>© POSCO International</span>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── 인증 처리 ────────────────────────────────────────────────
    if submitted:
        # 단일 헬퍼로 조회 — secrets/.env 어느 쪽에 설정돼 있어도 동작
        _pw_pr = _resolve_password("pr")
        _pw_general = _resolve_password("general")
        def _enter_app(role: str):
            """로그인 성공 처리 — 행업 방지 + 쿠키 flush 보장.
            즉시 st.rerun()을 부르면 쿠키 컴포넌트가 브라우저에 전달되기 전에
            런이 끊겨 '기기 기억하기'가 저장되지 않는다. 대신 짧은 자동 리프레시로
            무조건 다음 런 진입을 보장한다 (쿠키 컴포넌트의 자체 리런이 오면 더 빨리 진입)."""
            st.session_state.authenticated = True
            st.session_state["role"] = role
            st.session_state.pop("_logout_requested", None)
            if remember:
                set_auth_cookie(role)
                try:
                    st_autorefresh(interval=1200, key="_login_enter_refresh", limit=3)
                except Exception:
                    st.rerun()
            else:
                st.rerun()

        if _pw_pr and code_input == _pw_pr:
            _enter_app("pr")
        elif _pw_general and code_input == _pw_general:
            _enter_app("general")
        else:
            st.error("비밀번호가 올바르지 않습니다.")

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
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            return pd.read_csv(path, encoding="utf-8")
        except Exception:
            return pd.DataFrame()
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

@st.cache_resource(show_spinner=False)
def _get_data_llm():
    """DataBasedLLM 인스턴스 (데이터/서비스 재초기화 비용이 커 캐시)."""
    return DataBasedLLM(model="gpt-4o")

def generate_issue_report(media_name, reporter_name, issue_description):
    try:
        data_llm = _get_data_llm()
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


def _post_with_retry(url, *, headers, json_body, timeout=25, max_retries=2):
    """LLM REST 호출 공용 재시도 래퍼.
    429·5xx·타임아웃·연결오류에 한해 지수 백오프(1s→3s) 재시도 — 정상 경로 비용 증가 0.
    성공 시 (json, None), 실패 시 (None, err)."""
    delays = [1, 3][:max_retries]
    last_err = None
    for attempt in range(len(delays) + 1):
        r = None
        try:
            r = requests.post(url, headers=headers, json=json_body, timeout=timeout)
            if r.status_code == 429 or r.status_code >= 500:
                last_err = f"HTTP {r.status_code}"
            else:
                r.raise_for_status()
                return r.json(), None
        except (requests.Timeout, requests.ConnectionError) as e:
            last_err = str(e)
        except Exception as e:
            # 4xx 등 재시도 무의미한 오류는 즉시 반환
            return None, str(e)
        finally:
            if r is not None:
                r.close()
        if attempt < len(delays):
            time.sleep(delays[attempt])
    return None, last_err


def _openai_chat(messages, model=None, temperature=0.2, max_tokens=400):
    """경량 OpenAI Chat 호출 (재시도·백오프 포함)"""
    api_key = _get_openai_key()
    if not api_key:
        return None, "OPENAI_API_KEY not set"
    model = model or os.getenv("OPENAI_GPT_MODEL", "gpt-4o-mini")
    data, err = _post_with_retry(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json_body={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "n": 1},
    )
    if err:
        return None, err
    try:
        return data["choices"][0]["message"]["content"].strip(), None
    except Exception as e:
        return None, str(e)

# --- 무료 LLM: Google Gemini REST 호출 (기사 요약 전용) ---
def _get_gemini_key():
    """Gemini API 키 (무료). .env 또는 Streamlit secrets에서 로드."""
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    if not key:
        try:
            key = st.secrets.get("GEMINI_API_KEY", "") or st.secrets.get("GOOGLE_API_KEY", "")
        except Exception:
            pass
    return key.strip()


def _gemini_chat(system_prompt, user_prompt, temperature=0.25, max_tokens=2048):
    """Google Gemini 호출 (무료 티어, 재시도·백오프 포함). 성공 시 (text, None), 실패 시 (None, err)."""
    api_key = _get_gemini_key()
    if not api_key:
        return None, "GEMINI_API_KEY not set"
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    data, err = _post_with_retry(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        json_body={
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        },
    )
    if err:
        return None, err
    try:
        cand = (data.get("candidates") or [{}])[0]
        parts = (cand.get("content") or {}).get("parts") or []
        text = "".join(p.get("text", "") for p in parts).strip()
        return (text, None) if text else (None, "empty response")
    except Exception as e:
        return None, str(e)

# --- 기사 본문/제목 추출 (가벼운 크롤러, 연결 누수 방지) ---
def _extract_article_text_and_title(url: str):
    """기사 크롤링 (연결 누수 방지)"""
    html = ""
    resp = None
    try:
        resp = requests.get(url, timeout=12, headers={
            # 완전한 데스크톱 UA 사용: 네이버 등은 짧은 UA에 JS 셸만 반환해 본문 추출이 실패함
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        })
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
        # 제목 끝의 매체명 suffix 제거 (예: "...본업 경쟁력' | 아주경제")
        if title:
            title = re.split(r"\s*[|<]\s*", title)[0].strip() or title

        # 본문 (네이버 모바일/데스크톱 우선 → 일반 CMS → article/p → 전체 텍스트)
        candidates = ["#dic_area", "#newsct_article", "#articeBody", "#articleBodyContents",
                      "#article-view-content-div", "article", "div#newsEndContents",
                      "div#content", "div.article_body"]
        node = None
        for sel in candidates:
            node = soup.select_one(sel)
            if node: break
        if node:
            # 단락(p) 우선. 단 본문이 <p>로 안 감싸인 사이트(네이버 #dic_area 등)는
            # p 조인 결과가 거의 비므로 노드 전체 텍스트를 사용한다.
            joined = " ".join(p.get_text(" ", strip=True) for p in node.find_all("p"))
            node_text = node.get_text(" ", strip=True)
            text = joined if len(joined) >= len(node_text) * 0.6 else node_text
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

def _format_report(llm_text: str, media: str, title: str, url: str) -> str:
    """LLM이 만든 '도입부 + 불릿'에 매체:제목 헤더와 URL을 코드로 조립한다.
    매체명·제목·URL은 확정값이므로 LLM 출력에서 무시하고 정확히 삽입 → 오기/변형/누락 차단."""
    if not llm_text:
        return ""
    intro_parts, bullets = [], []
    seen_bullet = False
    for raw_line in llm_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line[0] in "-•·*▪◦":
            seen_bullet = True
            b = line.lstrip("-•·*▪◦ ").strip().rstrip(" .")  # 끝 마침표 제거(개조식)
            if b and not b.lower().startswith("http"):
                bullets.append(b)
        elif not seen_bullet:
            # 도입부 후보. 모델이 실수로 넣은 URL/'매체 : 제목' 헤더 라인은 제외.
            if line.lower().startswith("http"):
                continue
            if " : " in line and (title[:10] in line or line.startswith(media)):
                continue
            intro_parts.append(line)
    if not bullets:
        return ""
    intro = " ".join(intro_parts).strip()
    body = "\n\n".join(f"- {b}" for b in bullets[:12])
    segments = ([intro] if intro else []) + [f"{media} : {title}", body, url]
    return "\n\n".join(segments)

# --- 링크를 직접 읽어 GPT로 '카톡 보고 메시지' 생성 (개선 버전) ---
def make_kakao_report_from_url(url: str, fallback_media="", fallback_title="", fallback_summary=""):
    media = fallback_media or _publisher_from_link(url)
    title, body = _extract_article_text_and_title(url)
    title = title or fallback_title or "제목 미확인"

    # 기사 본문 (무료 Gemini는 컨텍스트가 넉넉 → 본문을 충분히 전달해 사실 누락 최소화)
    article_text = (body or fallback_summary or "").strip()
    if len(article_text) > 6000:
        article_text = article_text[:6000]
    if not article_text:
        article_text = _build_evidence_pack(fallback_summary or "", max_sentences=20)

    # 매체명·제목·URL은 확정값이라 LLM에 맡기지 않고 코드가 조립(_format_report)한다.
    # LLM은 '도입부 1문장 + 핵심 불릿'만 생성 → 매체/제목 오기·제목 변형·URL 누락 원천 차단.
    sys_prompt = """너는 포스코인터내셔널 홍보그룹의 '언론 모니터링 보고문 작성기'다.
기사 1건을 받아 '도입부 1문장'과 '핵심 사실 불릿'만 작성한다.
매체명·기사제목·URL은 시스템이 자동으로 넣으므로 너는 절대 출력하지 마라.

[출력 — 정확히 이 두 가지만]
1) 첫 줄: 도입부 1문장. 기사 내용이 무엇이며 포스코그룹과 어떤 관련이 있는지 밝히고
   "~ 관련 기사가 게재되어 보고 드립니다." / "~ 보도가 있어 공유드립니다." / "~ 보도입니다." 로 끝맺는다.
2) 빈 줄 1개 뒤, 핵심 사실 불릿. 불릿 개수는 적게 유지하되(보통 3~6개) 각 불릿에 관련 사실을 최대한 꼼꼼히 묶어 담는다. 각 줄은 "- "로 시작하며 불릿 사이에 빈 줄 1개를 둔다.
※ 매체명/제목 헤더, URL, 기자명은 출력 금지.

[불릿 작성 — 가장 중요]
- 완전성 유지: 기사에 나오는 구체적 사실을 하나도 빠뜨리지 않는다. 등장하는 기업·종목·인물·기관명, 날짜·금액·증감률·비중·순위 등 모든 수치, 그리고 배경·원인·결과를 반드시 보존한다. 여러 항목을 "등"으로 뭉뚱그려 생략하지 말고 실제 이름을 나열한다.
- 밀도 최우선 — 불릿을 늘리지 말고 한 불릿에 꼼꼼히 묶어라: 같은 주제(예: 매수 종목군과 그 사유 / 매도 종목군과 그 사유 / 한 인물의 이력·경력 / 한 사안의 배경·경위)는 여러 불릿으로 쪼개지 말고 반드시 한 불릿에 통합한다. 한 불릿은 대략 150~300자로, 누가·언제·무엇을·수치·배경·경위·인과를 한데 엮어 충실히 작성한다.
- 짧고 헐거운 단편(한 줄에 사실 1개)은 금지한다. 이력·경위·나열 항목은 토막내지 말고 한 줄에 연결한다.
  (나쁜 예: "청와대 행정관 역임함" / "KT에서 전무 역임함" 으로 쪼갬)
  (좋은 예: "청와대 행정관을 거쳐 한국통신프리텔·KT 대외협력실장 전무, 한화그룹 부사장을 역임했으며 2021년 포스코 커뮤니케이션본부장 부사장으로 임명됨" 으로 응축)
- 기사의 리드와 핵심 경위·배경·이력·수치를 빠짐없이 담되, 비슷한 사실은 한 불릿으로 묶어 불릿 수를 늘리지 않는다. 부차적·홍보성 수식만 생략한다.
- 기사 흐름 순서대로. 사실 간 중복은 피한다. 추측·해석·이모지 금지.

[문체 — 개조식 보고체]
- 모든 불릿은 명사형 종결: ~함 / ~음 / ~임 / ~밝힘 / ~전해짐 / ~알려짐 / ~기록함 / ~보임 / ~전망 등 (불릿 끝에 마침표 없음)

[연관성 판단 — 도입부 작성용 참고]
포스코인터내셔널 사업: 미얀마 가스전·LNG 터미널/트레이딩, 삼척블루파워, 구동모터코아(포스코모빌리티솔루션),
식량/곡물 트레이딩·팜오일, 종합상사 트레이딩, DAEWOO 가전 글로벌 라이선스.
그룹/관계사: 포스코홀딩스·포스코·포스코이앤씨(건설)·포스코퓨처엠 등. 경쟁군: 철강사·종합상사.
→ 기사가 위 사업/그룹사/경쟁사/전현직 임원과 닿으면 그 연결고리를 도입부에 명시한다.
   직접 관련이 약하면 무리하게 엮지 말고 사실 관계만 간결히 밝힌다.

[좋은 예시 1 — 인물/인사]
오석근 전 포스코 부사장(커뮤니케이션팀장)의 부산시 경제부시장 내정 관련 기사가 게재되어 보고 드립니다.

- 전재수 부산시장 당선인 측은 30일 민선 9기 첫 경제부시장에 오석근 전 포스코 부사장을 내정했다고 밝힘

- 오 내정자(1961년생)는 김영삼 정부 시절 청와대 행정관을 거쳐 한국통신프리텔·KT 대외협력실장 전무, 한화그룹 커뮤니케이션위원회 부사장을 역임했으며, 2021년 포스코 커뮤니케이션본부장 부사장으로 임명돼 대외 소통을 총괄한 바 있음

- 부산시는 정무적 감각과 경제 전반의 전문성을 동시에 갖춘 인물을 물색한 끝에 오 전 부사장을 최종 낙점한 것으로 알려짐

- 전 당선인은 앞서 하정우 전 청와대 AI미래기획수석비서관에게 경제부시장직을 간접 제안했으나 응답이 없어 오 전 부사장으로 선회한 것으로 전해짐

[좋은 예시 2 — 기업/산업 동향]
세아그룹 두 지주사가 본업 경쟁력에 따라 1분기 실적 희비가 갈렸다는 철강업계 분석으로, 종합상사·철강 경쟁 동향 차원에서 공유드립니다.

- 29일 업계에 따르면 올해 1분기 세아그룹 두 지주사의 실적은 뚜렷한 온도차를 보임

- 세아베스틸지주는 연결 기준 매출 9676억원·영업이익 307억원으로 전년 동기 대비 매출 7.5%, 영업이익 69.8% 증가한 반면, 세아제강지주는 매출 9919억원으로 4.7% 늘었으나 영업이익은 267억원으로 60.1% 감소함

- 세아베스틸은 자동차용 특수강에 머물지 않고 방산·원전·항공우주 등 고부가가치 시장으로 영역을 확대하며 안정적 수익 기반을 구축함

- 반면 세아제강은 북미 에너지용 강관(OCTG) 중심 사업 구조가 미국 관세 정책·통상 환경 변화, 글로벌 에너지 투자 둔화 등 대외 변수에 발목을 잡힘

위 두 예시처럼 한 불릿에 관련 사실을 충실히 응축하고, 매체명·제목·URL은 출력하지 않는다."""

    user_prompt = f"""[기사 정보]
매체명: {media}
제목: {title}

[기사 본문]
{article_text}

위 기사로 '도입부 1문장 + 핵심 불릿(보통 3~6개)'만 작성하라.
불릿 수는 적게 유지하되 관련 사실을 한 불릿에 묶어 각 150~300자로 꼼꼼히 담고, 종목·인물·기관명과 수치는 누락하지 마라.
매체명·제목·URL은 절대 쓰지 마라 (시스템이 자동 삽입)."""

    # 품질 우선: gpt-4o로 요약 생성(on-demand 버튼이라 호출량이 적어 비용 부담 작음).
    # OpenAI 실패/미설정 시에만 무료 Gemini로 폴백.
    out, _ = _openai_chat(
        [{"role": "system", "content": sys_prompt},
         {"role": "user", "content": user_prompt}],
        model="gpt-4o", temperature=0.2, max_tokens=2800,
    )
    if not out and _get_gemini_key():
        out, _ = _gemini_chat(sys_prompt, user_prompt, temperature=0.25, max_tokens=2800)

    report = _format_report(out, media, title, url) if out else ""
    if report:
        return report

    # LLM 실패/파싱 실패 시 백업 (도입부 없이 매체:제목 / 불릿 / URL)
    bullets = _short_bullets(article_text or fallback_summary, 5, 80)
    if len(bullets) < 2:
        bullets = ["기사 핵심 내용 확인 필요", "상세 내용은 원문 기사 참고"]
    bullets_formatted = "\n\n".join(f"- {b}" for b in bullets[:6])
    return f"{media} : {title}\n\n{bullets_formatted}\n\n{url}"

# --- 카운트다운 전용 프래그먼트(지원 시) + 폴백 ---
def _countdown_badge_html(secs_left: int) -> str:
    return f"""
    <div style="
        display:flex; align-items:center; justify-content:center;
        height:38px; box-sizing:border-box;
        background:rgba(200,146,10,0.20);
        border:1px solid rgba(200,146,10,0.35);
        border-radius:8px;
        color:#e8b84b; font-weight:700; font-size:0.82rem;
        width:100%; white-space:nowrap;">
        ⏱ {secs_left}s
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


@st.cache_data(ttl=180, show_spinner=False)  # 3분 캐싱 (auto-refresh 주기와 동일)
def crawl_all_news_sources(query: str, max_items: int = 200, sort: str = "date") -> pd.DataFrame:
    """
    Naver + Google News RSS 통합 수집 (캐싱 적용)

    Args:
        query: 검색 쿼리
        max_items: Naver API 최대 수집 개수
        sort: 정렬 방식

    Returns:
        병합된 DataFrame (URL 기준 dedupe, 최신순 정렬)
    """
    print(f"[DEBUG] crawl_all_news_sources called for query: {query}")

    # Naver 뉴스 수집
    naver_df = crawl_naver_news(query, max_items=max_items, sort=sort)

    # Google News RSS 수집 (POSCO International 키워드일 때만)
    google_df = pd.DataFrame()
    if "posco" in query.lower() and "international" in query.lower():
        try:
            print(f"[DEBUG] Fetching Google News RSS for: {query}")
            google_df = crawl_google_news_rss(query="POSCO International", max_items=50)
        except Exception as e:
            print(f"[WARNING] Google News RSS failed: {e}")
            google_df = pd.DataFrame()

    # 두 소스 병합
    merged_df = merge_news_sources(naver_df, google_df)

    # API 할당량 초과 정보 전달
    if naver_df.attrs.get('quota_exceeded', False):
        merged_df.attrs['quota_exceeded'] = True

    print(f"[DEBUG] Total items after merge: {len(merged_df)} (Naver: {len(naver_df)}, Google: {len(google_df)})")

    return merged_df


def load_news_db(force_refresh: bool = False) -> pd.DataFrame:
    """뉴스 DB 로드

    로드 우선순위:
      1. 로컬 파일 (save_news_db로 저장된 최신 수집 결과)
      2. GitHub raw URL (로컬 파일 없거나 실패 시 폴백)

    Args:
        force_refresh: True면 로컬 파일 캐시를 무시하고 GitHub에서 강제 로드
    """
    GITHUB_RAW_URL = "https://raw.githubusercontent.com/kimwoss/Risk_management/main/data/news_monitor.csv"

    def _read_local() -> pd.DataFrame | None:
        """로컬 파일 읽기. 없거나 실패 시 None 반환."""
        try:
            if not os.path.exists(NEWS_DB_FILE):
                return None
            df = pd.read_csv(NEWS_DB_FILE, encoding="utf-8")
            if "sentiment" not in df.columns:
                df["sentiment"] = "pos"
            if not df.empty and "날짜" in df.columns:
                latest_date = df["날짜"].iloc[0]
                print(f"[DEBUG] ✅ 로컬 파일 로드: {len(df)}건, 최신: {latest_date}")
            return df
        except Exception as e:
            print(f"[WARNING] 로컬 파일 로드 실패: {e}")
            return None

    def _read_github() -> pd.DataFrame | None:
        """GitHub raw URL에서 읽기. 실패 시 None 반환."""
        try:
            cache_buster = int(time.time()) if force_refresh else int(time.time() // 30)
            url = f"{GITHUB_RAW_URL}?t={cache_buster}"
            print(f"[DEBUG] GitHub 폴백 로드: {url}")
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            from io import StringIO
            df = pd.read_csv(StringIO(resp.text), encoding="utf-8")
            resp.close()
            if "sentiment" not in df.columns:
                df["sentiment"] = "pos"
            if not df.empty and "날짜" in df.columns:
                print(f"[DEBUG] ✅ GitHub 로드: {len(df)}건, 최신: {df['날짜'].iloc[0]}")
            return df
        except Exception as e:
            print(f"[WARNING] GitHub 로드 실패: {e}")
            return None

    # force_refresh: GitHub 강제 로드 후 로컬 저장
    if force_refresh:
        df = _read_github()
        if df is None:
            df = _read_local()
    else:
        # 로컬 우선 → GitHub 폴백
        df = _read_local()
        if df is None:
            df = _read_github()

    if df is not None:
        return df

    print("[ERROR] 모든 로드 시도 실패")
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
def _prep_contact_links(df: pd.DataFrame, phone_cols=(), email_cols=()):
    """연락처/이메일 컬럼을 tel:/mailto: 링크로 변환 → 원클릭 전화·메일.
    반환: (표시용 df, column_config). 원본 df는 변경하지 않는다."""
    display_df = df.copy()
    col_config = {}
    for c in phone_cols:
        if c in display_df.columns:
            display_df[c] = display_df[c].astype(str).map(
                lambda v: f"tel:{v.strip()}" if re.search(r"\d{3,}", v or "") else ""
            )
            col_config[c] = st.column_config.LinkColumn(
                f"📞 {c}", display_text=r"tel:(.*)", help="클릭하면 바로 전화 연결"
            )
    for c in email_cols:
        if c in display_df.columns:
            display_df[c] = display_df[c].astype(str).map(
                lambda v: f"mailto:{v.strip()}" if "@" in (v or "") else ""
            )
            col_config[c] = st.column_config.LinkColumn(
                f"✉️ {c}", display_text=r"mailto:(.*)", help="클릭하면 메일 작성"
            )
    return display_df, col_config


def show_table(df: pd.DataFrame, label: str, csv_name: str = None,
               phone_cols=(), email_cols=()):
    """공용 테이블 렌더 + 선택적 CSV 내보내기(utf-8-sig, 엑셀 호환) + tel/mailto 링크"""
    if label:
        st.markdown(f"#### {label}")
    display_df, col_config = _prep_contact_links(df, phone_cols, email_cols)
    st.dataframe(
        display_df, use_container_width=True,
        height=min(560, 44 + min(len(df), 12) * 38),
        column_config=col_config or None,
    )
    if csv_name:
        st.download_button(
            "⬇ 엑셀용 CSV 다운로드",
            df.to_csv(index=False).encode("utf-8-sig"),
            file_name=csv_name, mime="text/csv",
            key=f"csv_dl_{csv_name}",
        )

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

            # 감성 분석으로 이모지 결정 (🟢 긍정/중립, 🔴 부정)
            summary = article.get("summary", "")
            sentiment = article.get("sentiment") or get_article_sentiment(title, summary, link)
            emoji = "🔴" if sentiment == "neg" else "🟢"

            message = f"{emoji} *새 뉴스*\n\n"

            # 검색 키워드 해시태그 추가
            if keyword:
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

        # 전송 결과를 파일에 저장 (GitHub Actions와 중복 발송 방지)
        if success_count > 0:
            try:
                save_sent_cache(_sent_articles_cache)
                print(f"[DEBUG] 💾 전송 캐시 파일 저장 완료")
            except Exception as save_err:
                print(f"[DEBUG] ⚠️ 캐시 파일 저장 실패 (무시): {save_err}")

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

                # sentiment 필드 포함 (있으면 재사용, 없으면 빈값으로 send_telegram에서 분석)
                sentiment = str(row.get("sentiment", "")).strip()

                new_articles.append({
                    "title": title if title and title != "nan" else "제목 없음",
                    "link": url,
                    "date": article_date_str,
                    "press": press,
                    "keyword": keyword,
                    "summary": str(row.get("주요기사 요약", "")).strip(),
                    "sentiment": sentiment,
                })

        print(f"[DEBUG] 총 {len(new_articles)}건의 신규 기사 감지 (최근 6시간 이내)")
        return new_articles

    except Exception as e:
        print(f"[DEBUG] 신규 기사 감지 오류: {str(e)}")
        import traceback
        print(f"[DEBUG] 상세 오류:\n{traceback.format_exc()}")
        return []

# 전송된 기사 URL 추적 (파일 기반 초기화 + 메모리 캐시, 최근 1000개)
_sent_articles_cache = load_sent_cache()  # GitHub Actions가 저장한 캐시 파일에서 로드
_sent_articles_lock = threading.Lock()
_MAX_SENT_CACHE = 1000

# ----------------------------- 스타일 -----------------------------
# CSS 캐시 비활성화 - 즉시 반영
@st.cache_data(ttl=0)
def load_base_css():
    st.markdown("""
    <style>
      /* @import는 CSS 스펙상 다른 규칙보다 앞서야 로드됨 — 반드시 최상단 유지 */
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700&display=swap');

      /* ── 글로벌 디자인 토큰 (다크 = 기본) ────────────────────
         라이트/다크 전환은 html[data-theme] 속성 + 아래 변수 오버라이드만으로 처리.
         새 색이 필요하면 하드코딩하지 말고 토큰을 추가할 것. */
      :root {
        --c-bg:        #0a0b0d;
        --c-bg-2:      #0c0d10;
        --c-surface:   rgba(255,255,255,0.04);
        --c-surface-h: rgba(255,255,255,0.07);
        --c-border:    rgba(255,255,255,0.08);
        --c-panel:          #1E1E1E;   /* 뉴스 카드 등 솔리드 패널 */
        --c-panel-h:        #252525;
        --c-panel-border:   #2A2A2A;
        --c-panel-border-h: #3A3A3A;
        --c-card-bg1:  rgba(24,24,28,.65);
        --c-card-bg2:  rgba(16,16,20,.85);
        --c-dash-bg1:  rgba(26,26,46,0.88);
        --c-dash-bg2:  rgba(22,33,62,0.82);
        --c-nav-bg:    rgba(10,11,13,0.55);
        --c-btn-bg1:   #2a2b2f;
        --c-btn-bg2:   #1a1b1f;
        /* 골드 토큰 단일화: 전 화면이 아래 3단조만 참조 (#E89547/#c4a52e 등 개별 골드 금지) */
        --c-gold:      #D4AF37;
        --c-gold-deep: #b09530;
        --c-gold-dark: #8e771a;
        --c-gold-dim:  rgba(212,175,55,0.12);
        --c-gold-glow: rgba(212,175,55,0.20);
        --c-gold-border: rgba(212,175,55,0.45);
        --c-on-gold:   #f0e8c8;
        --c-pos:       #22c55e;
        --c-neg:       #ef4444;
        --c-warn:      #f59e0b;
        --c-info:      #6366f1;
        --c-blue:      #3b82f6;
        --c-teal:      #06b6d4;
        --c-pink:      #ec4899;
        --c-purple:    #8b5cf6;
        --c-orange:    #f97316;
        --c-emerald:   #10b981;
        --c-amber:     #c8920a;
        --c-text:        #e8e8e8;
        --c-text-strong: #ffffff;
        /* WCAG AA: 보조 텍스트 대비 상향 (dim ≥ 0.62, 정보 텍스트 ≥ 0.5) */
        --c-text-dim:  rgba(255,255,255,0.62);
        --c-text-mute: rgba(255,255,255,0.50);
        --c-hr:        rgba(255,255,255,0.07);
        --r-sm: 8px;  --r-md: 12px;  --r-lg: 16px;
        --shadow-card: 0 4px 20px rgba(0,0,0,0.25), 0 1px 0 rgba(255,255,255,0.05) inset;
        --shadow-card-h: 0 8px 28px rgba(0,0,0,0.35);
      }

      /* ── 라이트 테마 오버라이드 (◐ 토글 → html[data-theme='light']) ── */
      html[data-theme='light'] {
        --c-bg:        #f7f8fa;
        --c-bg-2:      #fdfdfe;
        --c-surface:   rgba(15,23,42,0.045);
        --c-surface-h: rgba(15,23,42,0.08);
        --c-border:    rgba(15,23,42,0.12);
        --c-panel:          #ffffff;
        --c-panel-h:        #f3f4f7;
        --c-panel-border:   #e2e5ea;
        --c-panel-border-h: #c9ced7;
        --c-card-bg1:  rgba(255,255,255,0.92);
        --c-card-bg2:  rgba(248,249,251,0.97);
        --c-dash-bg1:  rgba(255,255,255,0.95);
        --c-dash-bg2:  rgba(243,245,250,0.92);
        --c-nav-bg:    rgba(255,255,255,0.78);
        --c-btn-bg1:   #ffffff;
        --c-btn-bg2:   #eef0f3;
        /* 흰 배경 대비를 위해 라이트에선 골드를 어둡게 */
        --c-gold:      #9c7c1e;
        --c-gold-deep: #8a6d1b;
        --c-gold-dark: #6f5713;
        --c-gold-dim:  rgba(156,124,30,0.12);
        --c-gold-glow: rgba(156,124,30,0.18);
        --c-gold-border: rgba(156,124,30,0.45);
        --c-on-gold:   #fffdf2;
        --c-text:        #1a1c1f;
        --c-text-strong: #000000;
        --c-text-dim:  rgba(0,0,0,0.62);
        --c-text-mute: rgba(0,0,0,0.50);
        --c-hr:        rgba(0,0,0,0.08);
        --shadow-card: 0 4px 20px rgba(15,23,42,0.08), 0 1px 0 rgba(255,255,255,0.6) inset;
        --shadow-card-h: 0 8px 28px rgba(15,23,42,0.14);
      }

      /* ── 통합 대시보드 컨테이너 ─────────────────────────── */
      .iris-dash {
        background: linear-gradient(145deg, var(--c-dash-bg1) 0%, var(--c-dash-bg2) 100%);
        border: 1px solid var(--c-border);
        border-radius: var(--r-lg);
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.28);
        backdrop-filter: blur(8px);
      }
      .iris-dash * { text-align: center; }
      .iris-dash div[data-testid="column"] { padding: 0 6px !important; }
      @media (max-width: 768px) {
        .iris-dash div[data-testid="column"] { flex: 1 1 calc(33.333% - 12px) !important; min-width: 96px !important; }
      }
      @media (max-width: 480px) {
        .iris-dash div[data-testid="column"] { flex: 1 1 calc(50% - 12px) !important; }
      }

      /* ── 통합 스탯 카드 ──────────────────────────────────── */
      .iris-card {
        background: var(--c-surface);
        border-radius: var(--r-md);
        padding: 16px 12px;
        border-left: 3px solid var(--c-border);
        transition: background 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
        min-height: 120px;
        display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        text-align: center;
      }
      .iris-card:hover {
        background: var(--c-surface-h);
        transform: translateY(-2px);
        box-shadow: var(--shadow-card-h);
      }
      /* 카드 색상 변형 */
      .iris-card.ic-total   { border-left-color: var(--c-info);    background: rgba(99,102,241,0.05); }
      .iris-card.ic-pos     { border-left-color: var(--c-pos); }
      .iris-card.ic-neg     { border-left-color: var(--c-neg); }
      .iris-card.ic-warn    { border-left-color: var(--c-warn); }
      .iris-card.ic-orange  { border-left-color: var(--c-orange); }
      .iris-card.ic-blue    { border-left-color: var(--c-blue); }
      .iris-card.ic-teal    { border-left-color: var(--c-teal); }
      .iris-card.ic-pink    { border-left-color: var(--c-pink); }
      .iris-card.ic-purple  { border-left-color: var(--c-purple); }
      .iris-card.ic-emerald { border-left-color: var(--c-emerald); }
      .iris-card.ic-amber   { border-left-color: var(--c-amber); }
      /* 카드 내부 라벨 */
      .ic-label { font-size: 0.75rem; font-weight: 600; margin-bottom: 8px; color: var(--c-text-dim); }
      .iris-card.ic-total   .ic-label { color: var(--c-info); }
      .iris-card.ic-pos     .ic-label { color: var(--c-pos); }
      .iris-card.ic-neg     .ic-label { color: var(--c-neg); }
      .iris-card.ic-warn    .ic-label { color: var(--c-warn); }
      .iris-card.ic-orange  .ic-label { color: var(--c-orange); }
      .iris-card.ic-blue    .ic-label { color: var(--c-blue); }
      .iris-card.ic-teal    .ic-label { color: var(--c-teal); }
      .iris-card.ic-pink    .ic-label { color: var(--c-pink); }
      .iris-card.ic-purple  .ic-label { color: var(--c-purple); }
      .iris-card.ic-emerald .ic-label { color: var(--c-emerald); }
      .iris-card.ic-amber   .ic-label { color: var(--c-amber); }
      /* 카드 내부 숫자 */
      .ic-value { color: var(--c-text); font-size: 1.8rem; font-weight: 700; margin: 6px 0; }
      .iris-card.ic-total .ic-value { font-size: 2.4rem; color: var(--c-text-strong); }
      /* 퍼센트 */
      .ic-pct { color: var(--c-text-mute); font-size: 0.7rem; margin-top: 4px; }
      /* 감성 필 뱃지 */
      .ic-pill-row { display: flex; justify-content: center; align-items: center; gap: 6px; margin-top: 6px; }
      .ic-pill { font-size: 0.65rem; font-weight: 700; padding: 2px 7px; border-radius: 99px; letter-spacing: 0.02em; }
      .ic-pill.pos { background: rgba(34,197,94,0.14); color: var(--c-pos); border: 1px solid rgba(34,197,94,0.25); }
      .ic-pill.neg { background: rgba(239,68,68,0.12); color: var(--c-neg); border: 1px solid rgba(239,68,68,0.22); }

      /* ── 컨테이너 폭 + 상단 여백 ─────────────────────────── */
      .block-container {max-width:1360px !important; padding: 24px 20px 0 !important; margin-top: 16px !important;}

      /* 배경/폰트 (@import는 최상단으로 이동됨 — 여기 두면 브라우저가 무시함) */
      [data-testid="stAppViewContainer"]{
        background: linear-gradient(180deg, var(--c-bg-2) 0%, var(--c-bg) 100%) !important;
        color: var(--c-text); font-family:'Inter','Noto Sans KR',system-ui,Segoe UI,Roboto,Apple SD Gothic Neo,Pretendard,sans-serif;
      }
      [data-testid="stHeader"]{background:transparent; height:0;}
      section[data-testid="stSidebar"] {display:none !important;}

      /* 카드 */
      .card{
        background: linear-gradient(135deg, var(--c-card-bg1), var(--c-card-bg2));
        border: 1px solid var(--c-border);
        border-radius: 12px; padding: 24px; margin-bottom: 24px;
        box-shadow: var(--shadow-card);
        backdrop-filter: blur(10px);
      }
      .input-card{ border-color: var(--c-gold-border); }
      .result-card{ border-color: var(--c-border); }

      /* 버튼 (제네시스 톤)
         주의: help= 툴팁이 붙은 버튼은 stTooltip 래퍼로 감싸져 직계(>) 선택자가
         빗나가므로 자손 선택자를 사용한다 (◐/⏻ 버튼 다크 잔존 버그 방지) */
      .stButton button{
        border-radius:8px; font-weight:700; border:1px solid var(--c-border);
        background: linear-gradient(180deg, var(--c-btn-bg1), var(--c-btn-bg2)); color: var(--c-text);
        padding:10px 16px; letter-spacing:.01em;
      }
      /* 로고 영역 스타일 */
      .nav-container a:hover {
        opacity: 0.9;
      }
      .stButton button:hover{
        border-color: var(--c-gold-border) !important;
        background: linear-gradient(135deg, var(--c-btn-bg1), var(--c-btn-bg2)) !important;
        box-shadow: 0 4px 20px var(--c-gold-glow), 0 2px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px) !important;
        color: var(--c-text) !important;
      }
      .stButton button:disabled{
        color: var(--c-text); border-color: var(--c-border);
        background: linear-gradient(135deg, var(--c-surface-h), var(--c-surface));
      }

      /* 다운로드 버튼 특별 스타일 — 골드 토큰만 사용 */
      .stDownloadButton>button{
        background: linear-gradient(135deg, var(--c-gold-deep), var(--c-gold-dark)) !important;
        border: 1px solid var(--c-gold-border) !important;
        color: var(--c-on-gold) !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        letter-spacing: 0.01em !important;
        transition: all 0.25s ease !important;
      }
      .stDownloadButton>button:hover{
        background: linear-gradient(135deg, var(--c-gold), var(--c-gold-deep)) !important;
        border-color: var(--c-gold-border) !important;
        box-shadow: 0 4px 20px var(--c-gold-glow) !important;
        transform: translateY(-1px) !important;
        color: var(--c-on-gold) !important;
      }

      /* 데이터프레임 */
      div[data-testid="stDataFrame"]{ background: var(--c-surface) !important; border:1px solid var(--c-border); border-radius:10px; }
      div[data-testid="stDataFrame"] *{ color: var(--c-text) !important; }

      /* ── Streamlit 위젯 라벨·입력창: 테마 토큰 따르기 ──────────
         config.toml은 다크 고정(base=dark)이라 라이트 모드에서 라벨이 흰색,
         입력창이 검정으로 남는 문제를 토큰으로 보정 (다크에선 기존과 동일 톤). */
      [data-testid="stWidgetLabel"] p,
      [data-testid="stWidgetLabel"] label,
      .stTextInput > label, .stTextInput > label p,
      .stTextArea > label,  .stTextArea > label p,
      .stSelectbox > label, .stSelectbox > label p,
      div[data-testid="stRadio"] > label p,
      .stCheckbox label p {
        color: var(--c-text) !important;
      }
      .stTextInput > div > div,
      .stTextArea textarea,
      [data-testid="stNumberInput"] input,
      [data-testid="stSelectbox"] > div > div {
        background: var(--c-panel) !important;
        color: var(--c-text) !important;
        border-color: var(--c-border) !important;
      }
      .stTextInput input, .stTextArea textarea {
        color: var(--c-text) !important;
        -webkit-text-fill-color: var(--c-text) !important;
        caret-color: var(--c-gold) !important;
      }
      .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: var(--c-text-mute) !important;
        -webkit-text-fill-color: var(--c-text-mute) !important;
      }
      [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background: var(--c-panel) !important;
        color: var(--c-text) !important;
      }
      /* expander (과거 대응이력 등) */
      [data-testid="stExpander"] {
        background: var(--c-surface);
        border: 1px solid var(--c-border) !important;
        border-radius: 10px;
      }
      [data-testid="stExpander"] summary p,
      [data-testid="stExpander"] summary span {
        color: var(--c-text) !important;
      }
      /* caption */
      [data-testid="stCaptionContainer"] p { color: var(--c-text-mute) !important; }

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

      /* ── 메인 바로가기(CTA) 그리드 — 클래스 기반 반응형(iframe 제거) ── */
      .iris-cta-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px;
        margin: 10px 0 4px;
      }
      .iris-cta-card {
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-radius: 12px;
        padding: 18px 12px;
        text-align: center; text-decoration: none;
        transition: background 0.2s, border-color 0.2s, transform 0.2s;
        min-height: 118px;
      }
      .iris-cta-card:hover {
        background: var(--c-surface-h);
        border-color: var(--c-gold-border);
        transform: translateY(-3px);
        text-decoration: none;
      }
      .iris-cta-card .cta-ico { font-size: 1.7rem; margin-bottom: 8px; line-height: 1; }
      .iris-cta-card .cta-ttl { font-size: 0.92rem; font-weight: 700; color: var(--c-text); margin-bottom: 4px; word-break: keep-all; }
      .iris-cta-card .cta-dsc { font-size: 0.72rem; color: var(--c-text-mute); line-height: 1.4; word-break: keep-all; }

      /* ── 메뉴 중복 제거: 데스크톱은 '상단 내비'만 사용 → 홈 하단 CTA 그리드 숨김 ── */
      @media (min-width: 769px) {
        .iris-cta-grid { display: none !important; }
      }

      /* 모바일 최적화 (전역) */
      @media (max-width: 768px) {
        /* 가로 스크롤 차단 */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
          overflow-x: hidden !important; max-width: 100vw !important;
        }
        img, iframe { max-width: 100% !important; }

        .block-container { padding: 12px 14px 0 !important; margin-top: 8px !important; }
        .card { padding: 16px !important; border-radius: 10px !important; margin-bottom: 16px !important; }
        .main-copy { left: 24px !important; padding-right: 24px !important; }
        .stButton>button, .stDownloadButton>button { font-size: 0.9rem !important; padding: 10px 14px !important; }

        /* CTA 카드: 2열 */
        .iris-cta-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 8px !important; }
        .iris-cta-card { min-height: 104px; padding: 14px 10px; }

        /* KPI 카드 글자 축소 */
        .ic-value { font-size: 1.4rem !important; }
        .iris-card.ic-total .ic-value { font-size: 1.9rem !important; }
        .iris-card { min-height: 96px !important; padding: 12px 8px !important; }

        /* 상단 내비: 안쪽 메뉴 버튼을 2열 그리드로 (로고 줄은 위에 풀폭).
           st.container(key="iris_nav") → .st-key-iris_nav 앵커로 정확히 타깃 */
        .st-key-iris_nav div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] {
          flex-wrap: wrap !important; gap: 6px !important;
        }
        .st-key-iris_nav div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
        .st-key-iris_nav div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
          flex: 1 1 calc(50% - 3px) !important;
          min-width: calc(50% - 3px) !important;
          width: calc(50% - 3px) !important;
        }
        /* 비어 보이는 내비 래퍼 바 제거 (버튼은 별도 컨테이너에 렌더됨) */
        .nav-container:empty { display: none !important; }

        /* ── 메뉴 중복 제거: 모바일은 홈에서 '하단 CTA'만 사용 → 상단 내비 숨김 ──
           단, 홈(=CTA 그리드가 있는 페이지)에서만 숨긴다. 내부 페이지엔 CTA가 없으므로
           :has(.iris-cta-grid)가 매칭되지 않아 상단 내비가 그대로 남아 내비게이션 유지됨. */
        html:has(.iris-cta-grid) .st-key-iris_nav,
        html:has(.iris-cta-grid) .nav-container { display: none !important; }
      }

      @media (max-width: 480px) {
        .card { padding: 12px !important; border-radius: 8px !important; }
        .main-copy { left: 16px !important; padding-right: 16px !important; }
        [data-testid="stAppViewContainer"] .block-container { padding-left: 0.9rem !important; padding-right: 0.9rem !important; }
        .iris-cta-card .cta-ttl { font-size: 0.86rem; }
        .iris-cta-card .cta-dsc { font-size: 0.67rem; }
      }

      /* ── type="primary" 버튼 → gold 토큰 통일 ─────────────── */
      [data-testid="stBaseButton-primary"],
      .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, var(--c-gold-deep), var(--c-gold-dark)) !important;
        border: 1px solid var(--c-gold-border) !important;
        color: var(--c-on-gold) !important;
        font-weight: 700 !important;
      }
      [data-testid="stBaseButton-primary"]:hover,
      .stButton>button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--c-gold), var(--c-gold-deep)) !important;
        border-color: var(--c-gold-border) !important;
        box-shadow: 0 4px 20px var(--c-gold-glow) !important;
        color: var(--c-on-gold) !important;
      }

      /* ── 섹션 헤더 h3 (st.markdown "###") ───────────────── */
      [data-testid="stMarkdownContainer"] h3 {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: var(--c-text-dim) !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        margin: 28px 0 14px !important;
        padding-bottom: 8px !important;
        border-bottom: 1px solid var(--c-hr) !important;
      }

      /* ── 구분선 hr (st.markdown "---") ──────────────────── */
      hr {
        border: none !important;
        border-top: 1px solid var(--c-hr) !important;
        margin: 24px 0 !important;
      }

      /* ── 빈 상태 플레이스홀더 ──────────────────────────────── */
      .empty-state {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        min-height: 220px; text-align: center;
        color: var(--c-text-mute);
        padding: 32px 24px;
        border: 1px dashed var(--c-border);
        border-radius: var(--r-md, 12px);
      }
      .empty-state .es-icon { font-size: 2.4rem; margin-bottom: 12px; opacity: 0.5; }
      .empty-state .es-title { font-size: 0.95rem; font-weight: 600; color: var(--c-text-dim); margin-bottom: 6px; }
      .empty-state .es-desc  { font-size: 0.8rem; line-height: 1.55; }

      /* ── CTA 바로가기 카드 (메인 페이지) ─────────────────── */
      .cta-card {
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-radius: var(--r-md, 12px);
        padding: 20px 16px;
        text-align: center;
        transition: all 0.2s ease;
        cursor: pointer;
        text-decoration: none !important;
        display: block;
      }
      .cta-card:hover {
        background: var(--c-surface-h);
        border-color: var(--c-gold-border);
        transform: translateY(-3px);
        box-shadow: var(--shadow-card-h);
        text-decoration: none !important;
      }
      .cta-card .cta-icon  { font-size: 1.8rem; margin-bottom: 8px; }
      .cta-card .cta-title { font-size: 0.9rem; font-weight: 700; color: var(--c-text); margin-bottom: 4px; }
      .cta-card .cta-desc  { font-size: 0.72rem; color: var(--c-text-mute); line-height: 1.4; }
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
MENU_ITEMS = ["뉴스 모니터링", "키워드 인사이트", "이슈보고 생성", "언론사 정보", "담당자 정보", "대응이력 검색"]

def get_visible_menu():
    """역할에 따라 노출할 메뉴 목록 반환"""
    if st.session_state.get("role") == "general":
        return [m for m in MENU_ITEMS if m != "뉴스 모니터링"]
    return MENU_ITEMS

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
      /* ── 네비게이션 컨테이너 ─────────────────────────────── */
      .nav-container {
        background: var(--c-nav-bg);
        border: 1px solid var(--c-border);
        border-radius: 18px;
        padding: 12px 18px;
        margin: 8px 0 20px 0;
        box-shadow: 0 4px 24px rgba(0,0,0,0.22);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
      }

      /* ── 탭 버튼 (비활성) ─────────────────────────────────── */
      .nav-container .stButton>button {
        border-radius: 99px !important;
        font-weight: 500 !important;
        border: 1px solid transparent !important;
        background: transparent !important;
        color: var(--c-text-mute) !important;
        padding: 10px 16px !important;
        letter-spacing: 0.01em !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 44px !important;
        min-height: 44px !important;
        font-size: 0.9rem !important;
        box-shadow: none !important;
      }
      .nav-container .stButton>button:hover {
        background: var(--c-surface-h) !important;
        color: var(--c-text) !important;
        border-color: var(--c-border) !important;
        transform: none !important;
        box-shadow: none !important;
      }

      /* ── 탭 버튼 (활성 = disabled) ───────────────────────── */
      .nav-container .stButton>button:disabled {
        background: var(--c-gold-dim, rgba(212,175,55,0.12)) !important;
        color: var(--c-gold, #D4AF37) !important;
        border: 1px solid var(--c-gold-border) !important;
        box-shadow: 0 0 14px var(--c-gold-glow) !important;
        font-weight: 700 !important;
        opacity: 1 !important;
        transform: none !important;
      }

      /* ── 모바일 최적화 ───────────────────────────────────── */
      @media (max-width: 768px) {
        .nav-container .stButton>button {
          font-size: 0.72rem !important;
          padding: 8px 8px !important;
          height: auto !important;
          min-height: 40px !important;
          line-height: 1.3 !important;
          white-space: normal !important;
          word-break: keep-all !important;
        }
        .nav-container { padding: 10px 10px !important; margin: 6px 0 16px 0 !important; }
        .nav-container img { height: 34px !important; }
      }
      @media (max-width: 480px) {
        .nav-container .stButton>button {
          font-size: 0.67rem !important;
          padding: 6px 6px !important;
          min-height: 36px !important;
        }
        .nav-container { padding: 8px 8px !important; border-radius: 14px !important; }
        .nav-container img { height: 30px !important; }
      }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    with st.container(key="iris_nav"):
        c1, c2, c3 = st.columns([1.2, 3.5, 0.5], gap="medium")
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
            visible_items = get_visible_menu()
            cols = st.columns(len(visible_items))
            for i, label in enumerate(visible_items):
                with cols[i]:
                    clicked = st.button(label, key=f"nav_{label}", use_container_width=True, disabled=(label==active_label))
                    if clicked:
                        st.query_params["menu"] = label
                        st.rerun()
        with c3:
            t_col, o_col = st.columns(2, gap="small")
            with t_col:
                # ◐ 라이트/다크 테마 토글
                _theme = get_current_theme()
                if st.button("◐", key="nav_theme_toggle", use_container_width=True,
                             help="라이트/다크 테마 전환"):
                    _new_theme = "light" if _theme == "dark" else "dark"
                    set_theme(_new_theme)
                    # 주의: 여기서 st.rerun()을 부르면 쿠키 컴포넌트 flush가 끊겨
                    # 쿠키가 저장되지 않고, 리런 경합으로 토글이 이중 발화할 수 있다.
                    # data-theme은 CSS 변수 기반이라 속성 재주입만으로 즉시 전환된다.
                    apply_theme_attribute(_new_theme)
            with o_col:
                # ⏻ 로그아웃 (공용 PC·모바일 이탈 경로)
                if st.button("⏻", key="nav_logout", use_container_width=True,
                             help="로그아웃"):
                    logout()
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
          height:auto; min-height:360px; margin:12px 0;
          background:
            linear-gradient(180deg, rgba(0,0,0,.72) 0%, rgba(0,0,0,.35) 60%),
            url('{bg_uri}') center 62% / cover no-repeat, #000;
        }}
      }}
      .main-copy {{ position:absolute; left:48px; top:50%; transform:translateY(-50%); color:#fff; max-width:720px; text-shadow:0 4px 20px rgba(0,0,0,.45); }}
      .t {{ font-size:3.2rem; line-height:1.15; font-weight:300; margin:0 0 8px; letter-spacing:-.02em; }}
      .s {{ font-size:1.4rem; margin:4px 0 18px; color:rgba(255,255,255,.95); }}
      .d {{ font-size:1.05rem; color:rgba(255,255,255,.85); line-height:1.55; max-width:560px; }}
      @media (max-width:900px){{
        .main-copy {{ left:28px; right:20px; max-width:calc(100% - 48px); }}
        .t{{font-size:2.4rem;}} .s{{font-size:1.15rem;}} .d{{font-size:0.98rem;}}
      }}
      @media (max-width:600px){{
        .main-hero {{ min-height:320px; }}
        .main-copy {{ left:20px; right:16px; }}
        .t{{font-size:2rem;}} .s{{font-size:1rem; margin:4px 0 12px;}} .d{{font-size:0.9rem;}}
      }}
    </style>
    <section class="main-hero">
      <div class="main-copy">
        <div class="t">P-IRIS</div>
        <div class="s">POSCO International Risk Intelligence Solution</div>
        <div class="d">24시간 365일, 당신을 위해 깨어 있습니다.</div>
      </div>
    </section>
    """, unsafe_allow_html=True)

    # ── 바로가기 CTA 카드 그리드 (클래스 기반 반응형) ──
    # 클래스만 사용(인라인 style 없음)하므로 st.markdown sanitize 영향 없음.
    # iframe 고정 높이로 인한 모바일 잘림을 피하고, CSS auto-fit으로 데스크톱 6열·모바일 2열 자동 대응.
    _role = st.session_state.get("role", "pr")
    _cards = []
    if _role == "pr":
        _cards.append(("뉴스 모니터링", "📰", "실시간 기사 수집·감성 분석"))
    _cards += [
        ("키워드 인사이트", "🔍", "AI 기반 트렌드·리스크 분석"),
        ("이슈보고 생성", "📋", "AI 이슈 발생 보고서 자동 작성"),
        ("언론사 정보", "🏢", "출입매체·기자 연락처 조회"),
        ("담당자 정보", "👥", "내부 부서·담당자 검색"),
        ("대응이력 검색", "📂", "과거 언론대응 이력 검색"),
    ]
    _cards_html = "".join(
        f'<a href="?menu={label}" target="_self" class="iris-cta-card">'
        f'<span class="cta-ico">{ico}</span>'
        f'<span class="cta-ttl">{label}</span>'
        f'<span class="cta-dsc">{dsc}</span></a>'
        for label, ico, dsc in _cards
    )
    st.markdown(f'<div class="iris-cta-grid">{_cards_html}</div>', unsafe_allow_html=True)

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
        # ── 생성: 결과를 세션에 저장만 하고, 표시는 아래 공통 렌더가 담당 ──
        # (생성·표시가 한 블록에 있으면 편집/다운로드 클릭 rerun 때 gen=False가 되어
        #  결과가 통째로 사라지는 워크플로 파괴 버그가 있었음 → 생성/표시 디커플)
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
                # 키가 'issue_'로 시작하면 메뉴 전환 시 정리 로직에 지워지므로 다른 프리픽스 사용
                st.session_state["saved_issue_report"] = {
                    "content": report,
                    "media": media,
                    "reporter": reporter,
                    "issue": issue,
                    "created": datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S'),
                }
                # 이전 편집본 초기화 (새 보고서 기준으로 textarea 재생성)
                st.session_state.pop("saved_issue_report_edit", None)

        # ── 표시: 세션에 보고서가 있으면 항상 렌더 (편집·다운로드에도 유지) ──
        saved = st.session_state.get("saved_issue_report")
        if saved:
            st.markdown('<div class="card result-card">', unsafe_allow_html=True)
            st.markdown("### 생성된 이슈 발생 보고서")
            st.caption(f"{saved['media']} · {saved['reporter']} · {saved['created']} 생성")
            edited = st.text_area("보고서 내용(수정 가능)", value=saved["content"], height=300, key="saved_issue_report_edit")
            payload = f"""포스코인터내셔널 언론대응 이슈 발생 보고서
================================

생성일시: {saved['created']}
언론사: {saved['media']}
기자명: {saved['reporter']}
발생 이슈: {saved['issue']}

보고서 내용:
{edited}
"""
            dl_col, clr_col = st.columns([3, 1])
            with dl_col:
                st.download_button("⬇ 보고서 다운로드", data=payload,
                                   file_name=f"이슈발생보고서_{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M%S')}.txt",
                                   mime="text/plain", use_container_width=True)
            with clr_col:
                if st.button("🗑 지우기", use_container_width=True, key="issue_report_clear"):
                    st.session_state.pop("saved_issue_report", None)
                    st.session_state.pop("saved_issue_report_edit", None)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="es-icon">📝</div>
                <div class="es-title">보고서가 여기에 표시됩니다</div>
                <div class="es-desc">좌측에 언론사, 기자명, 발생 이슈를 입력하고<br>생성 버튼을 눌러주세요.</div>
            </div>
            """, unsafe_allow_html=True)

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
                                show_table(df_reporters, "👥 출입기자 상세정보",
                                           csv_name=f"출입기자_{info.get('name','언론사')}.csv",
                                           phone_cols=("연락처",), email_cols=("이메일",))
                        else:
                            st.info("등록된 출입기자 정보가 없습니다.")
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
            show_table(pd.DataFrame(filtered), "👥 담당자 검색 결과",
                       csv_name="담당자_검색결과.csv",
                       phone_cols=("연락처",), email_cols=("이메일",))
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
    show_table(df, "🔷 전체 부서 담당자 정보", csv_name="전체_부서_담당자.csv")
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
            clear_data_cache()  # 캐시 클리어
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

    # 현재 연도 데이터 필터링
    current_year = datetime.now().year
    df_current = df_all[df_all["발생 일시"].dt.year == current_year].copy()

    # 현재 연도 통계 정보 표시 (상단에 바로 표시)
    stage_counts = df_current["단계"].value_counts().to_dict()
    관심_count = stage_counts.get('관심', 0)
    주의_count = stage_counts.get('주의', 0)
    위기_count = stage_counts.get('위기', 0)
    비상_count = stage_counts.get('비상', 0)

    total = len(df_current)
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
        year=current_year,
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

            show_table(display_df, "",
                       csv_name=f"언론대응이력_{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d')}.csv")
        else:
            st.warning("❌ 검색 조건에 맞는 내역이 없습니다.")

def page_news_monitor():
    # ===== 기본 파라미터 (news_collector.KEYWORDS를 단일 진실 공급원으로 사용) =====
    keywords = KEYWORDS
    # 포스코 검색 결과에서 제외할 키워드 (중복 방지)
    exclude_keywords = EXCLUDE_KEYWORDS

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

    # ===== [컨트롤 Row] 알림 | 표시방식 | 타이머 | 새로고침 | CSV — 1줄 통합 =====
    # CSS 전역 주입 (타이머·버튼 동일 높이 38px 포함)
    st.markdown("""
    <style>
    /* ━━━ 모든 Row: 수직 중앙 + 섹션 간격 ━━━ */
    div[data-testid="stHorizontalBlock"] {
        gap: 0.5rem !important;
        margin-bottom: 22px !important;
        align-items: center !important;
    }
    /* ━━━ 상태 알림 여백 최소화 ━━━ */
    div[data-testid="stColumn"] .stAlert {
        margin: 0 !important;
        padding: 6px 10px !important;
    }
    /* ━━━ 버튼 여백 제거 ━━━ */
    div[data-testid="stColumn"] .stDownloadButton,
    div[data-testid="stColumn"] .stButton { margin-top: 0 !important; }
    /* ━━━ 새로고침·CSV 버튼: 38px 동일 높이 ━━━ */
    div[data-testid="stColumn"] .stButton > button,
    div[data-testid="stColumn"] .stDownloadButton > button {
        height: 38px !important;
        min-height: 38px !important;
        padding: 0 10px !important;
        font-size: 0.82rem !important;
        white-space: nowrap !important;
        width: 100% !important;
        margin-top: 0 !important;
    }
    /* ━━━ CSV 래퍼 전체 폭 ━━━ */
    div[data-testid="stColumn"] .stDownloadButton {
        width: 100% !important;
        display: flex !important;
    }
    /* ━━━ 라디오 버튼 ━━━ */
    div[data-testid="stRadio"] { margin-top: 0 !important; padding-top: 0 !important; }
    div[data-testid="stRadio"] > div { gap: 0.5rem !important; align-items: center; }
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label > div,
    div[data-testid="stRadio"] span,
    div[data-testid="stRadio"] p,
    .stRadio > label > div[data-testid="stMarkdownContainer"] > p { color: var(--c-text) !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── 1행: 상태 알림 + 새로고침 + 타이머 (액션/상태 컨트롤) ──
    c_status, c_refresh, c_timer = st.columns([7, 2, 2])
    with c_status:
        status = st.empty()
    with c_refresh:
        manual_refresh = st.button("🔄 새로고침", use_container_width=True)
    with c_timer:
        countdown_fragment(refresh_interval)

    # ── 2행: 뷰 선택 + 감성 필터 + CSV (표시/내보내기 컨트롤) ──
    c_view, c_sent, c_download = st.columns([3, 6, 2])

    # ===== 새로고침 방식 결정 =====
    # 수동 새로고침: Naver API 직접 호출 (실시간 최신 뉴스)
    # 자동 새로고침/초기 로드: Naver API 호출 (최신 데이터)
    if manual_refresh:
        # 수동 새로고침: API 캐시 초기화 후 실시간 수집
        crawl_all_news_sources.clear()  # 3분 캐시 강제 초기화
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
        # 브라우저는 직접 크롤링하지 않는다. 수집은 backend(auto_monitor 백그라운드 + GitHub Actions
        # heartbeat)가 전 키워드를 주기적으로 수행해 DB(news_monitor.csv)에 저장해 둔다 → 여기서는
        # 그 DB만 즉시 읽어 표시한다. (브라우저가 직접 크롤링하면 백그라운드 수집과 동시 호출되어
        #  네이버 rate limit 429 유발 + 새로고침 버퍼링이 생기므로, 수집과 표시를 분리.)
        status.info("🔄 최신 뉴스 불러오는 중…")
        try:
            # 로컬 DB 우선 로드: backend(auto_monitor 백그라운드)가 같은 컨테이너의 로컬 CSV를
            # 갱신하므로 로컬이 가장 신선함(GitHub 커밋본은 더 stale할 수 있음). 없으면 GitHub 폴백.
            df_latest = load_news_db(force_refresh=False)
            st.session_state.news_display_data = df_latest
            st.session_state.last_news_fetch = time.time()
            status.success(f"✅ 최신 뉴스 {len(df_latest)}건 표시 중")
        except Exception as e:
            status.error(f"❌ 뉴스 불러오기 오류: {e}")

        # 플래그 리셋 + 다음 라운드 타임스탬프
        st.session_state.trigger_news_update = False
        st.session_state.next_refresh_at = time.time() + refresh_interval
        st.session_state.initial_loaded = True

    # ===== 화면 표시 (저장된 최신 데이터 기준) =====
    # 세션에 최신 수집 데이터가 있으면 우선 사용 (즉시 반영)
    db = st.session_state.get('news_display_data', load_news_db())

    if db.empty:
        st.markdown('<p style="color: var(--c-text);">📰 저장된 뉴스 데이터가 없습니다.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # 키워드 필터 & 정렬
    pattern = "|".join(keywords)
    df_show = db[db["검색키워드"].astype(str).str.contains(pattern, case=False, na=False)].copy()
    if df_show.empty:
        st.markdown('<p style="color: var(--c-text);">📰 POSCO 관련 기사가 없습니다.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        return

    df_show = df_show.sort_values(by="날짜", ascending=False, na_position="last").reset_index(drop=True)

    # ── 2행 채우기: 뷰 선택 + 감성 필터 ──
    with c_view:
        view = st.radio(
            "표시 방식", ["카드형 뷰", "테이블 뷰"],
            index=0, horizontal=True, key="news_view",
            label_visibility="collapsed"
        )
    with c_sent:
        sent_filter = st.radio(
            "감성 필터", ["전체", "긍정·중립", "부정만 보기"],
            index=0, horizontal=True, key="news_sent_filter",
            label_visibility="collapsed"
        )

    # 감성 필터는 head(50) 이전에 적용 — "부정만 보기"가 상단 50건에 갇히지 않도록
    total_before_filter = len(df_show)
    if "sentiment" in df_show.columns and sent_filter != "전체":
        sent_series = df_show["sentiment"].astype(str)
        if sent_filter == "부정만 보기":
            df_show = df_show[sent_series == "neg"]
        else:
            df_show = df_show[sent_series != "neg"]
    filtered_count = len(df_show)
    df_show = df_show.head(50)

    if sent_filter != "전체":
        st.caption(f"전체 {total_before_filter:,}건 중 {filtered_count:,}건 (최신 {len(df_show)}건 표시)")

    if df_show.empty:
        st.info("조건에 맞는 기사가 없습니다.")
        return

    if "URL" in df_show.columns:
        df_show["매체명"] = df_show["URL"].apply(_publisher_from_link)
    if "매체명" in df_show.columns:
        df_show["매체명"] = df_show.apply(
            lambda row: _publisher_from_link(row["URL"]) if pd.notna(row["URL"]) else row["매체명"], axis=1
        )

    with c_download:
        st.download_button(
            "⬇ CSV",
            df_show.to_csv(index=False).encode("utf-8-sig"),  # 엑셀 한글 호환
            file_name=f"posco_news_{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if view == "카드형 뷰":
        st.markdown("""
<style>
  /* 기사 목록 카드 — 좌측 정렬 강제 (dashboard .news-card의 center 덮어쓰기) */
  .news-card{
    background: var(--c-panel);
    border: 1px solid var(--c-panel-border);
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 12px;
    transition: all 0.2s ease;
    position: relative;
    /* 좌측 정렬 override */
    display: block !important;
    text-align: left !important;
    align-items: flex-start !important;
  }
  .news-card:hover{
    background: var(--c-panel-h);
    border-color: var(--c-panel-border-h);
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
    background: var(--c-gold-dim);
    color: var(--c-gold);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
  }
  .news-key{
    background: rgba(100,155,195,.10);
    color: #55a8d8;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 500;
  }
  .news-date{
    color: var(--c-text-mute);
    font-size: 12px;
    font-weight: 400;
  }

  /* 중간: 제목과 요약 — 좌측 정렬 명시 */
  .news-title{
    color: var(--c-text-strong);
    font-size: 16px;
    font-weight: 600;
    line-height: 1.55;
    margin: 0 0 12px 0;
    word-break: break-word;
    text-align: left !important;
  }
  .news-summary{
    color: var(--c-text-dim);
    font-size: 13px;
    line-height: 1.7;
    margin: 0 0 16px 0;
    text-align: left !important;
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

  /* 보고서 생성 버튼 - 적당한 여백으로 가독성 확보 */
  button[kind="secondary"] {
    height: auto !important;
    min-height: auto !important;
    padding: 7px 14px !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    transition: all 0.2s ease !important;
    background-color: var(--c-surface-h) !important;
    border: 1px solid var(--c-border) !important;
    margin-bottom: 4px !important;
  }
  button[kind="secondary"]:hover {
    background-color: var(--c-gold-deep) !important;
    border-color: var(--c-gold-deep) !important;
    color: var(--c-on-gold) !important;
  }

  /* 생성된 보고서 스타일 */
  .report-container {
    background: var(--c-surface);
    border: 1px solid var(--c-border);
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    color: var(--c-text);
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
                if st.button("📄 기사 요약", key=report_key, type="secondary"):
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

# ----------------------------- 자동 모니터 (cron-job.org 트리거) -----------------------------

def auto_monitor_on_load():
    """
    앱 로드 시 자동으로 뉴스 수집 + 텔레그램 발송 실행.
    cron-job.org가 2분마다 앱 URL을 호출할 때 트리거됨.

    동시 실행 방지:
    - 파일 기반 실행 간격 체크 (100초) - 세션과 무관하게 동작
    - fcntl 파일 락 (Linux/Streamlit Cloud 환경)
    """
    # 주의: session_state 게이트 제거됨.
    # cron-job.org가 같은 세션을 재사용할 경우 session_state 플래그가 재실행을 막아버림.
    # 파일 기반 rate limiting(100초 간격 + fcntl 락)으로만 중복 방지.

    MIN_INTERVAL_SEC = 100  # 2분 cron 기준, 100초 미만이면 스킵
    run_status_path = os.path.join("data", "run_status.json")
    lock_path = os.path.join("data", "monitor.lock")

    # 1단계: 마지막 실행 시간 체크 (빠른 early-exit)
    try:
        if os.path.exists(run_status_path):
            with open(run_status_path, 'r', encoding='utf-8') as f:
                status = json.load(f)
            last_run_str = status.get("last_run_time", "")
            if last_run_str:
                elapsed = (datetime.now() - datetime.fromisoformat(last_run_str)).total_seconds()
                if elapsed < MIN_INTERVAL_SEC:
                    print(f"[AUTO_MONITOR] 최근 {elapsed:.0f}초 전 실행됨 - 스킵")
                    return
    except Exception as e:
        print(f"[AUTO_MONITOR] 상태 파일 읽기 실패 (무시): {e}")

    # 2단계: 파일 락 획득 (동시 세션/프로세스 중복 실행 방지)
    os.makedirs("data", exist_ok=True)
    try:
        lock_fd = open(lock_path, 'w')
    except Exception:
        return

    def _release_lock(_fd):
        try:
            import fcntl
            fcntl.flock(_fd, fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            _fd.close()
        except Exception:
            pass

    try:
        import fcntl
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (ImportError, IOError, OSError):
        # Windows 환경이거나 다른 프로세스/스레드가 이미 락 보유 중
        print("[AUTO_MONITOR] 파일 락 획득 실패 (다른 인스턴스 실행 중) - 스킵")
        try:
            lock_fd.close()
        except Exception:
            pass
        return

    # 3단계: 락 획득 후 재확인 (락 대기 중 다른 프로세스가 실행했을 수 있음)
    try:
        if os.path.exists(run_status_path):
            with open(run_status_path, 'r', encoding='utf-8') as f:
                status = json.load(f)
            last_run_str = status.get("last_run_time", "")
            if last_run_str:
                elapsed = (datetime.now() - datetime.fromisoformat(last_run_str)).total_seconds()
                if elapsed < MIN_INTERVAL_SEC:
                    print(f"[AUTO_MONITOR] 락 획득 후 재확인: {elapsed:.0f}초 전 실행됨 - 스킵")
                    _release_lock(lock_fd)
                    return
    except Exception:
        pass

    # 4단계: 실행 시작 시각 선행 기록 (다른 세션이 중복 진입 못하도록)
    try:
        status_update = {}
        if os.path.exists(run_status_path):
            with open(run_status_path, 'r', encoding='utf-8') as f:
                status_update = json.load(f)
        status_update["last_run_time"] = datetime.now().isoformat()
        with open(run_status_path, 'w', encoding='utf-8') as f:
            json.dump(status_update, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # 5단계: standalone_monitor.main()을 백그라운드 스레드로 실행 (페이지 렌더 비차단).
    #  - 수집/발송은 백그라운드에서 진행되고, 화면은 즉시 저장된 DB를 표시 → 버퍼링 제거.
    #  - 락은 스레드 종료 시 해제 (실행 중 다른 인스턴스 중복 진입 방지).
    import threading

    def _run_bg(_fd):
        try:
            import standalone_monitor
            standalone_monitor.main()
            print(f"[AUTO_MONITOR] 백그라운드 수집 완료: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"[AUTO_MONITOR] 백그라운드 실행 오류: {e}")
        finally:
            _release_lock(_fd)

    threading.Thread(target=_run_bg, args=(lock_fd,), daemon=True).start()
    print("[AUTO_MONITOR] 백그라운드 수집 시작 (페이지 비차단)")


# ----------------------------- 재접속 스플래시 -----------------------------
def _show_reconnect_splash():
    """모바일 복귀 등 재접속 시 쿠키 동기화(1런) 동안 보여줄 가벼운 스플래시.
    무거운 로그인 페이지(배경이미지·폰트·CSS) 렌더를 건너뛰어 '재부팅' 체감을 없앤다."""
    st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
            min-height:72vh;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="font-size:1.5rem;letter-spacing:.18em;font-weight:800;color:#D4AF37;">P-IRIS</div>
  <div style="margin-top:12px;font-size:.9rem;color:#94a3b8;">불러오는 중…</div>
  <div style="margin-top:18px;width:26px;height:26px;border:3px solid rgba(255,255,255,.15);
              border-top-color:#D4AF37;border-radius:50%;animation:pirisSpin .8s linear infinite;"></div>
</div>
<style>@keyframes pirisSpin{to{transform:rotate(360deg)}}</style>
""", unsafe_allow_html=True)
    # 쿠키 컴포넌트가 리런을 못 일으키는 경우를 대비한 짧은 폴백 자동 새로고침
    try:
        st_autorefresh(interval=1200, key="_auth_splash_refresh", limit=5)
    except Exception:
        pass


# ----------------------------- 메인 루틴 -----------------------------
def main():
    # cron-job.org 트리거: 인증 체크 전에 실행 (cron-job.org는 로그인하지 않음)
    auto_monitor_on_load()

    # 인증 체크 - 인증되지 않은 경우 로그인 페이지 표시
    if not check_authentication():
        # 재접속(모바일 복귀 등)은 새 세션이라 쿠키 동기화에 1런이 필요하다.
        # 최초 1회는 무거운 로그인 페이지 대신 가벼운 스플래시를 띄우고,
        # 쿠키가 동기화되면(리런) 자동으로 앱에 진입한다. 실제 쿠키가 없으면 다음 런에서 로그인.
        if not st.session_state.get("_auth_grace_used"):
            st.session_state["_auth_grace_used"] = True
            _show_reconnect_splash()
            return
        show_login_page()
        return
    st.session_state.pop("_auth_grace_used", None)

    load_base_css()
    # 테마: 리런마다 DOM이 다시 그려지므로 data-theme 속성을 매 렌더 재적용 (필수)
    apply_theme_attribute(get_current_theme())
    if "data_loaded" not in st.session_state:
        st.session_state["data_loaded"] = True

    active = set_active_menu_from_url()

    # general 역할 사용자가 접근 불가 메뉴에 진입하면 첫 번째 허용 메뉴로 보정
    _visible = get_visible_menu()
    if active not in _visible and active != "메인":
        active = _visible[0] if _visible else "메인"
        st.query_params["menu"] = active
        st.session_state["top_menu"] = active
        st.rerun()

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
    elif active == "이슈보고 생성":
        page_issue_report()
    elif active == "언론사 정보":
        page_media_search()
    elif active == "담당자 정보":
        page_contact_search()
    elif active == "대응이력 검색":
        page_history_search()
    elif active == "뉴스 모니터링":
        if st.session_state.get("role") != "pr":
            st.warning("접근 권한이 없습니다.")
            st.stop()
        page_news_monitor()
    elif active == "키워드 인사이트":
        from pages.keyword_insight import render_keyword_insight_page
        render_keyword_insight_page()
    else:
        # 잘못된 파라미터면 메인으로 보냄
        st.query_params["menu"] = "메인"
        st.rerun()

    # 버전 정보 표시 (하단, 작게)
    st.markdown(
        '<div style="text-align:center; color:rgba(255,255,255,0.2); font-size:11px; margin-top:40px; padding-bottom:20px;">P-IRIS v2.1</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()