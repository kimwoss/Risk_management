# streamlit_app.py
"""
포스코인터내셔널 언론대응 보고서 생성 시스템
Streamlit 웹 애플리케이션 (다크테마·레이아웃 보강판 + 라디오/입력창 스타일 + 기자 파서 강화)
"""
import streamlit as st
from PIL import Image
import json, os, io, re
import pandas as pd
import base64, mimetypes
from datetime import datetime, timezone, timedelta
from data_based_llm import DataBasedLLM
from llm_manager import LLMManager
import requests
import urllib.parse
from html import unescape
from dotenv import load_dotenv
import time

load_dotenv()  # .env의 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 읽기

# =============== 페이지 설정 (가장 먼저 선언) ===============
st.set_page_config(
    page_title="위기관리커뮤니케이션 AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====================== 경로 세팅 ======================
DATA_FOLDER = "data"
MASTER_DATA_FILE = os.path.join(DATA_FOLDER, "master_data.json")
MEDIA_RESPONSE_FILE = os.path.join(DATA_FOLDER, "언론대응내역.csv")
NEWS_DB_FILE = os.path.join(DATA_FOLDER, "news_monitor.csv")

# ====================== 캐시 로더 ======================
@st.cache_data
def _load_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

@st.cache_data
def load_master_data():
    # 파일 갱신 시간(mtime)을 키로 써서 변경 시 캐시 무효화
    mtime = os.path.getmtime(MASTER_DATA_FILE)
    st.session_state['_md_mtime'] = mtime  # (디버깅용)
    # 경로 문자열 뒤에 ?{mtime}를 붙여 캐시 키 변경
    return _load_json(f"{MASTER_DATA_FILE}?{mtime}")

@st.cache_data
def load_media_response_data():
    try:
        return pd.read_csv(MEDIA_RESPONSE_FILE, encoding='utf-8')
    except Exception as e:
        st.error(f"❌ 언론대응내역.csv 로드 오류: {e}")
        return pd.DataFrame()

# ====================== 캐시 로더 (Windows 안전 버전) ======================
import os, json
import pandas as pd
import streamlit as st

DATA_FOLDER = "data"
MASTER_DATA_FILE = os.path.join(DATA_FOLDER, "master_data.json")
MEDIA_RESPONSE_FILE = os.path.join(DATA_FOLDER, "언론대응내역.csv")

@st.cache_data
def _load_json_with_key(path: str, _cache_key: float) -> dict:
    """path는 실제 파일 경로 그대로, _cache_key는 캐시 무효화용(예: mtime)"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_master_data():
    try:
        mtime = os.path.getmtime(MASTER_DATA_FILE)
    except OSError:
        mtime = 0.0
    return _load_json_with_key(MASTER_DATA_FILE, mtime)

@st.cache_data
def _load_csv_with_key(path: str, _cache_key: float) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding='utf-8')
    except Exception:
        return pd.DataFrame()

def load_media_response_data():
    try:
        mtime = os.path.getmtime(MEDIA_RESPONSE_FILE)
    except OSError:
        mtime = 0.0
    return _load_csv_with_key(MEDIA_RESPONSE_FILE, mtime)

# ====================== 데이터 API ======================
def get_media_contacts():
    master_data = load_master_data()
    # media_contacts가 master_data.json의 최상위에 있어야 함
    return master_data.get("media_contacts", {})

def search_media_info(media_name: str):
    try:
        media_contacts = get_media_contacts()
        if not media_contacts:
            return None

        # 완전 일치 우선
        if media_name in media_contacts:
            media_data = media_contacts[media_name]
            return {
                'name': media_name,
                'type': media_data.get('구분', 'N/A'),
                'contact_person': media_data.get('담당자', 'N/A'),
                'desk': media_data.get('DESK', []),
                'reporters': media_data.get('출입기자', []),
                'raw_data': media_data
            }

        # 부분 일치
        name_lower = media_name.lower().strip()
        for media_key, media_info in media_contacts.items():
            if name_lower in media_key.lower():
                return {
                    'name': media_key,
                    'type': media_info.get('구분', 'N/A'),
                    'contact_person': media_info.get('담당자', 'N/A'),
                    'desk': media_info.get('DESK', []),
                    'reporters': media_info.get('출입기자', []),
                    'raw_data': media_info
                }
        return None
    except Exception as e:
        st.error(f"언론사 정보 검색 중 오류: {str(e)}")
        return None

def generate_issue_report(media_name, reporter_name, issue_description):
    try:
        data_llm = DataBasedLLM()
        return data_llm.generate_issue_report(media_name, reporter_name, issue_description)
    except Exception as e:
        return f"보고서 생성 중 오류가 발생했습니다: {str(e)}"

# ====================== 네이버 뉴스 유틸 함수들 ======================
def _naver_headers():
    cid = os.getenv("NAVER_CLIENT_ID", "")
    csec = os.getenv("NAVER_CLIENT_SECRET", "")
    if not cid or not csec:
        st.error("네이버 API 키가 없습니다. .env를 확인해주세요.")
    return {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec}

def _clean_text(s: str) -> str:
    if not s: return ""
    s = unescape(s)
    s = re.sub(r"</?b>", "", s)   # 네이버가 주는 <b> 태그 제거
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _publisher_from_link(u: str) -> str:
    try:
        host = urllib.parse.urlparse(u).netloc.lower().replace("www.", "")
        
        # 도메인을 언론사명으로 매핑
        media_mapping = {
            "sedaily.com": "서울경제",
            "cstimes.com": "충청투데이",
            "kihoilbo.co.kr": "기호일보", 
            "m-i.kr": "매일일보",
            "etoday.co.kr": "이투데이",
            "joongdo.co.kr": "중도일보",
            "sports.khan.co.kr": "경향신문(스포츠)",
            "economytalk.kr": "이코노미톡",
            "getnews.co.kr": "겟뉴스",
            "yna.co.kr": "연합뉴스",
            "topstarnews.net": "톱스타뉴스",
            "econonews.co.kr": "에코노뉴스",
            "news.bbsi.co.kr": "부산일보",
            "thetracker.co.kr": "더트래커",
            "job-post.co.kr": "잡포스트",
            "thepingpong.co.kr": "더핑퐁",
            "finomy.com": "피노미",
            "stardailynews.co.kr": "스타데일리뉴스",
            "seoulwire.com": "서울와이어",
            "fntimes.com": "파이낸셜뉴스",
            "mk.co.kr": "매일경제",
            "snmnews.com": "에스엔엠뉴스",
            "kmib.co.kr": "국민일보",
            "newswatch.kr": "뉴스워치",
            "epj.co.kr": "에너지경제",
            "ferrotimes.com": "철강금속신문",
            "news2day.co.kr": "뉴스투데이",
            "e2news.com": "이투뉴스",
            "newsworks.co.kr": "뉴스웍스",
            "dt.co.kr": "디지털타임스",
            "biztribune.co.kr": "비즈트리뷴",
            "newspim.com": "뉴스핌",
            "hansbiz.co.kr": "한스경제",
            "fnnews.com": "파이낸셜뉴스",
            "kyongbuk.co.kr": "경북일보",
            "news.mt.co.kr": "머니투데이",
            "mhns.co.kr": "목포MBC",
            "worktoday.co.kr": "워크투데이",
            "whitepaper.co.kr": "화이트페이퍼",
            "munhwa.com": "문화일보",
            "todayenergy.kr": "투데이에너지",
            "news.einfomax.co.kr": "연합인포맥스",
            "sentv.co.kr": "서울경제TV",
            "energydaily.co.kr": "에너지데일리",
            "yonhapnewstv.co.kr": "연합뉴스TV",
            "chosun.com": "조선일보",
            "donga.com": "동아일보",
            "joongang.co.kr": "중앙일보",
            "hani.co.kr": "한겨레",
            "khan.co.kr": "경향신문",
            "herald.co.kr": "헤럴드경제",
            "ytn.co.kr": "YTN",
            "sbs.co.kr": "SBS",
            "mbc.co.kr": "MBC",
            "kbs.co.kr": "KBS"
        }
        
        return media_mapping.get(host, host)
    except Exception:
        return ""

@st.cache_data(ttl=60)
def fetch_naver_news(query: str, start: int = 1, display: int = 50, sort: str = "date"):
    """네이버 뉴스 검색 API 한 페이지 호출"""
    try:
        url = "https://openapi.naver.com/v1/search/news.json"
        params = {"query": query, "start": start, "display": display, "sort": sort}
        headers = _naver_headers()
        
        # API 키가 없으면 조용히 빈 결과 반환
        if not headers.get("X-Naver-Client-Id") or not headers.get("X-Naver-Client-Secret"):
            return {"items": []}
            
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception:
        # 에러 시 빈 결과 반환 (자동갱신 시 에러 메시지 방지)
        return {"items": []}

def crawl_naver_news(query: str, max_items: int = 200, sort: str = "date") -> pd.DataFrame:
    """여러 페이지 돌며 최대 max_items 수집 → 표로 반환"""
    items, start, total = [], 1, 0
    display = 100 if max_items >= 100 else max(10, max_items)
    while total < max_items and start <= 1000:
        data = fetch_naver_news(query, start=start, display=min(display, max_items-total), sort=sort)
        arr = data.get("items", [])
        if not arr: break
        for it in arr:
            title = _clean_text(it.get("title"))
            desc  = _clean_text(it.get("description"))
            link  = it.get("originallink") or it.get("link") or ""
            pub   = it.get("pubDate", "")
            try:
                # 시간 정보까지 포함하여 저장 (분 단위까지)
                date_obj = pd.to_datetime(pub).tz_localize(None)
                date_str = date_obj.strftime("%Y-%m-%d %H:%M")
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
        if got == 0: break
        start += got
    df = pd.DataFrame(items, columns=["날짜","매체명","검색키워드","기사제목","주요기사 요약","URL"])
    if not df.empty:
        key = df["URL"].where(df["URL"].astype(bool), df["기사제목"] + "|" + df["날짜"])
        df = df.loc[~key.duplicated()].reset_index(drop=True)
    return df

def load_news_db() -> pd.DataFrame:
    if os.path.exists(NEWS_DB_FILE):
        try:
            return pd.read_csv(NEWS_DB_FILE, encoding="utf-8")
        except Exception:
            pass
    return pd.DataFrame(columns=["날짜","매체명","검색키워드","기사제목","주요기사 요약","URL"])

def save_news_db(df: pd.DataFrame):
    if not df.empty:
        # 기존 데이터의 매체명도 새로운 매핑으로 업데이트
        if "매체명" in df.columns and "URL" in df.columns:
            for idx, row in df.iterrows():
                if pd.notna(row["URL"]):
                    updated_media_name = _publisher_from_link(row["URL"])
                    df.at[idx, "매체명"] = updated_media_name
        
        # 안전한 날짜 정렬 (빈 값 처리)
        if "날짜" in df.columns:
            df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
            df = df.sort_values("날짜", ascending=False, na_position='last')
            df["날짜"] = df["날짜"].dt.strftime("%Y-%m-%d %H:%M")
        
        # 최신 50건만 유지
        df_top50 = df.head(50)
        df_top50.to_csv(NEWS_DB_FILE, index=False, encoding="utf-8")

# ====================== 공용 UI 함수 ======================
def show_table(df: pd.DataFrame, label: str):
    st.markdown(f"#### {label}")
    st.dataframe(df, use_container_width=True, height=min(560, 44 + min(len(df), 12) * 38))

# 더 느슨한 패턴들 (하이픈 유무, 공백 허용)
_PHONE_PATTERNS = [
    r'(?:0?1[016789])[ .-]?\d{3,4}[ .-]?\d{4}',   # 010-1234-5678 / 01012345678 / 10-1234-5678 등
]
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+')

def _extract_phone(text: str) -> str:
    s = text or ''
    for p in _PHONE_PATTERNS:
        m = re.search(p, s)
        if m:
            num = m.group(0)
            # 하이픈 표준화
            digits = re.sub(r'\D', '', num)
            if len(digits) == 11 and digits.startswith('010'):
                return f"010-{digits[3:7]}-{digits[7:]}"
            if len(digits) == 10 and digits.startswith('10'):
                return f"010-{digits[2:6]}-{digits[6:]}"
            return num
    return ''

def _extract_email(text: str) -> str:
    m = EMAIL_RE.search(text or '')
    return m.group(0) if m else ''

def parse_reporters_to_df(reporters) -> pd.DataFrame:
    if not reporters:
        return pd.DataFrame(columns=["이름","직책","연락처","이메일","소속/팀","비고"])

    rows = []
    for item in reporters:
        if isinstance(item, dict):
            name = item.get('이름') or item.get('name') or item.get('기자') or ''
            role = item.get('직책') or item.get('직급') or item.get('role') or ''
            phone = item.get('연락처') or item.get('mobile') or item.get('phone') or ''
            email = item.get('이메일') or item.get('email') or ''
            team  = item.get('팀') or item.get('소속') or ''
            note  = item.get('비고') or item.get('note') or ''
            rows.append([name, role, phone, email, team, note])
            continue

        s = " ".join([str(x).strip() for x in item]) if isinstance(item, (list, tuple)) else str(item).strip()
        email = EMAIL_RE.search(s)
        email = email.group(0) if email else ''
        phone = _extract_phone(s)

        parts = [p.strip() for p in re.split(r'[·\|,\t]+', s) if p.strip()]
        name  = parts[0] if parts else s
        team  = ''
        m = re.search(r'(.+?)\s*\((.+?)\)', name)
        if m:
            name, team = m.group(1).strip(), m.group(2).strip()

        role = ''
        for p in parts[1:]:
            if any(k in p for k in ['팀장','차장','기자','부장','에디터','데스크','CFO','국장']):
                role = p; break

        rows.append([name, role, phone, email, team, ''])

    df = pd.DataFrame(rows, columns=["이름","직책","연락처","이메일","소속/팀","비고"]).fillna('')

    # ⚠️ 중복 제거는 보수적으로: 이름+전화+이메일 모두 같을 때만 제거
    if not df.empty:
        df = df.drop_duplicates(subset=["이름","연락처","이메일"], keep="first").reset_index(drop=True)
    return df

def _to_people_df(lines, tag: str) -> pd.DataFrame:
    """문자열 리스트(lines)를 표로 변환 후 '구분' 컬럼(tag)을 붙인다."""
    if not lines:
        return pd.DataFrame(columns=["구분","이름","직책","연락처","이메일","소속/팀","비고"])
    df = parse_reporters_to_df(lines)
    # 사람 이름이 아닌 태그 행 제거(예: "<부장&데스크>")
    if not df.empty and "이름" in df.columns:
        df = df[~df["이름"].str.fullmatch(r"\s*<.*>\s*", na=False)]
    df.insert(0, "구분", tag)
    return df

# ====================== 스타일/CSS ======================
def load_css(_=0):
    st.markdown("""
    <style>
    /* ====== 중앙 컨테이너 폭 강제 ====== */
    .block-container,
    [data-testid="stAppViewContainer"] .block-container,
    [data-testid="stAppViewContainer"] > .main > div.block-container,
    [data-testid="stMain"] > div > div > div.block-container {
      max-width: 1360px !important;       /* 페이지 폭 확대: 1280px → 1360px */
      margin-left: auto !important;
      margin-right: auto !important;
      padding-left: 1.25rem !important;
      padding-right: 1.25rem !important;
    }

    /* 나머지 기존 스타일 유지 (아래는 네가 쓰던 것 그대로) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700&display=swap');
    [data-testid="stAppViewContainer"]{
      background: radial-gradient(1200px 800px at 20% 10%, #1a1b1f 0%, #0f1013 60%, #0a0b0d 100%) !important;
      color:#eee;
      font-family:'Inter','Noto Sans KR',system-ui,Segoe UI,Roboto,Apple SD Gothic Neo,Pretendard,sans-serif;
    }
    [data-testid="stHeader"]{ background:transparent !important; }

    /* 사이드바는 완전 제거 */
    section[data-testid="stSidebar"] { display:none !important; }
    .card{
      background: linear-gradient(135deg, rgba(24,24,28,.65), rgba(16,16,20,.8));
      border: 1px solid rgba(255,255,255,.08);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 8px 32px rgba(0,0,0,.3), 
                  0 1px 0 rgba(255,255,255,.05) inset;
      backdrop-filter: blur(10px);
      transition: all 0.3s ease;
    }
    .card:hover {
      transform: translateY(-2px);
      box-shadow: 0 12px 40px rgba(0,0,0,.4), 
                  0 1px 0 rgba(255,255,255,.08) inset;
    }
    .input-card{
      border-color: rgba(212,175,55,.3);
      background: linear-gradient(135deg, rgba(24,24,28,.75), rgba(16,16,20,.9));
    }
    .result-card{
      border-color: rgba(189,189,189,.2);
      background: linear-gradient(135deg, rgba(20,20,24,.75), rgba(14,14,18,.9));
    }
    .header-title{
      font-size: 2.0rem;
      font-weight: 300;
      color: #ffffff;
      margin: 0 0 8px 0;
      letter-spacing: -0.01em;
      line-height: 1.3;
    }
    .header-subtitle{
      font-size: 0.95rem;
      color: #bdbdbd;
      margin: 0 0 20px 0;
      font-weight: 400;
      letter-spacing: 0.01em;
    }
    .gen-divider{
      border: 0;
      height: 1px;
      background: linear-gradient(90deg, rgba(212,175,55,.4) 0%, rgba(255,255,255,.08) 100%);
      margin: 20px 0 24px 0;
    }
    .gen-side-title{
      font-size: 1.1rem;
      font-weight: 500;
      color: #ffffff;
      margin: 0 0 12px 0;
      letter-spacing: -0.01em;
    }

    /* DataFrame */
    div[data-testid="stDataFrame"]{
      background: rgba(255,255,255,.03) !important;
      border:1px solid rgba(255,255,255,.08);
      border-radius:10px;
    }
    div[data-testid="stDataFrame"] *{ color:#e7e7e7 !important; }

    /* Inputs */
    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stSelectbox>div>div>div>div{
      background:rgba(255,255,255,.92) !important; color:#111 !important;
      border:1px solid rgba(0,0,0,.15) !important;
    }
    .stTextInput>div>div>input::placeholder,
    .stTextArea>div>div>textarea::placeholder{ color:#8b8f98 !important; opacity:1; }
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus,
    .stSelectbox>div>div>div:focus-within{
      border-color:#D4AF37 !important;
      box-shadow:0 0 0 3px rgba(212,175,55,.18) inset !important;
      outline:none !important;
    }

    /* Genesis-style Buttons */
    .stButton>button{
      border-radius: 8px;
      font-weight: 500;
      border: 1px solid rgba(255,255,255,.12);
      background: linear-gradient(135deg, rgba(28,29,33,.9), rgba(20,21,25,.95));
      color: #ffffff;
      padding: 12px 24px;
      font-size: 0.95rem;
      letter-spacing: 0.01em;
      transition: all 0.3s ease;
      backdrop-filter: blur(10px);
    }
    .stButton>button:hover{
      border-color: rgba(212,175,55,.5);
      background: linear-gradient(135deg, rgba(32,33,37,.95), rgba(24,25,29,1));
      box-shadow: 0 4px 16px rgba(212,175,55,.15);
      transform: translateY(-1px);
    }
    .stButton>button:active{
      transform: translateY(0);
      box-shadow: 0 2px 8px rgba(212,175,55,.2);
    }
    </style>
    """, unsafe_allow_html=True)

def load_top_nav_css():
    st.markdown("""
    <style>
      :root{
        --brand:#ffffff;
        --ink:#f1f1f1;
        --ink-dim:#bdbdbd;
        --nav-bg:rgba(10,10,12,.95);
        --nav-h:#64px;
        --gold:#D4AF37;
      }
      
      /* Genesis-inspired 제목 스타일 */
      .genesis-section-title {
        font-size: 2.2rem;
        font-weight: 300;
        color: #ffffff;
        margin: 48px 0 32px 0;
        letter-spacing: -0.02em;
        position: relative;
        padding-left: 0;
        line-height: 1.2;
      }
      
      .genesis-section-title::before {
        content: "";
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 4px;
        height: 40px;
        background: linear-gradient(180deg, #D4AF37 0%, rgba(212,175,55,0.6) 100%);
        border-radius: 2px;
        margin-right: 16px;
      }
      
      .genesis-section-title .title-text {
        margin-left: 20px;
        display: inline-block;
      }
      
      .genesis-section-subtitle {
        font-size: 0.95rem;
        color: #bdbdbd;
        margin-top: -8px;
        margin-bottom: 24px;
        margin-left: 20px;
        font-weight: 400;
        letter-spacing: 0.01em;
      }
      /* 전체 배경 톤 (제네시스 느낌: 더 플랫하고 차콜) */
      [data-testid="stAppViewContainer"]{
        background: linear-gradient(180deg,#0c0d10 0%, #0a0b0d 100%) !important;
        color:var(--ink);
      }

      /* 기본 헤더 제거 및 상단 여백 보정 */
      [data-testid="stHeader"]{ background:transparent; height:0; }
      .block-container{ padding-top: calc(var(--nav-h) + 24px) !important; }

      /* 사이드바 완전 제거 */
      section[data-testid="stSidebar"] {
        display: none !important;
      }

      .gx-hero{
        width:100%; border-radius:14px; overflow:hidden;
        background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
        border:1px solid rgba(255,255,255,.08);
      }
      .gx-hero .pane{
        min-height: 300px;
        background: url('') center/cover no-repeat;
        display:flex; align-items:flex-end;
        padding: 56px 48px;
      }
      .gx-hero h1{
        font-size: 56px; line-height:1.05; margin:0;
        letter-spacing:.02em; font-weight:700; color:#fff;
      }
      .gx-hero .sub{
        margin-top:6px; color:#cfcfcf; font-size:1.05rem;
      }

      /* 데이터 프레임, 버튼 톤을 제네시스식으로 뉴트럴하게 정리 */
      .stButton>button{
        border-radius:8px; font-weight:700; border:1px solid rgba(255,255,255,.18);
        background: linear-gradient(180deg, #2a2b2f, #1a1b1f); color:#fff;
      }
      div[data-testid="stDataFrame"]{
        background: rgba(255,255,255,.02) !important;
        border:1px solid rgba(255,255,255,.08);
        border-radius:12px;
      }

      /* 모바일 대응 */
      @media (max-width: 880px){
        .gx-nav{ padding:0 16px; }
        .gx-nav .menu{ gap:18px; overflow-x:auto; }
        .gx-hero h1{ font-size: 36px; }
        .block-container{ padding-top: calc(var(--nav-h) + 14px) !important; }
      }
    </style>
    """, unsafe_allow_html=True)

def load_logo_data_uri():
    # 우선 SVG → PNG 순서로 탐색
    candidates = [
        os.path.join(DATA_FOLDER, "POSCO_INTERNATIONAL_Korean_Signature.svg"),
        os.path.join(DATA_FOLDER, "POSCO_INTERNATIONAL_Korean_Signature.png"),
        os.path.join(DATA_FOLDER, "logo.png"),  # 기존 백업
    ]
    for p in candidates:
        if os.path.exists(p):
            mt = mimetypes.guess_type(p)[0] or "image/png"
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            return f"data:{mt};base64,{b64}"
    return ""

def load_main_background_uri():
    main_bg_path = os.path.join(DATA_FOLDER, "Image_main.jpg")
    if os.path.exists(main_bg_path):
        with open(main_bg_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f"data:image/jpeg;base64,{b64}"
    return ""

def set_active_menu_from_url(default_label="메인"):
    import urllib.parse
    try:
        # st.query_params만 사용 (experimental API 제거)
        raw = st.query_params.get("menu", default_label)
        label = urllib.parse.unquote(str(raw))
        st.session_state["top_menu"] = label
        return label
    except Exception as e:
        # 세션 스테이트 기반 폴백
        if "top_menu" in st.session_state:
            return st.session_state["top_menu"]
        st.session_state["top_menu"] = default_label
        return default_label

def render_main_page():
    """메인 페이지 렌더링 (오른쪽 지구 + 왼쪽 카피, 잘림 없이)"""
    bg_uri = load_main_background_uri()

    st.markdown(f"""
    <style>
    .main-hero {{
        position: relative;
        width: 100%;
        height: 72vh;                 /* 화면 비율 고정 */
        min-height: 480px;
        border-radius: 16px;
        overflow: hidden;
        margin: 20px 0;
        box-shadow: 0 20px 60px rgba(0,0,0,0.4);
        /* 핵심: 오른쪽에 지구를 '잘리지 않게' 배치 */
        background:
          linear-gradient(90deg, rgba(0,0,0,.78) 0%, rgba(0,0,0,.45) 42%, rgba(0,0,0,0) 75%),
          url('{bg_uri}') right center / contain no-repeat,
          #000;
    }}
    /* 모바일/세로 화면에서는 cover로 전환 */
    @media (max-width: 900px) {{
        .main-hero {{
            background:
              linear-gradient(180deg, rgba(0,0,0,.72) 0%, rgba(0,0,0,.35) 60%),
              url('{bg_uri}') center 65% / cover no-repeat, #000;
        }}
    }}
    .main-hero__copy {{
        position: absolute;
        left: 48px;
        top: 50%;
        transform: translateY(-50%);
        max-width: 720px;
        color: #fff;
        text-shadow: 0 4px 20px rgba(0,0,0,.45);
    }}
    .main-hero__title {{
        font-size: 3.2rem;
        line-height: 1.15;
        font-weight: 300;
        margin: 0 0 8px 0;
        letter-spacing: -0.02em;
    }}
    .main-hero__subtitle {{
        font-size: 1.4rem; margin: 4px 0 18px 0; color: rgba(255,255,255,.95);
    }}
    .main-hero__desc {{
        font-size: 1.05rem; color: rgba(255,255,255,.85); line-height: 1.55;
        max-width: 560px;
    }}
    @media (max-width: 900px){{
        .main-hero__title {{ font-size: 2.2rem; }}
        .main-hero__subtitle {{ font-size: 1.1rem; }}
    }}
    </style>

    <section class="main-hero">
      <div class="main-hero__copy">
        <div class="main-hero__title">위기관리커뮤니케이션</div>
        <div class="main-hero__subtitle">AI 자동화 솔루션</div>
        <div class="main-hero__desc">
          포스코인터내셔널의 스마트한 언론대응 시스템입니다.<br/>
          AI 기반 분석으로 신속하고 정확한 위기관리 솔루션을 제공합니다.
        </div>
      </div>
    </section>
    """, unsafe_allow_html=True)
    

def render_top_nav(active_label: str):
    logo_uri = load_logo_data_uri()
    items = ["뉴스 모니터링", "이슈발생보고 생성", "언론사 정보 검색", "담당자 정보 검색", "기존대응이력 검색"]

    # 1단계: 컨테이너와 기본 스타일 (로고 클릭 가능하게)
    # 메인페이지일 때 body에 속성 추가
    main_page_script = """
    <script>
    if (""" + str(active_label == "메인").lower() + """) {
        document.body.setAttribute('data-main-page', 'true');
    } else {
        document.body.removeAttribute('data-main-page');
    }
    </script>
    """ if active_label == "메인" else ""
    
    st.markdown("""
    <div class="nav-container" style="max-width:1360px; margin:8px auto 12px; background:linear-gradient(180deg,rgba(20,20,22,.85),rgba(12,12,14,.85)); border:1px solid rgba(255,255,255,.08); border-radius:12px; padding:10px 18px;">
      <div style="display:flex; align-items:center; gap:20px;">
        <div class="logo-clickable" style="display:flex; align-items:center; gap:12px; cursor:pointer; transition:opacity 0.2s ease;" onclick="window.parent.postMessage({type: 'streamlit:setQueryParams', queryParams: {menu: '메인'}}, '*'); setTimeout(() => location.reload(), 100);">""" + 
    (f'<img src="{logo_uri}" alt="POSCO" style="height:34px;"/>' if logo_uri else '') + """
          <span style="color:#cfcfcf; font-weight:700; font-size:.9rem;">POSCO INTERNATIONAL</span>
        </div>
      </div>
    </div>
    <style>
      .logo-clickable:hover { opacity: 0.8; }
    </style>
    """ + main_page_script, unsafe_allow_html=True)

    # 2단계: 라디오 버튼 렌더링
    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        st.empty()  # 로고 공간 확보
    with col2:
        # 현재 활성 메뉴가 items에 있으면 해당 인덱스 사용, 메인이면 -1 (선택 없음)
        if active_label in items:
            idx = items.index(active_label)
        else:
            idx = -1  # 메인페이지일 때는 선택 없음 표시
        
        # 메뉴 항목에 빈 선택지를 추가하여 메인페이지일 때 선택되도록 함
        menu_items = [""] + items if active_label == "메인" else items
        menu_idx = 0 if active_label == "메인" else idx
        
        sel = st.radio("", menu_items, index=menu_idx, horizontal=True, label_visibility="collapsed", key="topnav_radio")
        
        # 빈 선택지를 선택했으면 메인으로 처리
        if sel == "":
            sel = "메인"

    # 3단계: 렌더링 후 강력한 CSS 주입 (모든 가능한 선택자 사용)
    st.markdown("""
    <style>
    /* 최고 우선순위로 라디오 점 완전 제거 */
    div[data-testid="stRadio"] input[type="radio"] { display: none !important; visibility: hidden !important; }
    div[data-testid="stRadio"] label > div:first-child,
    div[data-testid="stRadio"] [data-baseweb="radio"] > div:first-child,
    div[role="radiogroup"] label > div:first-child,
    div[role="radiogroup"] [data-baseweb="radio"] > div:first-child { 
        display: none !important; 
        width: 0 !important; 
        height: 0 !important; 
        opacity: 0 !important; 
        visibility: hidden !important;
        position: absolute !important;
        left: -9999px !important;
    }
    
    /* 라디오그룹을 탭처럼 */
    div[data-testid="stRadio"] div[role="radiogroup"] {
        display: flex !important;
        gap: 28px !important;
        align-items: center !important;
        justify-content: flex-end !important;
    }
    
    /* 라벨 스타일링 */
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        cursor: pointer !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* 텍스트만 보이게 + 탭 스타일 */
    div[data-testid="stRadio"] div[role="radiogroup"] label > div:last-child {
        color: #f1f1f1 !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em !important;
        padding: 8px 2px !important;
        position: relative !important;
        opacity: 0.9 !important;
        transition: all 0.2s ease !important;
    }
    
    /* 호버 효과 */
    div[data-testid="stRadio"] div[role="radiogroup"] label:hover > div:last-child {
        opacity: 1 !important;
    }
    
    /* 밑줄 애니메이션 */
    div[data-testid="stRadio"] div[role="radiogroup"] label > div:last-child::after {
        content: "" !important;
        position: absolute !important;
        left: 0 !important;
        right: 0 !important;
        bottom: -6px !important;
        height: 2px !important;
        background: #fff !important;
        transform: scaleX(0) !important;
        transform-origin: left !important;
        transition: transform 0.25s ease !important;
    }
    
    /* 선택된 탭 밑줄 */
    div[data-testid="stRadio"] div[role="radiogroup"] label[aria-checked="true"] > div:last-child::after,
    div[data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"] > div:last-child::after,
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) > div:last-child::after {
        transform: scaleX(1) !important;
    }
    
    /* 라디오 라벨 자체도 숨기기 */
    div[data-testid="stRadio"] > label {
        display: none !important;
    }
    
    /* 메인페이지일 때 첫 번째 빈 항목 숨기기 */
    div[data-testid="stRadio"] div[role="radiogroup"] label:first-child:has(div:last-child:empty) {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 선택 변경 처리
    # 메인페이지에서 첫 번째 메뉴를 다시 클릭한 경우가 아니라면 페이지 변경
    if active_label == "메인":
        # 메인페이지에서는 실제 메뉴를 선택했을 때만 변경
        if sel and sel != active_label:
            st.session_state["top_menu"] = sel
            st.query_params["menu"] = sel
            st.rerun()
    else:
        # 다른 페이지에서는 일반적인 처리
        if sel != active_label:
            st.session_state["top_menu"] = sel
            st.query_params["menu"] = sel
            st.rerun()

def render_hero(title="POSCO INTERNATIONAL", headline="Crisis Communication AI", sub="AI 기반 스마트 언론대응 솔루션"):
    st.markdown(f"""
    <div class="gx-hero">
      <div class="pane">
        <div>
          <div style="font-size:14px; letter-spacing:.24em; color:#b9b9b9; margin-bottom:6px;">{title}</div>
          <h1>{headline}</h1>
          <div class="sub">{sub}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def load_sidebar_radio_css():
    # 라디오가 렌더된 뒤에 적용(덮어쓰기 방지)
    st.markdown("""
    <style>
    /* 기본 텍스트 흰색 */
    section[data-testid="stSidebar"] [data-baseweb="radio"] label:has(input[type="radio"]) > div:last-child,
    section[data-testid="stSidebar"] [role="radiogroup"] label:has(input[type="radio"]) > div:last-child{
      color:#ffffff !important;
      transition: color .15s ease, text-shadow .15s ease;
    }
    /* hover 골드 */
    section[data-testid="stSidebar"] [data-baseweb="radio"] label:hover > div:last-child,
    section[data-testid="stSidebar"] [role="radiogroup"] label:hover > div:last-child{
      color:#D4AF37 !important;
      text-shadow:0 0 6px rgba(212,175,55,.25);
    }
    /* 선택 항목 골드+볼드 */
    section[data-testid="stSidebar"] [data-baseweb="radio"] label:has(input[type="radio"]:checked) > div:last-child,
    section[data-testid="stSidebar"] [role="radiogroup"] label:has(input[type="radio"]:checked) > div:last-child{
      color:#D4AF37 !important;
      font-weight:700 !important;
    }
    /* 라디오 점 */
    section[data-testid="stSidebar"] [data-baseweb="radio"] label input + div{
      border-color: rgba(255,255,255,.75) !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="radio"] label input:checked + div{
      background:#D4AF37 !important;
      border-color:#D4AF37 !important;
      box-shadow:0 0 0 3px rgba(212,175,55,.18) inset !important;
    }
    </style>
    """, unsafe_allow_html=True)

def load_logo():
    logo_path = os.path.join(DATA_FOLDER, "logo.png")
    if os.path.exists(logo_path):
        try:
            return Image.open(logo_path)
        except Exception:
            return None
    return None

# ====================== 메인 ======================
def main():
    load_css()
    load_top_nav_css()   # ✅ 추가
    if 'data_loaded' not in st.session_state:
        load_data()

    active = set_active_menu_from_url()   # ✅ URL 파라미터에서 현재 탭
    render_top_nav(active)                 # ✅ 상단 네비 출력

    # 사이드바는 비활성화
    with st.sidebar:
        st.empty()  # 상단 네비 완전 전환 시

    # ===== 메뉴 분기 =====
    if active == "메인":
        render_main_page()
    
    elif active == "이슈발생보고 생성":
        st.markdown("""
        <div class="genesis-section-title">
            <span class="title-text">이슈발생보고 생성</span>
        </div>
        <div class="genesis-section-subtitle">언론사 기자 문의에 대한 AI 기반 이슈 분석 보고서를 생성합니다</div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown('<div class="card input-card"><div class="gen-side-title">이슈 정보 입력</div>', unsafe_allow_html=True)
            selected_media = st.text_input("언론사명", placeholder="예: 조선일보, 동아일보, 한국경제 등", key="media_input")
            selected_reporter = st.text_input("기자명", placeholder="담당 기자명을 입력하세요", key="reporter_input")
            issue_description = st.text_area("발생 이슈", placeholder="발생한 이슈에 대해 상세히 기술해주세요...", height=150, key="issue_input")
            generate_button = st.button("이슈발생보고 생성", key="generate_btn", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="card result-card"><div class="gen-side-title">생성 결과</div>', unsafe_allow_html=True)
            if generate_button:
                if not selected_media.strip():
                    st.error("언론사명을 입력해주세요.")
                elif not selected_reporter.strip():
                    st.error("기자명을 입력해주세요.")
                elif not issue_description.strip():
                    st.error("발생 이슈를 입력해주세요.")
                else:
                    with st.spinner("AI가 분석하고 있습니다..."):
                        report = generate_issue_report(selected_media, selected_reporter, issue_description)
                        # 보고서 결과를 바로 수정할 수 있는 영역 추가
                        st.markdown("### 생성된 이슈 발생 보고서")
                        edited_report = st.text_area(
                            "보고서 내용(수정 가능)",
                            value=report,
                            height=300,
                            key="edited_report_area"
                        )
                        save_button = st.button("저장하기", key="save_report_btn", use_container_width=True)
                        if save_button:
                            with open("temp_issue_report.txt", "w", encoding="utf-8") as f:
                                f.write(edited_report)
                            st.success("보고서가 저장되었습니다. (temp_issue_report.txt)")

                        # 기존 다운로드 버튼도 유지
                        report_data = f"""
포스코인터내셔널 언론대응 이슈 발생 보고서
================================

생성일시: {datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')}
언론사: {selected_media}
기자명: {selected_reporter}
발생 이슈: {issue_description}

보고서 내용:
{edited_report}
"""
                        st.download_button(
                            label="보고서 다운로드",
                            data=report_data,
                            file_name=f"이슈발생보고서_{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
            else:
                st.info("좌측에서 정보를 입력하고 원하는 분석 버튼을 클릭해줘.")
            st.markdown('</div>', unsafe_allow_html=True)

    # ===== 메뉴 2: 언론사 정보 검색 =====
    elif active == "언론사 정보 검색":
        st.markdown("""
        <div class="genesis-section-title">
            <span class="title-text">언론사 정보 조회</span>
        </div>
        <div class="genesis-section-subtitle">언론사별 담당자 및 연락처 정보를 조회합니다</div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        media_search = st.text_input("언론사명을 입력하세요:", key="media_search", placeholder="예: 조선일보, 중앙일보, 한국경제 등")
        if st.button("🔍 언론사 정보 조회", key="media_info_btn", use_container_width=True):
            if media_search:
                with st.spinner("언론사 정보를 검색하고 있습니다..."):
                    media_info = search_media_info(media_search)
                    if media_info:
                        st.success(f"✅ '{media_info.get('name','')}' 언론사 정보를 찾았어!")
                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown("#### 📋 기본 정보")
                            name = media_info.get('name', 'N/A')
                            mtype = media_info.get('type', 'N/A')
                            contact = media_info.get('contact_person', 'N/A')
                            st.markdown(f"**언론사명**: {name}  ")
                            st.markdown(f"**분류**: {mtype}  ")
                            st.markdown(f"**담당자(社內)**: {contact}  ")
                            # ⛔️ DESK는 이제 여기서 그리지 않습니다.

                        with col2:
                            st.markdown("#### 👥 DESK + 출입기자 정보")
                            desk = media_info.get('desk', [])
                            reporters = media_info.get('reporters', [])

                            df_parts = []
                            if desk:
                                df_parts.append(_to_people_df(desk, "DESK"))
                            if reporters:
                                df_parts.append(_to_people_df(reporters, "출입기자"))

                            if df_parts:
                                df_people = pd.concat(df_parts, ignore_index=True)
                                # (선택) 중복 제거 기준 보강: 이름+연락처+이메일+구분
                                if not df_people.empty:
                                    df_people = df_people.drop_duplicates(subset=["구분","이름","연락처","이메일"], keep="first").reset_index(drop=True)
                                show_table(df_people, "👥 DESK + 출입기자")
                            else:
                                st.info("등록된 DESK/출입기자 정보가 없습니다.")

                        with st.expander("🔍 상세 데이터 (개발자용)"):
                            st.json(media_info.get('raw_data', {}))
                    else:
                        st.warning(f"❌ '{media_search}' 언론사 정보를 찾을 수 없어.")
                        with st.expander("📋 등록된 언론사 목록 확인"):
                            try:
                                contacts = get_media_contacts()
                                media_list = list(contacts.keys())
                                cols = st.columns(3)
                                for i, media in enumerate(media_list):
                                    cols[i % 3].write(f"• {media}")
                            except Exception as e:
                                st.error(f"언론사 목록 로드 실패: {str(e)}")
            else:
                st.error("언론사명을 입력해줘.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ===== 메뉴 3: 담당자 정보 검색 =====
    elif active == "담당자 정보 검색":
        st.markdown("""
        <div class="genesis-section-title">
            <span class="title-text">담당자 정보 검색</span>
        </div>
        <div class="genesis-section-subtitle">부서별 담당자 연락처 및 업무 정보를 조회합니다</div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        departments = load_master_data().get("departments", {})
        search_name = st.text_input("담당자 성명으로 검색:", key="contact_name_search", placeholder="예) 김우현")
        submitted = st.button("🔍 담당자 검색", key="contact_search_btn", use_container_width=True)

        def collect_all_rows():
            rows = []
            for dept_name, dept_info in departments.items():
                # 홍보그룹처럼 담당자들이 배열인 경우 처리
                if "담당자들" in dept_info:
                    for person in dept_info["담당자들"]:
                        rows.append({
                            "부서명": dept_name,
                            "성명": person.get("담당자", ""),
                            "직급": person.get("직급", ""),
                            "연락처": person.get("연락처", ""),
                            "이메일": person.get("이메일", "")
                        })
                else:
                    # 기존 단일 담당자 형태
                    rows.append({
                        "부서명": dept_name,
                        "성명": dept_info.get("담당자", ""),
                        "직급": dept_info.get("직급", ""),
                        "연락처": dept_info.get("연락처", ""),
                        "이메일": dept_info.get("이메일", "")
                    })
            return rows

        if submitted:
            all_rows = collect_all_rows()
            filtered = [r for r in all_rows if (search_name.strip() in r["성명"])] if search_name.strip() else all_rows
            if filtered:
                show_table(pd.DataFrame(filtered), "👥 담당자 검색 결과")
            else:
                st.warning("❌ 해당 조건에 맞는 담당자를 찾을 수 없어.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        main_dept_rows = []
        for dept_name, dept_info in departments.items():
            # 홍보그룹처럼 담당자들이 배열인 경우 처리
            if "담당자들" in dept_info:
                for person in dept_info["담당자들"]:
                    main_dept_rows.append([
                        dept_name,
                        person.get("담당자", ""),
                        person.get("직급", ""),
                        person.get("연락처", ""),
                        person.get("이메일", "")
                    ])
            else:
                # 기존 단일 담당자 형태
                main_dept_rows.append([
                    dept_name,
                    dept_info.get("담당자", ""),
                    dept_info.get("직급", ""),
                    dept_info.get("연락처", ""),
                    dept_info.get("이메일", "")
                ])
        main_dept_df = pd.DataFrame(
            main_dept_rows,
            columns=["부서명", "담당자", "직급", "연락처", "이메일"]
        )
        show_table(main_dept_df, "🔷 전체 부서 담당자 정보")
        st.markdown('</div>', unsafe_allow_html=True)

    # ===== 메뉴 4: 기존대응이력 검색 =====
    elif active == "기존대응이력 검색":
        st.markdown("""
        <div class="genesis-section-title">
            <span class="title-text">기존 대응 이력 검색</span>
        </div>
        <div class="genesis-section-subtitle">과거 위기 대응 사례를 검색하고 분석합니다</div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <style>
        .gm-card{background:linear-gradient(135deg, rgba(24,24,28,.65), rgba(14,14,18,.9));
                 border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:18px 18px;margin:12px 0 18px;
                 box-shadow:0 20px 40px -10px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.03)}
        .gm-divider{height:1px;border:0;margin:14px 0;background:linear-gradient(90deg, rgba(255,255,255,.08), rgba(255,255,255,.02))}
        </style>
        """, unsafe_allow_html=True)

        df_all = load_media_response_data()
        if df_all.empty:
            st.warning("❌ 데이터가 없습니다. 'data/언론대응내역.csv'를 확인해줘.")
        else:
            required_cols = ["발생 일시", "단계", "발생 유형", "현업 부서", "이슈 발생 보고", "대응 결과"]
            missing = [c for c in required_cols if c not in df_all.columns]
            if missing:
                st.error(f"필수 컬럼이 없습니다: {', '.join(missing)}")
            else:
                df_all["발생 일시"] = pd.to_datetime(df_all["발생 일시"], errors="coerce")
                valid_dates = df_all["발생 일시"].dropna()
                years = sorted(valid_dates.dt.year.unique().tolist()) if not valid_dates.empty else []

                with st.container():
                    st.markdown('<div class="gm-card">', unsafe_allow_html=True)
                    col_period, col_stage, col_kw, col_btn = st.columns([0.8, 0.8, 2.0, 0.6])

                    with col_period:
                        st.markdown('<div style="color:#bdbdbd;font-size:.82rem;margin-bottom:6px">기간</div>', unsafe_allow_html=True)
                        period_mode = st.selectbox("기간", ["전체", "연도", "연월"], index=0, label_visibility="collapsed")
                        sel_year = None
                        sel_month = None
                        if period_mode != "전체" and valid_dates.empty:
                            st.info("유효한 '발생 일시'가 없어 기간 필터를 사용할 수 없어.")
                            period_mode = "전체"
                        if period_mode == "연도" and years:
                            sel_year = st.selectbox("연도 선택", options=years, index=0, label_visibility="collapsed")
                        elif period_mode == "연월" and years:
                            sel_year = st.selectbox("연도 선택", options=years, index=0, label_visibility="collapsed")
                            months = sorted(valid_dates[valid_dates.dt.year == sel_year].dt.month.unique().tolist())
                            sel_month = st.selectbox("월 선택", options=months if months else [], index=0 if months else None,
                                                     disabled=(len(months) == 0), label_visibility="collapsed")

                    with col_stage:
                        st.markdown('<div style="color:#bdbdbd;font-size:.82rem;margin-bottom:6px">단계</div>', unsafe_allow_html=True)
                        stage_option = st.selectbox("단계", ["전체", "관심", "주의", "위기", "비상"], index=0, label_visibility="collapsed")

                    with col_kw:
                        st.markdown('<div style="color:#bdbdbd;font-size:.82rem;margin-bottom:6px">검색어</div>', unsafe_allow_html=True)
                        keyword = st.text_input("검색어", value="", label_visibility="collapsed",
                                                placeholder="예) 포스코, 실적발표, IR (여러 단어 공백 → AND)")

                    with col_btn:
                        st.markdown('<div style="color:#bdbdbd;font-size:.82rem;margin-bottom:6px">&nbsp;</div>', unsafe_allow_html=True)
                        do_search = st.button("🔍 검색", use_container_width=True)

                    st.markdown('</div>', unsafe_allow_html=True)

                if do_search:
                    result_df = df_all.copy()

                    if period_mode != "전체" and not valid_dates.empty:
                        if period_mode == "연도" and sel_year is not None:
                            result_df = result_df[result_df["발생 일시"].dt.year == sel_year]
                        elif period_mode == "연월" and sel_year is not None and sel_month is not None:
                            result_df = result_df[
                                (result_df["발생 일시"].dt.year == sel_year) &
                                (result_df["발생 일시"].dt.month == int(sel_month))
                            ]

                    if stage_option != "전체":
                        result_df = result_df[result_df["단계"].astype(str).str.contains(stage_option, case=False, na=False)]

                    if keyword.strip():
                        terms = [t for t in keyword.split() if t.strip()]
                        target_cols = ["발생 유형", "현업 부서", "이슈 발생 보고", "대응 결과"]
                        for t in terms:
                            mask_any = result_df[target_cols].astype(str).apply(
                                lambda col: col.str.contains(t, case=False, na=False)
                            ).any(axis=1)
                            result_df = result_df[mask_any]

                    st.markdown('<div class="gm-card">', unsafe_allow_html=True)
                    if not result_df.empty:
                        try:
                            result_df = result_df.sort_values("발생 일시", ascending=False)
                        except Exception:
                            pass
                        st.markdown(f"**📈 검색 결과: 총 {len(result_df)}건**")
                        st.markdown('<div class="gm-divider"></div>', unsafe_allow_html=True)
                        show_table(result_df, "📄 검색 결과")
                    else:
                        st.warning("❌ 검색 조건에 맞는 내역이 없어.")
                    st.markdown('</div>', unsafe_allow_html=True)

    # ===== 메뉴 5: 뉴스 모니터링 (포스코인터내셔널 전용) =====
    elif active == "뉴스 모니터링":
        st.markdown("""
        <div class="genesis-section-title">
            <span class="title-text">뉴스 모니터링</span>
        </div>
        <div class="genesis-section-subtitle">POSCO 관련 실시간 뉴스를 모니터링합니다</div>
        """, unsafe_allow_html=True)
        
        # 고정된 키워드와 설정
        keywords = ["포스코인터내셔널", "POSCO INTERNATIONAL", "포스코인터", "삼척블루파워", "포스코모빌리티솔루션"]
        refresh_interval = 180  # 3분으로 변경
        max_items = 100
        
        # 초기 세션 상태 설정
        if 'last_news_update' not in st.session_state:
            st.session_state.last_news_update = 0
        if 'initial_news_loaded' not in st.session_state:
            st.session_state.initial_news_loaded = False

        # 상태 표시와 버튼
        status_placeholder = st.empty()
        col1, col2 = st.columns([3, 1])
        with col2:
            manual_refresh = st.button("🔄 지금 새로고침", use_container_width=True)
        
        # 뉴스 데이터 로드 및 업데이트 처리
        current_time = time.time()
        should_initial_load = not st.session_state.initial_news_loaded
        should_update = (current_time - st.session_state.last_news_update > refresh_interval) or manual_refresh
        
        if should_initial_load or should_update:
            if should_initial_load:
                with status_placeholder:
                    st.info("🔄 초기 뉴스 데이터를 가져오는 중...")
                load_count = 50
            else:
                with status_placeholder:
                    st.info("🔄 포스코인터내셔널 최신 뉴스를 가져오는 중...")
                load_count = max_items
            
            try:
                # 여러 키워드로 뉴스 수집
                all_news = []
                for keyword in keywords:
                    df_kw = crawl_naver_news(keyword, max_items=load_count//len(keywords), sort="date")
                    if not df_kw.empty:
                        all_news.append(df_kw)
                
                if all_news:
                    df_new = pd.concat(all_news, ignore_index=True)
                    # 중복 제거
                    df_new = df_new.drop_duplicates(subset=["URL","기사제목"], keep="first").reset_index(drop=True)
                else:
                    df_new = pd.DataFrame()
                
                if should_initial_load:
                    # 초기 로드
                    if not df_new.empty:
                        save_news_db(df_new)
                        st.session_state.initial_news_loaded = True
                        st.session_state.last_news_update = current_time
                        with status_placeholder:
                            st.success(f"✅ 초기 데이터 로드 완료! {len(df_new)}건의 기사를 가져왔습니다.")
                    else:
                        st.session_state.initial_news_loaded = True
                        with status_placeholder:
                            st.warning("⚠️ 초기 데이터를 가져올 수 없습니다.")
                else:
                    # 업데이트
                    db = load_news_db()
                    if not df_new.empty:
                        merged = pd.concat([df_new, db], ignore_index=True)
                        merged = merged.drop_duplicates(subset=["URL","기사제목"], keep="first").reset_index(drop=True)
                        
                        # 날짜별 정렬 (최신순)
                        if not merged.empty:
                            merged["날짜"] = pd.to_datetime(merged["날짜"], errors="coerce")
                            merged = merged.sort_values("날짜", ascending=False, na_position='last').reset_index(drop=True)
                            merged["날짜"] = merged["날짜"].dt.strftime("%Y-%m-%d %H:%M")
                        
                        save_news_db(merged)  # 최신 50건만 저장
                        new_count = len(df_new)
                        
                        st.session_state.last_news_update = current_time
                        
                        with status_placeholder:
                            current_kst = datetime.now(timezone(timedelta(hours=9)))
                            if new_count > 0:
                                st.success(f"✅ 업데이트 완료! 새 기사 {new_count}건 추가 (최신 50건 유지) - {current_kst.strftime('%H:%M:%S')}")
                            else:
                                st.markdown(f'<p style="color: white;">ℹ️ 새로운 기사 없음 (최신 50건 유지) - {current_kst.strftime("%H:%M:%S")}</p>', unsafe_allow_html=True)
                    else:
                        with status_placeholder:
                            st.warning("⚠️ 검색 결과가 없습니다.")
                            
            except Exception as e:
                with status_placeholder:
                    st.error(f"❌ 뉴스 수집 오류: {str(e)}")
                if should_initial_load:
                    st.session_state.initial_news_loaded = True  # 오류 시에도 더이상 로드 시도하지 않음
        
        else:
            # 다음 업데이트까지 남은 시간 표시 (하얀색 글씨)
            time_left = refresh_interval - (current_time - st.session_state.last_news_update)
            with status_placeholder:
                st.markdown(f'<p style="color: white;">⏰ 다음 자동 업데이트까지 {int(time_left)}초</p>', unsafe_allow_html=True)

        # 현재 저장된 뉴스 표시 (항상 실행)
        st.markdown("---")
        db = load_news_db()

        if not db.empty:
            # 모든 키워드 필터링
            keyword_pattern = "|".join(keywords)
            df_show = db[db["검색키워드"].astype(str).str.contains(keyword_pattern, case=False, na=False)].copy()
            
            if not df_show.empty:
                # 최신순 정렬하고 최신 50건만 표시
                df_show = df_show.sort_values(by="날짜", ascending=False, na_position='last').reset_index(drop=True)
                df_show = df_show.head(50)  # 최신 50건만
                
                # 헤더와 다운로드 버튼
                col_header, col_download = st.columns([3, 1])
                with col_header:
                    st.markdown(f"**📊 POSCO 관련 기사: {len(df_show)}건 (최신 50건)**")
                with col_download:
                    st.download_button(
                        "⬇ CSV 다운로드",
                        df_show.to_csv(index=False).encode("utf-8"),
                        file_name=f"posco_news_{datetime.now(timezone(timedelta(hours=9))).strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv", use_container_width=True
                    )
                
                # 뷰 모드 선택 (라디오 버튼 스타일 적용)
                st.markdown("""
                <style>
                /* 라디오 버튼 모든 텍스트를 하얀색으로 강제 설정 */
                div[role="radiogroup"] label span {
                    color: #ffffff !important;
                }
                div[data-baseweb="radio"] label span {
                    color: #ffffff !important;
                }
                div[role="radiogroup"] label > div:last-child {
                    color: #ffffff !important;
                }
                div[data-baseweb="radio"] label > div:last-child {
                    color: #ffffff !important;
                }
                /* 라디오 버튼 라벨 및 옵션 텍스트 하얀색 */
                .stRadio > label {
                    color: #ffffff !important;
                }
                .stRadio div[role="radiogroup"] label {
                    color: #ffffff !important;
                }
                .stRadio div[role="radiogroup"] label span {
                    color: #ffffff !important;
                }
                .stRadio label[data-baseweb="radio"] {
                    color: #ffffff !important;
                }
                .stRadio label[data-baseweb="radio"] span {
                    color: #ffffff !important;
                }
                .stRadio label[data-baseweb="radio"] > div {
                    color: #ffffff !important;
                }
                /* 모든 라디오 버튼 관련 텍스트 */
                [data-testid="stRadio"] label {
                    color: #ffffff !important;
                }
                [data-testid="stRadio"] label span {
                    color: #ffffff !important;
                }
                [data-testid="stRadio"] label > div {
                    color: #ffffff !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                view_mode = st.radio(
                    "표시 방식",
                    ["카드형 뷰", "테이블 뷰"],
                    index=0,
                    horizontal=True,
                    help="카드형 뷰: 모든 정보를 한눈에 / 테이블 뷰: 전통적인 표 형태"
                )
                
                if view_mode == "카드형 뷰":
                    # 카드형 뷰 - 모든 컬럼 정보를 보기 좋게 표시
                    st.markdown("""
                    <style>
                    .news-card {
                        background: rgba(255,255,255,0.05);
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 8px;
                        padding: 15px;
                        margin: 10px 0;
                        transition: all 0.3s ease;
                    }
                    .news-card:hover {
                        background: rgba(255,255,255,0.08);
                        border-color: #D4AF37;
                    }
                    .news-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 8px;
                    }
                    .news-date {
                        color: #D4AF37;
                        font-weight: 600;
                        font-size: 0.9rem;
                    }
                    .news-media {
                        background: rgba(212,175,55,0.2);
                        color: #D4AF37;
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 0.8rem;
                        font-weight: 600;
                    }
                    .news-title {
                        color: #ffffff;
                        font-size: 1.1rem;
                        font-weight: 600;
                        margin: 8px 0;
                        line-height: 1.4;
                    }
                    .news-summary {
                        color: #cccccc;
                        font-size: 0.9rem;
                        line-height: 1.5;
                        margin: 8px 0;
                        max-height: 60px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    .news-url {
                        margin-top: 10px;
                    }
                    .news-url a {
                        color: #87CEEB;
                        text-decoration: none;
                        font-size: 0.85rem;
                        display: inline-block;
                        max-width: 400px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    }
                    .news-url a:hover {
                        color: #D4AF37;
                        text-decoration: underline;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # 각 뉴스를 카드 형태로 표시
                    for idx, row in df_show.iterrows():
                        title = row.get("기사제목", "").strip('"')
                        summary = row.get("주요기사 요약", "")
                        if len(summary) > 150:
                            summary = summary[:150] + "..."
                        
                        # 날짜 시간 포맷 처리
                        date_time = row.get("날짜", "")
                        if " " in str(date_time):  # 시간 정보가 있는 경우
                            date_part, time_part = str(date_time).split(" ", 1)
                            formatted_datetime = f"📅 {date_part} 🕐 {time_part}"
                        else:
                            formatted_datetime = f"📅 {date_time}"
                        
                        st.markdown(f"""
                        <div class="news-card">
                            <div class="news-header">
                                <span class="news-date">{formatted_datetime}</span>
                                <span class="news-media">{row.get("매체명", "")}</span>
                            </div>
                            <div class="news-title">{title}</div>
                            <div class="news-summary">{summary}</div>
                            <div class="news-url">
                                <a href="{row.get("URL", "")}" target="_blank" title="{row.get("URL", "")}">🔗 기사 보기: {row.get("URL", "")}</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    # 테이블 뷰 - 컬럼 순서 조정 및 표시
                    df_table = df_show[["날짜", "매체명", "검색키워드", "기사제목", "주요기사 요약", "URL"]].copy()
                    
                    # 컬럼명을 더 직관적으로 변경
                    df_table = df_table.rename(columns={
                        "날짜": "📅 발행일시",
                        "매체명": "📰 언론사",
                        "검색키워드": "🔍 키워드",
                        "기사제목": "📰 제목",
                        "주요기사 요약": "📝 요약",
                        "URL": "🔗 링크"
                    })
                    
                    st.dataframe(
                        df_table, 
                        use_container_width=True, 
                        height=min(700, 44 + max(len(df_table), 12)*35),
                        column_config={
                            "🔗 링크": st.column_config.LinkColumn(
                                "🔗 링크",
                                help="기사 원문 링크",
                                display_text="기사보기"
                            ),
                            "📝 요약": st.column_config.TextColumn(
                                "📝 요약",
                                help="기사 요약",
                                max_chars=100
                            )
                        }
                    )
            else:
                st.markdown('<p style="color: white;">📰 POSCO 관련 기사가 없습니다.</p>', unsafe_allow_html=True)
        else:
            if st.session_state.initial_news_loaded:
                st.markdown('<p style="color: white;">📰 저장된 뉴스 데이터가 없습니다.</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color: white;">📰 초기 데이터를 로드하고 있습니다...</p>', unsafe_allow_html=True)

        # --- 자동 새로고침: 주기적으로만 작동 ---
        if st.session_state.initial_news_loaded:
            # streamlit 1.30+ 에서 st.autorefresh 지원. 하위버전 호환용 JS 폴백 포함
            _autorefresh = getattr(st, "autorefresh", None)
            if _autorefresh:
                _autorefresh(interval=refresh_interval * 1000)  # milliseconds
            else:
                # 폴백: JavaScript 기반 자동새로고침
                st.markdown(f"""
                <script>
                // 페이지 로드 후 {refresh_interval}초마다 새로고침
                setTimeout(function() {{
                    if (!window.newsAutoRefreshStarted) {{
                        window.newsAutoRefreshStarted = true;
                        setInterval(function() {{
                            window.location.reload();
                        }}, {refresh_interval * 1000});
                    }}
                }}, {refresh_interval * 1000});
                </script>
                """, unsafe_allow_html=True)

# 세션 로딩 플래그
def load_data():
    st.session_state['data_loaded'] = True

# 담당자 정보 로딩 함수 정의 (NameError 방지)
def get_contact_info():
    # master_data.json의 departments 정보를 반환
    master_data = load_master_data()
    return master_data.get("departments", {})

if __name__ == "__main__":
    main()