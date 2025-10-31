# streamlit_app.py
"""
포스코인터내셔널 언론대응 보고서 생성 시스템
- 상단 네비: 순수 Streamlit 버튼 기반 (iFrame/JS 제거, 확실한 리런)
- 중복된 로더/스타일 정리
"""
import os, json, re, time, base64, mimetypes, urllib.parse, requests
from datetime import datetime, timezone, timedelta

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from PIL import Image
from html import unescape
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # NEW

from data_based_llm import DataBasedLLM

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

# ----------------------------- 인증 설정 -----------------------------
ACCESS_CODE = "pointl"  # 비밀코드

def check_authentication():
    """인증 확인 함수"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated

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

    st.markdown('<div style="margin-bottom: 12px; text-align: left; color: rgba(255,255,255,.7); font-size: 13px; font-weight: 600;">비밀코드</div>', unsafe_allow_html=True)
    code_input = st.text_input(
        "비밀코드",
        type="password",
        placeholder="비밀코드를 입력하세요",
        label_visibility="collapsed",
        key="login_code_input"
    )

    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    if st.button("로그인", use_container_width=True, key="login_button"):
        if code_input == ACCESS_CODE:
            st.session_state.authenticated = True
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
    except OSError:
        mtime = 0.0
    return _load_csv_with_key(MEDIA_RESPONSE_FILE, mtime)

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
            # 사용자 제공 도메인들 추가
            "youthdaily.co.kr": "청년일보",
            "weeklytrade.co.kr": "주간무역",
            "viva100.com": "비바100",
            "obsnews.co.kr": "OBS뉴스",
            "newsworks.co.kr": "뉴스웍스",
            "newstomato.com": "뉴스토마토",
            "newsquest.co.kr": "뉴스퀘스트",
            "nbnews.kr": "NBN뉴스",
            "naeil.com": "내일신문",
            "kmib.co.kr": "국민일보",
            "joongdo.co.kr": "중도일보",
            "joins.com": "중앙일보",
            "imaeil.com": "매일신문",
            "etoday.co.kr": "이투데이",
            "ekn.kr": "에너지경제",
            "dailian.co.kr": "데일리안",
            "biztribune.co.kr": "비즈니스트리뷴",
            "asiae.co.kr": "아시아경제",
            
            # 네가 준 목록 + 기존 보강
            "wikileaks-kr.org": "위키리크스한국",
            "newsian.co.kr": "뉴시안",
            "nocutnews.co.kr": "노컷뉴스",
            "yna.co.kr": "연합뉴스",
            "pinpointnews.co.kr": "핀포인트뉴스",
            "ohmynews.com": "오마이뉴스",
            "ebn.co.kr": "EBN",
            "joongangenews.com": "중앙앤뉴스",
            "news1.kr": "뉴스1",
            "sisaweek.com": "시사위크",
            "kbsm.net": "KBS부산·경남",
            "newscj.com": "천지일보",
            "mhnse.com": "MHN스포츠",
            "newspim.com": "뉴스핌",
            "munhwa.com": "문화일보",
            "starnewskorea.com": "스타뉴스",
            "thepingpong.co.kr": "더핑퐁",
            "worldkorean.net": "월드코리안뉴스",
            "shinailbo.co.kr": "신아일보",
            "insight.co.kr": "인사이트",
            "ajunews.com": "아주경제",
            "businesskorea.co.kr": "비즈니스코리아",
            "kbs.co.kr": "KBS",
            "ferrotimes.com": "철강금속신문",
            "dealsitetv.com": "딜사이트TV",
            "edaily.co.kr": "이데일리",
            "heraldcorp.com": "헤럴드경제",
            "dt.co.kr": "디지털타임스",
            "m-i.kr": "매일일보",
            "energy-news.co.kr": "에너지뉴스",
            "donga.com": "동아일보",
            "breaknews.com": "브레이크뉴스",
            "nspna.com": "NSP통신",
            "hankooki.com": "한국일보",          # (daily.hankooki.com은 위에서 '데일리한국'으로 처리)
            "enewstoday.co.kr": "이뉴스투데이",
            "newsbrite.net": "뉴스브라이트",
            "kjmbc.co.kr": "광주MBC",
            "segye.com": "세계일보",

            # 사용자 제공 도메인 매핑 추가
            "zdnet.co.kr": "지디넷코리아",
            "wsobi.com": "월드스포츠비즈니스아이",
            "womentimes.co.kr": "여성타임즈",
            "whitepaper.co.kr": "화이트페이퍼",
            "todayenergy.kr": "투데이에너지",
            "thetracker.co.kr": "더트래커",
            "thelec.kr": "더일렉",
            "theguru.co.kr": "더구루",
            "techholic.co.kr": "테크홀릭",
            "snmnews.com": "SNM뉴스",
            "smedaily.co.kr": "SME데일리",
            "seoul.co.kr": "서울신문",
            "sedaily.com": "서울경제",
            "popcornnews.net": "팝콘뉴스",
            "pointe.co.kr": "포인트경제",
            "nextdaily.co.kr": "넥스트데일리",
            "newswatch.kr": "뉴스워치",
            "newsprime.co.kr": "뉴스프라임",
            "newsis.com": "뉴시스",
            "newsinside.kr": "뉴스인사이드",
            "newdaily.co.kr": "뉴데일리",
            "metroseoul.co.kr": "메트로서울",
            "meconomynews.com": "엠이코노미뉴스",
            "lawissue.co.kr": "법률저널",
            "laborplus.co.kr": "노동플러스",
            "kukinews.com": "국민일보",
            "industrynews.co.kr": "산업뉴스",
            "hidomin.com": "하이도민",
            "g-enews.com": "지이뉴스",
            "einfomax.co.kr": "연합인포맥스",
            "econovill.com": "이코노빌",
            "cnbnews.com": "CNB뉴스",
            "aving.net": "AVING",

            # 추가 매체 매핑 2차
            "thebell.co.kr": "더벨",
            "sisaon.co.kr": "시사ON",
            "newsmaker.or.kr": "뉴스메이커",
            "munhaknews.com": "문학뉴스",
            "kwnews.co.kr": "강원일보",
            "koreaherald.com": "코리아헤럴드",
            "joseilbo.com": "조세일보",
            "jeonmae.co.kr": "전국매일신문",
            "idaegu.co.kr": "IDN대구신문",
            "fntimes.com": "파이낸셜타임스",
            "asiatoday.co.kr": "아시아투데이",

            # 추가 매체명 변경 (2025-01-20)
            "digitaltoday.co.kr": "디지털투데이",
            "sisajournal.com": "시사저널",
            "skyedaily.com": "스카이데일리",
            "nongmin.com": "농민신문",
            "kado.net": "강원도민일보",
            "econonews.co.kr": "이코노뉴스",
            "finomy.com": "현대경제신문",
            "isplus.com": "일간스포츠",
            "ksmnews.co.kr": "경상매일신문",
            "seoulfn.com": "서울파이낸스",
            "seoulwire.com": "서울와이어",
            "yeongnam.com": "영남일보",

            # 추가 매체명 변경 (2025-01-21)
            "tokenpost.kr": "토큰포스트",
            "queen.co.kr": "이코노미퀸",
            "newstapa.org": "뉴스타파",
            "mt.co.kr": "머니투데이",
            "moneys.co.kr": "머니S",
            "kbmaeil.com": "경북매일",
            "gukjenews.com": "국제뉴스",
            "etnews.com": "전자신문",
            "businesspost.co.kr": "비즈니스포스트",

            # 추가 매체명 변경 (2025-01-29)
            "worktoday.co.kr": "워크투데이",
            "widedaily.com": "와이드경제",
            "thepowernews.co.kr": "더파워",
            "swtvnews.com": "스포츠W",
            "startuptoday.co.kr": "스타트업투데이",
            "sisafocus.co.kr": "시사포커스",
            "newsfc.co.kr": "금융소비자뉴스",
            "marketnews.co.kr": "마켓뉴스",
            "lkp.news": "리버티코리아포스트",
            "kihoilbo.co.kr": "기호일보",
            "incheonnews.com": "인천뉴스",
            "hansbiz.co.kr": "한스경제",
            "hankookilbo.com": "한국일보",
            "greened.kr": "녹색경제신문",
            "getnews.co.kr": "글로벌경제신문",
            "gasnews.com": "가스신문",
            "epj.co.kr": "일렉트릭파워",
            "bloter.net": "블로터",
            "amenews.kr": "신소재경제신문",

            # 기타 대형/보편
            "chosun.com": "조선일보",
            "joongang.co.kr": "중앙일보",
            "hani.co.kr": "한겨레",
            "khan.co.kr": "경향신문",
            "herald.co.kr": "헤럴드경제",
            "mk.co.kr": "매일경제",
            "fnnews.com": "파이낸셜뉴스",
            "hankyung.com": "한국경제",
            "wowtv.co.kr": "한국경제TV",
            "ytn.co.kr": "YTN",
            "sbs.co.kr": "SBS",
            "mbc.co.kr": "MBC",
            "inews24.com": "아이뉴스24",
        }

        return base_map.get(base, base)  # 모르는 도메인은 '기본 도메인'으로 통일
    except Exception:
        return ""

# --- OpenAI 키 조회 (OPENAI_API_KEY 또는 OPEN_API_KEY 둘 다 지원) ---
def _get_openai_key():
    return os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY") or ""

def _openai_chat(messages, model=None, temperature=0.2, max_tokens=400):
    """경량 OpenAI Chat 호출 (requests 사용)"""
    api_key = _get_openai_key()
    if not api_key:
        return None, "OPENAI_API_KEY not set"
    model = model or os.getenv("OPENAI_GPT_MODEL", "gpt-4o-mini")
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

# --- 기사 본문/제목 추출 (가벼운 크롤러) ---
def _extract_article_text_and_title(url: str):
    html = ""
    try:
        resp = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text
    except Exception:
        pass

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

    # ✅ 개선된 프롬프트 (포괄성 + 논리성 강화)
    sys_prompt = """너는 포스코인터내셔널 홍보그룹 전용 '뉴스 보고 메시지 생성 봇'이다.
입력된 기사 핵심 내용을 기반으로 카카오톡 보고용 메시지를 작성한다. 추측·외부지식 금지.

[출력 형식 - 반드시 준수]
1) 첫 줄: 원문 링크
2) 빈 줄 1칸
3) 매체명 : 기사 제목
4) 핵심 요약 4~6줄
   - 각 줄 50자 이내, 하이픈(-) 시작
   - 마침표/이모지 금지
   - 순수 텍스트만 (코드블록/마크다운 금지)

[작성 원칙 - 절대 준수]
✅ 사실 기반: 기사 명시 내용만 사용 (추측·분석 금지)
✅ 숫자 정확성: 억/조/원/% 등 단위 원문 그대로 (절대 추정 금지)
✅ 포스코 우선: 포스코인터내셔널/그룹 관련 내용 1줄 이상 필수
✅ 포괄성: 실적·일정·계약·투자·공급망·향후계획 빠짐없이 포함 (중복 금지)
✅ 논리성: 원인→결과→영향 순서로 배열
✅ 제외: 기자명/작성시간/광고/메타정보

[필수 포함 요소] (기사에 있을 경우)
1) 핵심 사건/발표 내용 (What)
2) 관련 기업/기관 (Who)
3) 금액/수치/일정 (When/How much)
4) 비즈니스 영향/의미 (Impact)
5) 향후 계획/다음 단계 (Next)

[예시]
https://example.com/news/123

전기신문 : 광명시흥 3기 신도시 집단에너지 발전公 물밑 경쟁
- 산업부, 1일 집단에너지 신규 공급지역에 광명시흥 공공주택지구 지정 예비공고
- 남동발전 경쟁 선두, 동서발전도 당사와 함께 관심
- 발전공기업들의 타 사업 확보 여부가 경쟁 구도에 영향 전망
- 총 공급규모 약 3000억원 추정, 2026년 착공 목표"""

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

    backup_report = f"""{url}

{media} : {title}

{chr(10).join(f"- {b}" for b in bullets[:4])}"""
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
        # 오직 이 조각만 1초 리프레시
        st_autorefresh(interval=1000, key="countdown_tick")
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
        
        # 보고서 생성 중이 아닐 때만 자동 리프레시
        if not any(key.startswith("report_generating_") and st.session_state.get(key, False) for key in st.session_state.keys()):
            st_autorefresh(interval=1000, key="countdown_fallback")
        
        # 0초 되면 트리거 플래그 설정하고 즉시 페이지 리런
        if secs_left == 0 and not st.session_state.get("trigger_news_update", False):
            st.session_state.trigger_news_update = True
            st.rerun()

def fetch_naver_news(query: str, start: int = 1, display: int = 50, sort: str = "date"):
    try:
        url = "https://openapi.naver.com/v1/search/news.json"
        params = {"query": query, "start": start, "display": display, "sort": sort}
        headers = _naver_headers()
        
        print(f"[DEBUG] API Request - Query: {query}, Params: {params}")
        print(f"[DEBUG] Headers present: ID={bool(headers.get('X-Naver-Client-Id'))}, Secret={bool(headers.get('X-Naver-Client-Secret'))}")
        
        if not headers.get("X-Naver-Client-Id") or not headers.get("X-Naver-Client-Secret"):
            print("[DEBUG] Missing API keys, returning empty result")
            return {"items": []}
            
        print(f"[DEBUG] Starting API request...")
        r = requests.get(url, headers=headers, params=params, timeout=5)  # 타임아웃을 5초로 단축
        print(f"[DEBUG] API Response status: {r.status_code}")
        
        r.raise_for_status()
        result = r.json()
        print(f"[DEBUG] API Response items count: {len(result.get('items', []))}")
        return result
        
    except requests.exceptions.Timeout:
        print(f"[WARNING] Naver API timeout for query: {query}")
        return {"items": []}
    except requests.exceptions.RequestException as e:
        print(f"[WARNING] Naver API request failed for query: {query}, error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[WARNING] Response status: {e.response.status_code}, body: {e.response.text[:200]}")
        return {"items": []}
    except Exception as e:
        print(f"[WARNING] Unexpected error in fetch_naver_news: {e}")
        return {"items": []}

def crawl_naver_news(query: str, max_items: int = 200, sort: str = "date") -> pd.DataFrame:
    print(f"[DEBUG] Starting crawl_naver_news for query: {query}, max_items: {max_items}")
    items, start, total = [], 1, 0
    display = min(50, max_items)  # 한 번에 최대 50개로 제한
    max_attempts = 2  # 최대 2번 시도로 제한하여 빠른 실패
    attempt_count = 0
    
    while total < max_items and start <= 100 and attempt_count < max_attempts:  # 시작 위치도 100으로 제한
        attempt_count += 1
        print(f"[DEBUG] Attempt {attempt_count} for query: {query}")
        
        try:
            data = fetch_naver_news(query, start=start, display=min(display, max_items - total), sort=sort)
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
    if not df.empty:
        # 최신순 정렬 먼저 수행
        df["날짜_datetime"] = pd.to_datetime(df["날짜"], errors="coerce")
        df = df.sort_values("날짜_datetime", ascending=False, na_position="last").reset_index(drop=True)
        df = df.drop("날짜_datetime", axis=1)
        
        # 중복 제거 (URL 우선, 없으면 제목+날짜)
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
    if df.empty:
        print("[DEBUG] save_news_db skipped: empty dataframe")
        return
    # 매체명 정리 (URL 기반)
    if "매체명" in df.columns and "URL" in df.columns:
        for idx, row in df.iterrows():
            if pd.notna(row["URL"]):
                df.at[idx, "매체명"] = _publisher_from_link(row["URL"])
    
    # 날짜 컬럼이 이미 정렬되어 있으므로 추가 정렬 생략
    # 상위 50개만 저장
    out = df.head(50)
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

# ----------------------------- 스타일 -----------------------------
@st.cache_data(ttl=3600)  # CSS는 1시간 캐시
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
        border-color: rgba(212,175,55,.5);
        box-shadow: 0 4px 16px rgba(212,175,55,.15);
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

# ----------------------------- 자원 로드 -----------------------------
def load_logo_data_uri():
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

def load_main_background_uri():
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
      /* 개선된 네비게이션 스타일 - 제네시스 톤 */
      .stButton>button {
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
      .stButton>button:hover {
        border-color: rgba(212,175,55,.6) !important;
        background: linear-gradient(135deg, rgba(32,34,40,.9), rgba(24,26,32,.95)) !important;
        box-shadow: 0 4px 20px rgba(212,175,55,.12), 0 2px 8px rgba(0,0,0,0.2) !important;
        transform: translateY(-1px) !important;
        color: #fff !important;
      }
      .stButton>button:disabled {
        color: #D4AF37 !important;
        border-color: rgba(212,175,55,.8) !important;
        background: linear-gradient(135deg, rgba(212,175,55,.15), rgba(212,175,55,.08)) !important;
        box-shadow: 0 0 0 1px rgba(212,175,55,.3) inset, 0 4px 16px rgba(212,175,55,.08) !important;
        transform: none !important;
        font-weight: 700 !important;
      }
      .nav-container {
        background: linear-gradient(135deg, rgba(16,18,24,.4), rgba(12,14,20,.6));
        border: 1px solid rgba(255,255,255,.06);
        border-radius: 16px;
        padding: 16px 20px;
        margin: 8px 0 20px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,.2);
        backdrop-filter: blur(12px);
      }

      /* 모바일 최적화 (768px 이하) */
      @media (max-width: 768px) {
        .stButton>button {
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
          height: 40px !important;
        }
      }

      /* 더 작은 화면 (480px 이하) */
      @media (max-width: 480px) {
        .stButton>button {
          font-size: 0.7rem !important;
          padding: 6px 4px !important;
          min-height: 38px !important;
        }
        .nav-container {
          padding: 10px 8px !important;
          border-radius: 12px !important;
        }
        .nav-container img {
          height: 36px !important;
        }
      }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="nav-container">', unsafe_allow_html=True)
    with st.container():
        c1, c2 = st.columns([1.2, 4.0], gap="medium")
        with c1:
            if logo_uri:
                # 로고를 클릭 가능한 HTML로 직접 구현
                st.markdown(f'''
                <div style="width: 100%; height: 90px; display: flex; align-items: center; justify-content: center;">
                    <a href="?home=1" style="display: block; cursor: pointer; transition: all 0.2s ease;">
                        <img src="{logo_uri}" alt="POSCO 메인으로" title="메인 페이지로 이동"
                             style="height:54px; max-width: 100%; transition: transform 0.2s ease;"
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
    st.markdown("""
<div class="card" style="margin-top:8px">
  <div style="display:flex; align-items:center; justify-content:space-between; gap:12px;">
    <div style="font-weight:600;">이슈발생보고 생성</div>
    <a href="https://chatgpt.com/g/g-WMuN0viKE-pointeo-wigigwanrikeom-cinjeolhan-gaideu"
       target="_blank" rel="noopener noreferrer"
       style="display:inline-block; padding:10px 16px; border-radius:8px; font-weight:700; text-decoration:none;
              background:linear-gradient(135deg, #D4AF37, #B8941F); border:1px solid rgba(212,175,55,.4); color:#000;">
      GPT봇 사용하기
    </a>
  </div>
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
    st.markdown('<div class="card" style="margin-top:8px"><div style="font-weight:600; margin-bottom:8px;">언론사 정보 조회</div>', unsafe_allow_html=True)
    
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
    st.markdown('</div>', unsafe_allow_html=True)

def page_contact_search():
    st.markdown('<div class="card" style="margin-top:8px"><div style="font-weight:600; margin-bottom:8px;">담당자 정보 검색</div>', unsafe_allow_html=True)
    
    departments = load_master_data_fresh().get("departments", {})
    
    name = st.text_input("담당자 성명으로 검색:", placeholder="예) 김우현", key="contact_search_name")
    if st.button("🔍 담당자 검색", use_container_width=True):
        rows = []
        # 홍보그룹을 먼저 처리
        if "홍보그룹" in departments:
            dept = departments["홍보그룹"]
            if "담당자들" in dept:
                for p in dept["담당자들"]:
                    rows.append({"부서명": "홍보그룹", "성명": p.get("담당자",""), "직급": p.get("직급",""),
                                 "연락처": p.get("연락처",""), "이메일": p.get("이메일","")})
        # 나머지 부서들 처리
        for dept_name, dept in departments.items():
            if dept_name == "홍보그룹":  # 이미 처리했으므로 스킵
                continue
            if "담당자들" in dept:
                for p in dept["담당자들"]:
                    rows.append({"부서명": dept_name, "성명": p.get("담당자",""), "직급": p.get("직급",""),
                                 "연락처": p.get("연락처",""), "이메일": p.get("이메일","")})
            else:
                rows.append({"부서명": dept_name, "성명": dept.get("담당자",""), "직급": dept.get("직급",""),
                             "연락처": dept.get("연락처",""), "이메일": dept.get("이메일","")})
        filtered = [r for r in rows if (name.strip() in r["성명"])] if name.strip() else rows
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
                rows.append(["홍보그룹", p.get("담당자",""), p.get("직급",""), p.get("연락처",""), p.get("이메일","")])
    # 나머지 부서들 처리
    for dept_name, dept in departments.items():
        if dept_name == "홍보그룹":  # 이미 처리했으므로 스킵
            continue
        if "담당자들" in dept:
            for p in dept["담당자들"]:
                rows.append([dept_name, p.get("담당자",""), p.get("직급",""), p.get("연락처",""), p.get("이메일","")])
        else:
            rows.append([dept_name, dept.get("담당자",""), dept.get("직급",""), dept.get("연락처",""), dept.get("이메일","")])
    df = pd.DataFrame(rows, columns=["부서명","담당자","직급","연락처","이메일"])
    show_table(df, "🔷 전체 부서 담당자 정보")
    st.markdown('</div>', unsafe_allow_html=True)

def page_history_search():
    st.markdown('<div class="card" style="margin-top:8px"><div style="font-weight:600; margin-bottom:8px;">기존 대응 이력 검색</div>', unsafe_allow_html=True)

    # 30초마다 자동으로 파일 변경 체크 (백그라운드)
    st_autorefresh(interval=30000, key="history_autorefresh")

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

    # 2025년 데이터 필터링
    df_2025 = df_all[df_all["발생 일시"].dt.year == 2025].copy()

    # 2025년 통계 정보 표시 (상단에 바로 표시)
    st.markdown("### 📊 2025년 데이터 통계")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

    stage_counts = df_2025["단계"].value_counts().to_dict()
    관심_count = stage_counts.get('관심', 0)
    주의_count = stage_counts.get('주의', 0)
    위기_count = stage_counts.get('위기', 0)
    비상_count = stage_counts.get('비상', 0)

    with stat_col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; text-align: center;">
            <div style="color: rgba(255,255,255,0.8); font-size: 0.9em; margin-bottom: 5px;">총 건수</div>
            <div style="color: white; font-size: 2em; font-weight: bold;">{len(df_2025):,}건</div>
        </div>
        """, unsafe_allow_html=True)

    with stat_col2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 10px; text-align: center;">
            <div style="color: rgba(255,255,255,0.9); font-size: 0.9em; margin-bottom: 5px;">관심</div>
            <div style="color: white; font-size: 2em; font-weight: bold;">{관심_count}건</div>
        </div>
        """, unsafe_allow_html=True)

    with stat_col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ffa751 0%, #ffe259 100%); padding: 20px; border-radius: 10px; text-align: center;">
            <div style="color: rgba(255,255,255,0.9); font-size: 0.9em; margin-bottom: 5px;">주의</div>
            <div style="color: white; font-size: 2em; font-weight: bold;">{주의_count}건</div>
        </div>
        """, unsafe_allow_html=True)

    with stat_col4:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 10px; text-align: center;">
            <div style="color: rgba(255,255,255,0.9); font-size: 0.9em; margin-bottom: 5px;">위기/비상</div>
            <div style="color: white; font-size: 2em; font-weight: bold;">{위기_count + 비상_count}건</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # 검색 필터
    years = sorted(valid_dates.dt.year.unique().tolist()) if not valid_dates.empty else []
    type_options = ["전체"] + sorted([t for t in df_all["발생 유형"].dropna().unique().tolist() if t])

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

    st.markdown('</div>', unsafe_allow_html=True)

def page_news_monitor():
    # ===== 기본 파라미터 =====
    st.markdown('<div class="card" style="margin-top:8px"><div style="font-weight:600; margin-bottom:8px;">뉴스 모니터링</div>', unsafe_allow_html=True)
    keywords = [
        "포스코인터내셔널",
        "POSCO INTERNATIONAL",
        "포스코인터",
        "삼척블루파워",
        "포스코모빌리티솔루션",
        "속보+포스코",  # [속보]와 포스코가 함께 언급된 기사
        "단독+포스코",  # 단독과 포스코가 함께 언급된 기사
        "포스코"  # 일반 포스코 기사 (기존 키워드 제외 필터링 적용)
    ]
    # 포스코 검색 결과에서 제외할 키워드 (중복 방지)
    exclude_keywords = ["포스코인터내셔널", "POSCO INTERNATIONAL", "포스코인터",
                       "삼척블루파워", "포스코모빌리티솔루션"]

    refresh_interval = 180  # 180초 카운트다운
    max_items = 100

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

    # ===== 상단 UI (카운트다운/상태/수동 새로고침) =====
    c_count, c_status, c_btn = st.columns([1, 2.5, 1])
    with c_btn:
        manual_refresh = st.button("🔄 지금 새로고침", use_container_width=True)
    with c_status:
        status = st.empty()

    # 카운트다운 프래그먼트 (1초 단위 업데이트)
    with c_count:
        countdown_fragment(refresh_interval)

    # ===== 수집 조건: 트리거 플래그 or 수동 새로고침 =====
    should_fetch = manual_refresh or st.session_state.trigger_news_update or (not st.session_state.initial_loaded)

    # ===== 새로고침 시 기존 보고서 초기화 =====
    if manual_refresh or st.session_state.trigger_news_update:
        # 보고서 관련 세션 상태 키들을 모두 삭제
        report_keys = [key for key in st.session_state.keys() if key.startswith('report_state_')]
        for key in report_keys:
            del st.session_state[key]
        if report_keys:
            refresh_type = "수동" if manual_refresh else "자동"
            print(f"[DEBUG] {refresh_type} 새로고침: {len(report_keys)}개 보고서 초기화")

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
            if api_ok:
                # 키워드별 최신순 수집
                for kw in keywords:
                    df_kw = crawl_naver_news(kw, max_items=max_items // len(keywords), sort="date")
                    if not df_kw.empty:
                        # "포스코" 키워드의 경우 제목 기반 필터링
                        if kw == "포스코":
                            def should_include(row):
                                title = str(row.get("기사제목", ""))
                                title_lower = title.lower()

                                # 1단계: 제목에 "포스코"가 있는가?
                                if "포스코" not in title and "posco" not in title_lower:
                                    return False

                                # 2단계: 제목에 제외 키워드가 없는가?
                                for exclude_kw in exclude_keywords:
                                    if exclude_kw.lower() in title_lower:
                                        return False

                                return True

                            # 조건을 만족하는 기사만 포함
                            mask = df_kw.apply(should_include, axis=1)
                            df_kw = df_kw[mask].reset_index(drop=True)
                            if not df_kw.empty:
                                print(f"[DEBUG] '포스코' 제목 필터링: {len(df_kw)}건 추가")

                        if not df_kw.empty:
                            all_news.append(df_kw)

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

                    save_news_db(merged)
                    st.session_state.last_news_fetch = now
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
    db = load_news_db()
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
  .news-card{
    background:rgba(255,255,255,.05);
    border:1px solid rgba(255,255,255,.1);
    border-radius:8px;
    padding:15px; margin:10px 0;
    transition:all .3s ease;
  }
  .news-card:hover{ background:rgba(255,255,255,.08); border-color:#D4AF37; }
  .news-header{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
  .news-left{ display:flex; align-items:center; gap:8px; }
  .news-media{
    background:rgba(212,175,55,.2);
    color:#D4AF37;
    padding:2px 8px; border-radius:4px;
    font-size:.8rem; font-weight:700;
  }
  .news-key{
    background:rgba(255,255,255,.12);
    color:#e6e6e6;
    padding:2px 8px; border-radius:4px;
    font-size:.8rem; font-weight:600;
  }
  .news-date{ color:#D4AF37; font-weight:600; font-size:.9rem; }
  .news-title{ color:#fff; font-size:1.1rem; font-weight:600; margin:8px 0; line-height:1.4; }
  .news-summary{ color:#ccc; font-size:.9rem; line-height:1.5; margin:8px 0; max-height:60px; overflow:hidden; text-overflow:ellipsis; }
  .news-url a{ color:#87CEEB; text-decoration:none; font-size:.85rem; display:inline-block; max-width:400px;
               overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .news-url a:hover{ color:#D4AF37; text-decoration:underline; }
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
            if " " in dt:
                d, t = dt.split(" ", 1)
                formatted_dt = f"📅 {d}  🕐 {t}"
            else:
                formatted_dt = f"📅 {dt}"
            
            # 파일명에 사용할 안전한 제목 생성
            safe_name = re.sub(r'[^\w가-힣\s]', '', title)[:30]

            st.markdown(f"""
            <div class="news-card">
              <div class="news-header">
                <div class="news-left">
                  <span class="news-media">{media}</span>
                  <span class="news-key">{keyword}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span class="news-date">{formatted_dt}</span>
                </div>
              </div>
              <div class="news-title">{title}</div>
              <div class="news-summary">{summary}</div>
              <div class="news-url">
                <a href="{url}" target="_blank">🔗 기사 보기: {url}</a>
              </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 보고서 생성 버튼을 날짜 왼쪽에 배치
            col_btn, col_spacer = st.columns([1, 4])
            with col_btn:
                report_key = f"report_btn_{i}"
                report_state_key = f"report_state_{i}"
                
                # 보고서 상태 초기화
                if report_state_key not in st.session_state:
                    st.session_state[report_state_key] = {"generated": False, "content": ""}
                
                if st.button("📝 보고서 생성", key=report_key, use_container_width=True):
                    with st.spinner("기사 요약 생성 중..."):
                        try:
                            report_txt = make_kakao_report_from_url(
                                url, fallback_media=media, fallback_title=title, fallback_summary=summary
                            )
                            # 세션 상태에 보고서 저장
                            st.session_state[report_state_key]["generated"] = True
                            st.session_state[report_state_key]["content"] = report_txt
                            st.rerun()
                        except Exception as e:
                            # 에러 시에도 백업 보고서 제공
                            backup_report = f"{url}\n\n{media} : \"{title}\"\n- 핵심 요약은 원문 참고\n- 상세 내용은 링크 확인 필요"
                            st.session_state[report_state_key]["generated"] = True
                            st.session_state[report_state_key]["content"] = backup_report
                            st.rerun()
            
            # 보고서가 생성된 경우 하단에 표시
            if st.session_state[report_state_key]["generated"]:
                st.markdown("#### 📋 생성된 보고서")
                st.markdown(
                    f"""<div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); 
                    border-radius: 8px; padding: 15px; margin: 10px 0; color: #e0e0e0; font-family: monospace; 
                    white-space: pre-wrap; line-height: 1.5;">{st.session_state[report_state_key]["content"]}</div>""", 
                    unsafe_allow_html=True
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

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------- 메인 루틴 -----------------------------
def main():
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
        # 메뉴가 변경되었을 때 모든 입력 관련 세션 상태 정리 (확장)
        keys_to_clear = [k for k in st.session_state.keys() 
                        if k.startswith(('issue_', 'media_search_', 'contact_search_', 'history_search_', 
                                       'news_view', 'widget_', 'text_input_', 'text_area_', 'selectbox_'))]
        for key in keys_to_clear:
            try:
                del st.session_state[key]
            except KeyError:
                pass  # 키가 없어도 무시
        
        # 메뉴 상태 즉시 업데이트
        st.session_state.current_menu = active
        
        # 입력창 완전 초기화를 위한 단일 리런 (조건부에서 무조건으로 변경)
        st.rerun()
    
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

if __name__ == "__main__":
    main()