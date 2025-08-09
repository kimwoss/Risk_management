"""
포스코인터내셔널 언론대응 보고서 생성 시스템
Streamlit 웹 애플리케이션
"""
import streamlit as st
import requests
from PIL import Image
import io
import json
import pandas as pd
from datetime import datetime
import os
from data_based_llm import DataBasedLLM
from llm_manager import LLMManager
from performance_monitor import PerformanceMonitor, PerformanceMetrics
from prompt_optimizer import PromptOptimizer
from adaptive_learning import AdaptiveLearner
from performance_enhancer import PerformanceEnhancer
import asyncio
import time

# 페이지 설정
st.set_page_config(
    page_title="포스코인터내셔널 언론대응 시스템",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    import streamlit as st
    st.markdown("""
    <style>
    /* CSS Version 2.0 - Enhanced Table Design */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');

    /* ====== App Base (다크 제네시스 무드) ====== */
    .stApp{
      background: radial-gradient(ellipse at center, #121212 0%, #0b0b0b 100%) !important;
      font-family:'Noto Sans KR',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif !important;
      color:#e7e7e7 !important;
    }
    .block-container{
      max-width:1200px !important;
      padding-top:24px !important;            /* 상단 흰 띠 느낌 제거 */
      padding-bottom:32px !important;
      box-shadow: inset 1px 0 0 rgba(255,255,255,.07); /* 좌측 메뉴와의 얇은 세로 구분선 */
    }

    /* ====== Header ====== */
    .header-container{
      background: linear-gradient(135deg, rgba(20,20,20,.95), rgba(12,12,12,.98));
      border:1px solid rgba(212,175,55,.10);
      box-shadow: 0 25px 50px -12px rgba(0,0,0,.7), inset 0 1px 0 rgba(255,255,255,.03);
      border-radius: 6px;
      padding: 28px 24px;
      margin-bottom: 24px;
      position: relative; overflow: hidden;
      backdrop-filter: blur(12px);
    }
    .header-container::before{
      content:""; position:absolute; left:0; right:0; top:0; height:1px;
      background: linear-gradient(90deg, transparent, rgba(212,175,55,.35), transparent);
    }
    .header-title{
      color:#fff !important; font-size:2.25rem !important; font-weight:600 !important;
      letter-spacing:-.01em; line-height:1.2; text-align:center; margin:0;
    }
    .header-subtitle{
      color:#bdbdbd !important; font-size:.95rem !important; font-weight:400 !important;
      letter-spacing:.18em; text-transform:uppercase; text-align:center; margin-top:8px;
    }

    /* ====== Sidebar (안정 selector + Active/Hover 확실) ====== */
    [data-testid="stSidebar"]{
      background: linear-gradient(180deg, #141414 0%, #0f0f0f 100%) !important;
      border-right:1px solid rgba(255,255,255,.07) !important; /* 좌/중앙 구분선 */
    }
    .side-heading{
      color:#fff; font-weight:600; letter-spacing:.04em; padding:12px 8px 8px;
      border-bottom:1px solid rgba(255,255,255,.06); margin-bottom:8px;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] > div{ display:flex; gap:8px; flex-direction:column; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label{
      background:#151515; color:#bdbdbd; border:1px solid rgba(255,255,255,.08);
      border-radius:10px; padding:10px 12px; cursor:pointer; transition:.15s ease;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover{
      background:#1b1b1b; color:#eee; border-color: rgba(212,175,55,.35);
    }
    /* checked (두 방식 모두 대응) */
    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked),
    [data-testid="stSidebar"] [data-testid="stRadio"] input:checked + div + label{
      background:#222; color:#fff; border-color: rgba(212,175,55,.6);
      box-shadow: 0 0 0 1px rgba(212,175,55,.18) inset;
    }

    /* ====== Cards ====== */
    .card{
      background: linear-gradient(135deg, rgba(24,24,24,.65), rgba(14,14,14,.9));
      border:1px solid rgba(255,255,255,.08);
      border-radius: 6px; padding:20px 22px; margin-bottom:16px;
      box-shadow: 0 20px 40px -10px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.03);
      transition: .2s ease;
    }
    .card:hover{ border-color: rgba(212,175,55,.18); transform: translateY(-1px); }
    .input-card{ border-left:2px solid rgba(212,175,55,.36); }
    .result-card{ border-left:2px solid rgba(136,136,136,.36); }
    .card h3{ color:#fff !important; font-weight:600 !important; font-size:1.125rem !important; margin:0 0 12px 0; }

    /* ====== Inputs (쓰기감 강화) ====== */
    .stTextInput input, .stTextArea textarea{
      background: rgba(11,11,11,.82) !important; color:#fff !important;
      border:1px solid rgba(255,255,255,.10) !important; border-radius:6px !important;
      padding:12px 12px !important; font-size:14px !important; transition:.15s ease;
      caret-color: #D4AF37 !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder{ color: rgba(255,255,255,.38) !important; }
    .stTextInput input:focus, .stTextArea textarea:focus{
      border-color: rgba(212,175,55,.55) !important; box-shadow: 0 0 0 2px rgba(212,175,55,.16) !important;
    }
    /* Selectbox - 세련된 다크 디자인 */
    [data-testid="stSelectbox"] > div > div{
      background: linear-gradient(135deg, rgba(28,28,28,.95), rgba(18,18,18,.98)) !important; 
      border: 1px solid rgba(212,175,55,.25) !important;
      border-radius: 8px !important; 
      color: #ffffff !important; 
      font-weight: 500 !important;
      padding: 12px 16px !important;
      transition: all .2s ease !important;
      box-shadow: 0 4px 12px rgba(0,0,0,.15) !important;
    }
    [data-testid="stSelectbox"] > div > div:hover{
      border-color: rgba(212,175,55,.45) !important;
      box-shadow: 0 6px 20px rgba(0,0,0,.25), 0 0 0 1px rgba(212,175,55,.1) inset !important;
      background: linear-gradient(135deg, rgba(32,32,32,.95), rgba(22,22,22,.98)) !important;
    }
    [data-testid="stSelectbox"] > div:focus-within{
      box-shadow: 0 0 0 3px rgba(212,175,55,.2) !important; 
      border-color: rgba(212,175,55,.7) !important;
    }
    
    /* Selectbox 드롭다운 옵션들 */
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div{
      background: rgba(20,20,20,.98) !important;
      border: 1px solid rgba(212,175,55,.3) !important;
      border-radius: 8px !important;
      box-shadow: 0 8px 32px rgba(0,0,0,.4) !important;
    }
    
    /* 개별 옵션 스타일 */
    [data-testid="stSelectbox"] ul[role="listbox"] li{
      background: transparent !important;
      color: #e0e0e0 !important;
      padding: 12px 16px !important;
      transition: all .15s ease !important;
      border-bottom: 1px solid rgba(255,255,255,.05) !important;
    }
    [data-testid="stSelectbox"] ul[role="listbox"] li:hover{
      background: linear-gradient(90deg, rgba(212,175,55,.15), rgba(212,175,55,.08)) !important;
      color: #ffffff !important;
      border-left: 3px solid rgba(212,175,55,.6) !important;
    }
    [data-testid="stSelectbox"] ul[role="listbox"] li:last-child{
      border-bottom: none !important;
    }

    /* ====== Buttons ====== */
    .stButton > button{
      background:#131313 !important; color:#D4AF37 !important;
      border:1px solid rgba(212,175,55,.35) !important; border-radius:6px !important;
      padding:12px 20px !important; font-weight:500 !important; letter-spacing:.06em !important;
      transition:.18s ease; position:relative; overflow:hidden;
    }
    .stButton > button:hover{ color:#fff !important; border-color: rgba(212,175,55,.6) !important; box-shadow:0 10px 24px -8px rgba(212,175,55,.22); }
    .stButton > button:disabled{ opacity:.45 !important; color:#9a8a57 !important; border-color: rgba(212,175,55,.25) !important; }

    /* ====== Tables - 강력한 다크 스타일 적용 ====== */
    
    /* 모든 데이터프레임 컨테이너 */
    div[data-testid="stDataFrame"],
    div[data-testid="stDataFrame"] > div,
    .stDataFrame {
      background: linear-gradient(135deg, rgba(18,18,18,.95), rgba(12,12,12,.98)) !important;
      border: 1px solid rgba(212,175,55,.15) !important;
      border-radius: 12px !important;
      box-shadow: 0 8px 32px rgba(0,0,0,.3), inset 0 1px 0 rgba(255,255,255,.02) !important;
      overflow: hidden !important;
      margin: 8px 0 !important;
    }
    
    /* 모든 테이블 요소 */
    div[data-testid="stDataFrame"] table,
    .stDataFrame table,
    table.dataframe {
      background: transparent !important;
      color: #e8e8e8 !important;
      border-collapse: collapse !important;
      width: 100% !important;
      font-family: 'Noto Sans KR', sans-serif !important;
      border: none !important;
    }
    
    /* 모든 테이블 헤더 */
    div[data-testid="stDataFrame"] thead tr,
    .stDataFrame thead tr,
    table.dataframe thead tr {
      background: linear-gradient(90deg, rgba(212,175,55,.08), rgba(212,175,55,.12)) !important;
      border-bottom: 2px solid rgba(212,175,55,.4) !important;
    }
    
    div[data-testid="stDataFrame"] thead th,
    .stDataFrame thead th,
    table.dataframe thead th {
      color: #ffffff !important;
      font-weight: 600 !important;
      font-size: 16px !important;
      padding: 16px 20px !important;
      text-align: left !important;
      border: none !important;
      background: transparent !important;
      letter-spacing: 0.5px !important;
    }
    
    /* 모든 테이블 바디 행 */
    div[data-testid="stDataFrame"] tbody tr,
    .stDataFrame tbody tr,
    table.dataframe tbody tr {
      background: transparent !important;
      border-bottom: 1px solid rgba(255,255,255,.06) !important;
      transition: all 0.2s ease !important;
    }
    
    div[data-testid="stDataFrame"] tbody tr:hover,
    .stDataFrame tbody tr:hover,
    table.dataframe tbody tr:hover {
      background: linear-gradient(90deg, rgba(212,175,55,.05), rgba(212,175,55,.02)) !important;
      border-left: 3px solid rgba(212,175,55,.6) !important;
      transform: translateX(2px) !important;
    }
    
    div[data-testid="stDataFrame"] tbody tr:nth-child(even),
    .stDataFrame tbody tr:nth-child(even),
    table.dataframe tbody tr:nth-child(even) {
      background: rgba(255,255,255,.015) !important;
    }
    
    div[data-testid="stDataFrame"] tbody tr:nth-child(even):hover,
    .stDataFrame tbody tr:nth-child(even):hover,
    table.dataframe tbody tr:nth-child(even):hover {
      background: linear-gradient(90deg, rgba(212,175,55,.05), rgba(212,175,55,.02)) !important;
      border-left: 3px solid rgba(212,175,55,.6) !important;
      transform: translateX(2px) !important;
    }
    
    /* 모든 테이블 셀 */
    div[data-testid="stDataFrame"] tbody td,
    .stDataFrame tbody td,
    table.dataframe tbody td {
      color: #e8e8e8 !important;
      font-size: 15px !important;
      font-weight: 400 !important;
      padding: 14px 20px !important;
      border: none !important;
      vertical-align: middle !important;
      background: transparent !important;
    }
    
    /* 첫 번째 열 */
    div[data-testid="stDataFrame"] tbody td:first-child,
    .stDataFrame tbody td:first-child,
    table.dataframe tbody td:first-child {
      text-align: left !important;
      font-weight: 500 !important;
      color: #f0f0f0 !important;
    }
    
    /* 마지막 열 */
    div[data-testid="stDataFrame"] tbody td:last-child,
    .stDataFrame tbody td:last-child,
    table.dataframe tbody td:last-child {
      text-align: right !important;
      font-family: 'Courier New', monospace !important;
      color: rgba(212,175,55,.9) !important;
    }
    
    /* 두 번째 열 */
    div[data-testid="stDataFrame"] tbody td:nth-child(2),
    .stDataFrame tbody td:nth-child(2),
    table.dataframe tbody td:nth-child(2) {
      text-align: center !important;
    }

    /* ====== Typography ====== */
    h1,h2,h3,h4,h5,h6{ color:#fff !important; letter-spacing:-.01em !important; }
    p,div,span{ color:#cfcfcf !important; line-height:1.6 !important; }

    /* ====== Scrollbar ====== */
    ::-webkit-scrollbar{ width:6px; } 
    ::-webkit-scrollbar-track{ background:#0e0e0e; }
    ::-webkit-scrollbar-thumb{ background: rgba(212,175,55,.32); border-radius:3px; }
    ::-webkit-scrollbar-thumb:hover{ background: rgba(212,175,55,.5); }
    </style>
    
    <script>
    // 강력한 테이블 스타일 적용
    function forceTableStyling() {
        // 모든 데이터프레임 찾기
        const dataframes = document.querySelectorAll('[data-testid="stDataFrame"]');
        
        dataframes.forEach(function(df) {
            // 컨테이너 스타일링
            df.style.cssText = `
                background: linear-gradient(135deg, rgba(18,18,18,.95), rgba(12,12,12,.98)) !important;
                border: 1px solid rgba(212,175,55,.15) !important;
                border-radius: 12px !important;
                box-shadow: 0 8px 32px rgba(0,0,0,.3), inset 0 1px 0 rgba(255,255,255,.02) !important;
                overflow: hidden !important;
                margin: 8px 0 !important;
            `;
            
            // 내부 div 스타일링
            const innerDivs = df.querySelectorAll('div');
            innerDivs.forEach(function(div) {
                div.style.background = 'transparent !important';
                div.style.border = 'none !important';
            });
            
            // 테이블 스타일링
            const tables = df.querySelectorAll('table');
            tables.forEach(function(table) {
                table.style.cssText = `
                    background: transparent !important;
                    color: #e8e8e8 !important;
                    border-collapse: collapse !important;
                    width: 100% !important;
                    font-family: 'Noto Sans KR', sans-serif !important;
                    border: none !important;
                `;
                
                // 헤더 스타일링
                const headers = table.querySelectorAll('thead th');
                headers.forEach(function(th) {
                    th.style.cssText = `
                        color: #ffffff !important;
                        font-weight: 600 !important;
                        font-size: 16px !important;
                        padding: 16px 20px !important;
                        text-align: left !important;
                        border: none !important;
                        background: linear-gradient(90deg, rgba(212,175,55,.08), rgba(212,175,55,.12)) !important;
                        letter-spacing: 0.5px !important;
                        border-bottom: 2px solid rgba(212,175,55,.4) !important;
                    `;
                });
                
                // 행 스타일링
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(function(tr, index) {
                    tr.style.cssText = `
                        background: ${index % 2 === 0 ? 'transparent' : 'rgba(255,255,255,.015)'} !important;
                        border-bottom: 1px solid rgba(255,255,255,.06) !important;
                        transition: all 0.2s ease !important;
                    `;
                    
                    // 호버 효과
                    tr.addEventListener('mouseenter', function() {
                        this.style.cssText += `
                            background: linear-gradient(90deg, rgba(212,175,55,.05), rgba(212,175,55,.02)) !important;
                            border-left: 3px solid rgba(212,175,55,.6) !important;
                            transform: translateX(2px) !important;
                        `;
                    });
                    
                    tr.addEventListener('mouseleave', function() {
                        this.style.cssText = `
                            background: ${index % 2 === 0 ? 'transparent' : 'rgba(255,255,255,.015)'} !important;
                            border-bottom: 1px solid rgba(255,255,255,.06) !important;
                            transition: all 0.2s ease !important;
                            border-left: none !important;
                            transform: translateX(0px) !important;
                        `;
                    });
                    
                    // 셀 스타일링
                    const cells = tr.querySelectorAll('td');
                    cells.forEach(function(td, cellIndex) {
                        td.style.cssText = `
                            color: #e8e8e8 !important;
                            font-size: 15px !important;
                            font-weight: 400 !important;
                            padding: 14px 20px !important;
                            border: none !important;
                            vertical-align: middle !important;
                            background: transparent !important;
                        `;
                        
                        // 정렬 설정
                        if (cellIndex === 0) {
                            td.style.textAlign = 'left';
                            td.style.fontWeight = '500';
                            td.style.color = '#f0f0f0';
                        } else if (cellIndex === cells.length - 1) {
                            td.style.textAlign = 'right';
                            td.style.fontFamily = 'Courier New, monospace';
                            td.style.color = 'rgba(212,175,55,.9)';
                        } else {
                            td.style.textAlign = 'center';
                        }
                    });
                });
            });
        });
    }
    
    // 페이지 로드 시 실행
    document.addEventListener('DOMContentLoaded', forceTableStyling);
    
    // 주기적으로 실행 (동적 콘텐츠 대응)
    setInterval(forceTableStyling, 1000);
    
    // MutationObserver로 DOM 변경 감지
    const observer = new MutationObserver(forceTableStyling);
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    </script>
    """, unsafe_allow_html=True)


def load_logo():
    """포스코인터내셔널 로고 로드"""
    try:
        # 포스코인터내셔널 공식 로고 URL
        logo_url = "https://www.poscointl.com/images/main/logo_header.png"
        
        response = requests.get(logo_url, timeout=10)
        if response.status_code == 200:
            logo_image = Image.open(io.BytesIO(response.content))
            return logo_image
        else:
            # 로고 로드 실패 시 대체 텍스트
            return None
    except Exception:
        return None

def load_data():
    """데이터 로드 및 캐싱"""
    if 'data_loaded' not in st.session_state:
        try:
            # master_data.json 로드
            with open('data/master_data.json', 'r', encoding='utf-8') as f:
                master_data = json.load(f)
            
            # 부서 목록 추출
            departments = list(master_data.get('departments', {}).keys())
            
            st.session_state.master_data = master_data
            st.session_state.departments = departments
            st.session_state.data_loaded = True
            
        except Exception as e:
            st.error(f"데이터 로드 실패: {str(e)}")
            st.session_state.departments = []

def search_media_info(media_name):
    """언론사 정보 검색"""
    try:
        with open('data/master_data.json', 'r', encoding='utf-8') as f:
            master_data = json.load(f)
        
        media_contacts = master_data.get('media_contacts', {})
        
        # 정확한 매칭 먼저 시도
        if media_name in media_contacts:
            media_data = media_contacts[media_name]
            # 표준 구조로 변환
            return {
                'name': media_name,
                'type': media_data.get('구분', 'N/A'),
                'contact_person': media_data.get('담당자', 'N/A'),
                'reporters': media_data.get('출입기자', []),
                'raw_data': media_data  # 원본 데이터 보존
            }
        
        # 부분 매칭 시도
        for media_key, media_info in media_contacts.items():
            if media_name.lower() in media_key.lower() or media_key.lower() in media_name.lower():
                return {
                    'name': media_key,
                    'type': media_info.get('구분', 'N/A'),
                    'contact_person': media_info.get('담당자', 'N/A'),
                    'reporters': media_info.get('출입기자', []),
                    'raw_data': media_info
                }
        
        return None
        
    except Exception as e:
        st.error(f"언론사 정보 검색 중 오류: {str(e)}")
        return None

def get_contact_info():
    """담당자 정보 반환"""
    contact_info = {
        "주관부서": {
            "부서명": "커뮤니케이션실 – 홍보그룹",
            "담당자": [
                {"성명": "허성형", "직책": "상무", "사무실번호": "02-759-2052"},
                {"성명": "손창호", "직책": "상무보", "사무실번호": "02-3457-2275"},
                {"성명": "심원보", "직책": "리더", "사무실번호": "02-3457-2065"},
                {"성명": "이인규", "직책": "과장", "사무실번호": "02-3457-2147"},
                {"성명": "김우현", "직책": "과장", "사무실번호": "02-3457-2090"},
                {"성명": "안성민", "직책": "과장", "사무실번호": "02-3457-2077"}
            ]
        },
        "협의체_참여부서": [
            {"부서명": "경영전략그룹", "성명": "서유리", "직책": "리더", "사무실번호": "02-759-3793"},
            {"부서명": "지속가능경영그룹", "성명": "이승진", "직책": "리더", "사무실번호": "02-759-0918"},
            {"부서명": "법인지사관리그룹", "성명": "이종일", "직책": "리더", "사무실번호": "02-759-2398"},
            {"부서명": "IR그룹", "성명": "유근석", "직책": "리더", "사무실번호": "02-759-3647"},
            {"부서명": "HR그룹", "성명": "권택현", "직책": "리더", "사무실번호": "02-759-3681"},
            {"부서명": "대외협력그룹", "성명": "고영택", "직책": "차장", "사무실번호": "02-3457-2089"},
            {"부서명": "철강사업운영섹션", "성명": "김요섭", "직책": "리더", "사무실번호": "02-759-3866"},
            {"부서명": "소재바이오사업운영섹션", "성명": "김준표", "직책": "리더", "사무실번호": "02-759-2309"},
            {"부서명": "에너지정책그룹", "성명": "왕희훈", "직책": "리더", "사무실번호": "02-3457-2130"},
            {"부서명": "에너지행정지원그룹", "성명": "홍성규", "직책": "리더", "사무실번호": "032-550-8270"},
            {"부서명": "가스사업운영섹션", "성명": "김승모", "직책": "부장", "사무실번호": "02-759-2288"},
            {"부서명": "포스코모빌리티솔루션", "성명": "엄유나", "직책": "과장", "사무실번호": "041-580-1483"},
            {"부서명": "삼척블루파워", "성명": "장재영", "직책": "과장", "사무실번호": "033-570-0709"}
        ]
    }
    return contact_info

def get_filter_options():
    """필터 옵션을 위한 데이터 로드"""
    try:
        df = pd.read_csv('data/언론대응내역.csv', encoding='utf-8')
        
        # 연도 옵션 추출
        years = sorted(df['발생 일시'].astype(str).str[:4].unique(), reverse=True)
        year_options = ["전체"] + years
        
        # 단계 옵션 추출
        stages = df['단계'].unique()
        stage_options = ["전체"] + sorted([stage for stage in stages if pd.notna(stage)])
        
        return year_options, stage_options
        
    except Exception as e:
        st.error(f"필터 옵션 로드 중 오류: {str(e)}")
        return ["전체"], ["전체"]

def simple_filter_search(year_filter, stage_filter, keyword_search):
    """간단한 필터 기반 검색"""
    try:
        df = pd.read_csv('data/언론대응내역.csv', encoding='utf-8')
        
        conditions = []
        search_explanation = []
        
        # 연도 필터
        if year_filter != "전체":
            year_condition = df['발생 일시'].astype(str).str.startswith(year_filter + '-')
            conditions.append(year_condition)
            search_explanation.append(f"{year_filter}년")
        
        # 단계 필터
        if stage_filter != "전체":
            stage_condition = df['단계'].astype(str).str.strip() == stage_filter
            conditions.append(stage_condition)
            search_explanation.append(f"{stage_filter} 단계")
        
        # 키워드 검색 (이슈 발생 보고 내용에서)
        if keyword_search.strip():
            keywords = [kw.strip() for kw in keyword_search.split() if kw.strip()]
            if keywords:
                keyword_conditions = []
                for keyword in keywords:
                    # 이슈 발생 보고 컬럼에서만 검색
                    keyword_condition = df['이슈 발생 보고'].astype(str).str.contains(keyword, case=False, na=False)
                    keyword_conditions.append(keyword_condition)
                
                # 모든 키워드가 포함된 것만 검색 (AND 조건)
                if keyword_conditions:
                    combined_keyword_condition = keyword_conditions[0]
                    for cond in keyword_conditions[1:]:
                        combined_keyword_condition = combined_keyword_condition & cond
                    conditions.append(combined_keyword_condition)
                    search_explanation.append(f"키워드: {', '.join(keywords)}")
        
        # 모든 조건을 AND로 결합
        if conditions:
            final_condition = conditions[0]
            for condition in conditions[1:]:
                final_condition = final_condition & condition
            search_results = df[final_condition]
        else:
            search_results = df
        
        explanation = f"필터 조건: {', '.join(search_explanation)}" if search_explanation else "전체 데이터"
        
        return search_results, explanation
        
    except Exception as e:
        st.error(f"검색 중 오류: {str(e)}")
        return pd.DataFrame(), f"검색 중 오류가 발생했습니다: {str(e)}"

def search_response_history(search_query):
    """개선된 기존 대응 이력 검색"""
    try:
        df = pd.read_csv('data/언론대응내역.csv', encoding='utf-8')
        
        if search_query.strip() == "":
            return df
        
        # 검색어를 공백과 쉼표로 분리하여 개별 키워드로 처리
        keywords = [keyword.strip() for keyword in search_query.replace(',', ' ').split() if keyword.strip()]
        
        if not keywords:
            return df
        
        # 각 키워드별로 검색 조건 생성
        search_conditions = []
        debug_info = []  # 디버그 정보
        
        for keyword in keywords:
            # 연도 검색 개선 (2022, 2023, 2024, 2025 등) - 정확한 매칭
            if keyword.isdigit() and len(keyword) == 4:
                year_condition = df['발생 일시'].astype(str).str.startswith(keyword + '-')
                search_conditions.append(year_condition)
                debug_info.append(f"연도 검색: {keyword}")
            
            # 월 검색 개선 (1월, 01, 05월 등) - 연도와 구분하기 위해 더 정확한 조건 사용
            elif '월' in keyword:
                # '5월' -> '05' 또는 '-05-' 형태로 검색
                month_num = keyword.replace('월', '').strip()
                if month_num.isdigit() and 1 <= int(month_num) <= 12:
                    month_num = month_num.zfill(2)  # 01, 02 형태로 변환
                    month_condition = df['발생 일시'].astype(str).str.contains(f'-{month_num}-', case=False, na=False)
                    search_conditions.append(month_condition)
                    debug_info.append(f"월 검색: {keyword} -> -{month_num}-")
            # 2자리 월 패턴 (01-12) - 하지만 4자리 연도는 제외
            elif keyword.isdigit() and len(keyword) == 2 and 1 <= int(keyword) <= 12:
                month_condition = df['발생 일시'].astype(str).str.contains(f'-{keyword}-', case=False, na=False)
                search_conditions.append(month_condition)
                debug_info.append(f"월 검색 (2자리): {keyword}")
            
            # 단계별 검색 개선 (위기, 경보, 주의, 관심) - 정확한 매칭
            elif keyword in ['위기', '경보', '주의', '관심']:
                stage_condition = df['단계'].astype(str).str.strip() == keyword
                search_conditions.append(stage_condition)
                debug_info.append(f"단계 검색: {keyword}")
            
            # 발생 유형 검색 개선
            elif keyword in ['언론문의', '언론 문의', '보도자료', '기획기사', '기획자료']:
                type_condition = df['발생 유형'].astype(str).str.contains(keyword, case=False, na=False)
                search_conditions.append(type_condition)
                debug_info.append(f"유형 검색: {keyword}")
            
            # 사업 분야별 키워드 매핑
            elif keyword in ['식량', '농업', '팜', '팜유', '바이오']:
                # 식량/농업 관련 키워드는 부서명과 내용에서 확장 검색
                food_keywords = ['식량', '팜', '팜유', '바이오', '농업', '농협', '곡물', '우크라이나', '탄자니아']
                food_conditions = []
                for food_keyword in food_keywords:
                    food_condition = df.astype(str).apply(
                        lambda row: row.str.contains(food_keyword, case=False, na=False).any(), 
                        axis=1
                    )
                    food_conditions.append(food_condition)
                
                # 식량 관련 키워드 중 하나라도 매치되면 포함 (OR 조건)
                combined_food_condition = food_conditions[0]
                for condition in food_conditions[1:]:
                    combined_food_condition = combined_food_condition | condition
                
                search_conditions.append(combined_food_condition)
                debug_info.append(f"식량/농업 확장 검색: {keyword}")
                
            # 일반 텍스트 검색 - 모든 컬럼에서 검색
            else:
                general_condition = df.astype(str).apply(
                    lambda row: row.str.contains(keyword, case=False, na=False).any(), 
                    axis=1
                )
                search_conditions.append(general_condition)
                debug_info.append(f"일반 검색: {keyword}")
        
        # 디버그 정보 출력 (AI 검색에서는 항상 표시)
        if search_explanation:
            st.info(f"🔍 적용된 검색 조건: {', '.join(search_explanation)}")
        
        # 키워드 검색에서의 디버그 정보 (개발용)
        if st.session_state.get('debug_mode', False):
            st.info(f"검색 조건: {', '.join(debug_info)}")
        
        # 모든 키워드 조건을 AND로 결합 (모든 키워드가 포함된 결과만)
        if search_conditions:
            final_condition = search_conditions[0]
            for condition in search_conditions[1:]:
                final_condition = final_condition & condition
            
            search_results = df[final_condition]
        else:
            search_results = df
        
        return search_results
        
    except Exception as e:
        st.error(f"대응 이력 검색 중 오류: {str(e)}")
        return pd.DataFrame()

def analyze_response_history(df, query):
    """대응 이력 분석"""
    try:
        analysis = {}
        
        # 연도별 분석
        if '년' in query or '월' in query:
            # 날짜 컬럼이 있다면 연도/월별 분석
            if '대응일자' in df.columns:
                df['대응일자'] = pd.to_datetime(df['대응일자'], errors='coerce')
                df['년도'] = df['대응일자'].dt.year
                df['월'] = df['대응일자'].dt.month
                
                analysis['연도별_통계'] = df['년도'].value_counts().to_dict()
                analysis['월별_통계'] = df['월'].value_counts().to_dict()
        
        # 대응 단계별 분석
        if '대응단계' in df.columns:
            analysis['대응단계별_통계'] = df['대응단계'].value_counts().to_dict()
        
        # 언론사별 분석
        if '언론사' in df.columns:
            analysis['언론사별_통계'] = df['언론사'].value_counts().head(10).to_dict()
        
        # 이슈 유형별 분석
        if '이슈유형' in df.columns:
            analysis['이슈유형별_통계'] = df['이슈유형'].value_counts().to_dict()
        
        return analysis
        
    except Exception as e:
        st.error(f"대응 이력 분석 중 오류: {str(e)}")
        return {}

def generate_issue_report(media_name, reporter_name, issue_description):
    """완전한 8단계 프로세스를 사용하여 이슈 발생 보고서 생성"""
    start_time = time.time()
    
    try:
        # 성능 모니터링 및 최적화 시스템 초기화
        monitor = PerformanceMonitor()
        enhancer = PerformanceEnhancer()
        
        # DataBasedLLM 초기화
        data_llm = DataBasedLLM()
        
        # Enhanced 모드로 8단계 프로세스 실행 (최적화된 기본값)
        response = data_llm.generate_comprehensive_issue_report(
            media_name, 
            reporter_name, 
            issue_description
        )
        
        # 성능 지표 기록
        processing_time = time.time() - start_time
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time,
            report_length=len(response) if response else 0,
            issue_category="이슈",  # 실제 구현에서는 이슈 분석 결과 사용
            departments_count=3  # 실제 구현에서는 매핑된 부서 수 사용
        )
        monitor.log_performance(metrics)
        
        return response
        
    except Exception as e:
        # 에러 발생 시에도 성능 지표 기록
        processing_time = time.time() - start_time
        metrics = PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time,
            report_length=0,
            error_count=1
        )
        monitor.log_performance(metrics)
        
        return f"보고서 생성 중 오류가 발생했습니다: {str(e)}"

def get_enhanced_analysis(media_name, reporter_name, issue_description):
    """개선된 분석 정보 제공"""
    try:
        data_llm = DataBasedLLM()
        
        analysis = {
            'media_info': None,
            'departments': [],
            'crisis_level': None,
            'past_cases': []
        }
        
        # 1. 언론사별 맞춤 정보 
        try:
            analysis['media_info'] = data_llm.get_media_specific_info(media_name, reporter_name)
        except Exception as e:
            st.warning(f"언론사 정보 조회 중 오류: {str(e)}")
            analysis['media_info'] = None
        
        # 2. 개선된 부서 매핑
        try:
            analysis['departments'] = data_llm.get_relevant_departments(issue_description)
        except Exception as e:
            st.warning(f"부서 정보 조회 중 오류: {str(e)}")
            analysis['departments'] = []
        
        # 3. AI 기반 위기 단계 판단
        try:
            analysis['crisis_level'] = data_llm._assess_crisis_level(issue_description)
        except Exception as e:
            st.warning(f"위기 단계 판단 중 오류: {str(e)}")
            analysis['crisis_level'] = "2단계 (주의)"
        
        # 4. 과거 사례 검색
        try:
            analysis['past_cases'] = data_llm.search_media_responses(issue_description, limit=3)
        except Exception as e:
            st.warning(f"과거 사례 검색 중 오류: {str(e)}")
            analysis['past_cases'] = []
        
        return analysis
        
    except Exception as e:
        st.error(f"분석 정보 생성 중 오류: {str(e)}")
        return None

def main():
    """메인 애플리케이션"""

    # CSS / 데이터 (강제 새로고침 적용)
    load_css()
    load_data()
    

    # 헤더 로고
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo = load_logo()
        if logo:
            st.image(logo, width=300)
        else:
            # 인라인 스타일 대신 클래스 사용(테마와 톤 맞춤)
            st.markdown(
                '<div class="logo-container"><h1 class="header-title">POSCO INTERNATIONAL</h1></div>',
                unsafe_allow_html=True
            )

    # 메인 헤더
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">위기관리커뮤니케이션 AI 자동화 솔루션</h1>
        <p class="header-subtitle">AI 기반 스마트 언론대응 솔루션</p>
    </div>
    """, unsafe_allow_html=True)

    # ===== 사이드바 (여기까지만 사이드바에 머물러야 함) =====
    with st.sidebar:
        st.markdown('<div class="side-heading">메뉴</div>', unsafe_allow_html=True)
        menu_option = st.radio(
            "카테고리 선택",
            ["이슈발생보고 생성", "언론사 정보 검색", "담당자 정보 검색", "기존대응이력 검색"],
            index=0,
            label_visibility="collapsed",
            key="menu_radio"
        )
        
        # 성능 상태 표시
        st.markdown('<div class="side-heading">시스템 상태</div>', unsafe_allow_html=True)
        try:
            monitor = PerformanceMonitor()
            daily_metrics = monitor.get_daily_metrics()
            
            if daily_metrics['total_reports'] > 0:
                st.metric("오늘 처리량", f"{daily_metrics['total_reports']}건")
                st.metric("평균 처리시간", f"{daily_metrics['avg_processing_time']:.1f}초")
                st.metric("평균 만족도", f"{daily_metrics['avg_user_rating']:.1f}/5.0")
            else:
                st.info("📊 오늘 처리된 보고서가 없습니다.")
        except Exception as e:
            st.error(f"상태 조회 실패: {e}")
    # ===== 여기서부터는 메인 영역 =====

    # 1) 이슈발생보고 생성
    if menu_option == "이슈발생보고 생성":
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown('<div class="card input-card"><h3>이슈 정보 입력</h3></div>', unsafe_allow_html=True)

            selected_media = st.text_input(
                "언론사명",
                placeholder="언론사명을 입력하세요 (예: 조선일보, 동아일보, 한국경제 등)",
                key="media_input"
            )
            selected_reporter = st.text_input(
                "기자명",
                placeholder="담당 기자명을 입력하세요",
                key="reporter_input"
            )
            issue_description = st.text_area(
                "발생 이슈",
                placeholder="발생한 이슈에 대해 상세히 기술해주세요...",
                height=150,
                key="issue_input"
            )

            generate_button = st.button("이슈발생보고 생성", key="generate_btn", use_container_width=True)

        with col2:
            st.markdown('<div class="card result-card"><h3>생성 결과</h3></div>', unsafe_allow_html=True)

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
                        st.markdown("### 생성된 이슈 발생 보고서")
                        st.write(report)

                    if 'report' in locals():
                        report_data = f"""
포스코인터내셔널 언론대응 이슈 발생 보고서
================================

생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
언론사: {selected_media}
기자명: {selected_reporter}
발생 이슈: {issue_description}

보고서 내용:
{report}
"""
                        st.download_button(
                            label="보고서 다운로드",
                            data=report_data,
                            file_name=f"이슈발생보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
            else:
                st.info("좌측에서 정보를 입력하고 원하는 분석 버튼을 클릭해주세요.")

    # 2) 언론사 정보 검색
    elif menu_option == "언론사 정보 검색":
        st.markdown("### 언론사 정보 조회")
        media_search = st.text_input("언론사명을 입력하세요:", key="media_search", placeholder="예: 조선일보, 중앙일보, 한국경제 등")

        if st.button("언론사 정보 조회", key="media_info_btn"):
            if media_search:
                # 테이블 디자인 강제 적용 (담당자 정보와 동일)
                table_style = """
                <style id="media-table-style">
                /* 언론사 정보 테이블 전용 디자인 */
                div[data-testid="stDataFrame"] {
                    border: none !important;
                    background: transparent !important;
                    box-shadow: none !important;
                }
                div[data-testid="stDataFrame"] > div {
                    border: none !important;
                    background: transparent !important;
                }
                div[data-testid="stDataFrame"] table {
                    border-collapse: collapse !important;
                    color: #ddd !important;
                    font-size: 15px !important;
                    background: transparent !important;
                    width: 100% !important;
                }
                div[data-testid="stDataFrame"] table thead tr {
                    background: transparent !important;
                }
                div[data-testid="stDataFrame"] table thead th {
                    color: #fff !important;
                    font-weight: bold !important;
                    font-size: 16px !important;
                    padding: 14px 16px !important;
                    border: none !important;
                    border-bottom: 2px solid #444 !important;
                    background: transparent !important;
                    text-align: left !important;
                }
                div[data-testid="stDataFrame"] table tbody tr {
                    background: transparent !important;
                    border-bottom: 1px solid #333 !important;
                    transition: background-color 0.15s ease !important;
                }
                div[data-testid="stDataFrame"] table tbody tr:hover {
                    background: rgba(255,255,255,0.05) !important;
                }
                div[data-testid="stDataFrame"] table tbody tr:nth-child(even) {
                    background: transparent !important;
                }
                div[data-testid="stDataFrame"] table tbody tr:nth-child(even):hover {
                    background: rgba(255,255,255,0.05) !important;
                }
                div[data-testid="stDataFrame"] table tbody td {
                    color: #ddd !important;
                    font-size: 15px !important;
                    padding: 14px 16px !important;
                    border: none !important;
                    border-bottom: 1px solid #333 !important;
                    vertical-align: middle !important;
                    background: transparent !important;
                }
                div[data-testid="stDataFrame"] table tbody td:first-child {
                    text-align: left !important;
                }
                div[data-testid="stDataFrame"] table tbody td:last-child {
                    text-align: right !important;
                }
                div[data-testid="stDataFrame"] table tbody td:nth-child(2) {
                    text-align: center !important;
                }
                </style>
                """
                st.markdown(table_style, unsafe_allow_html=True)
                
                # JavaScript로 강제 스타일 적용
                js_code = """
                <script>
                setTimeout(function() {
                    // 모든 데이터프레임 찾기
                    const dataframes = document.querySelectorAll('[data-testid="stDataFrame"]');
                    dataframes.forEach(function(df) {
                        // 컨테이너 스타일
                        df.style.border = 'none';
                        df.style.background = 'transparent';
                        df.style.boxShadow = 'none';
                        
                        // 테이블 찾기
                        const table = df.querySelector('table');
                        if (table) {
                            table.style.borderCollapse = 'collapse';
                            table.style.color = '#ddd';
                            table.style.fontSize = '15px';
                            table.style.background = 'transparent';
                            
                            // 헤더 스타일
                            const headers = table.querySelectorAll('thead th');
                            headers.forEach(function(th) {
                                th.style.color = '#fff';
                                th.style.fontWeight = 'bold';
                                th.style.fontSize = '16px';
                                th.style.padding = '14px 16px';
                                th.style.border = 'none';
                                th.style.borderBottom = '2px solid #444';
                                th.style.background = 'transparent';
                                th.style.textAlign = 'left';
                            });
                            
                            // 데이터 행 스타일
                            const rows = table.querySelectorAll('tbody tr');
                            rows.forEach(function(tr, index) {
                                tr.style.background = 'transparent';
                                tr.style.borderBottom = '1px solid #333';
                                tr.style.transition = 'background-color 0.15s ease';
                                
                                // 호버 이벤트
                                tr.addEventListener('mouseenter', function() {
                                    this.style.background = 'rgba(255,255,255,0.05)';
                                });
                                tr.addEventListener('mouseleave', function() {
                                    this.style.background = 'transparent';
                                });
                                
                                // 셀 스타일
                                const cells = tr.querySelectorAll('td');
                                cells.forEach(function(td, cellIndex) {
                                    td.style.color = '#ddd';
                                    td.style.fontSize = '15px';
                                    td.style.padding = '14px 16px';
                                    td.style.border = 'none';
                                    td.style.borderBottom = '1px solid #333';
                                    td.style.background = 'transparent';
                                    
                                    // 정렬
                                    if (cellIndex === 0) td.style.textAlign = 'left';
                                    else if (cellIndex === cells.length - 1) td.style.textAlign = 'right';
                                    else td.style.textAlign = 'center';
                                });
                            });
                        }
                    });
                }, 500); // 0.5초 후 실행
                </script>
                """
                st.markdown(js_code, unsafe_allow_html=True)
                
                with st.spinner("언론사 정보를 검색하고 있습니다..."):
                    media_info = search_media_info(media_search)
                    if media_info:
                        st.success(f"'{media_search}' 언론사 정보를 찾았습니다!")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("#### 기본 정보")
                            st.info(f"""
**언론사명**: {media_info.get('name', 'N/A')}
**분류**: {media_info.get('type', 'N/A')}
**담당자**: {media_info.get('contact_person', 'N/A')}
**출입기자 수**: {len(media_info.get('reporters', []))}명
""")
                        with col2:
                            st.markdown("#### 출입기자 정보")
                            reporters = media_info.get('reporters', [])
                            if reporters:
                                # 출입기자 테이블 형태로 표시
                                reporter_data = []
                                for i, reporter in enumerate(reporters, 1):
                                    # 기자 이름에서 연락처 정보 분리 (있는 경우)
                                    if isinstance(reporter, dict):
                                        reporter_data.append([
                                            reporter.get('name', 'N/A'),
                                            reporter.get('position', 'N/A'),
                                            reporter.get('contact', 'N/A')
                                        ])
                                    else:
                                        # 문자열인 경우 이름만 표시
                                        reporter_data.append([reporter, "기자", "N/A"])
                                
                                reporter_df = pd.DataFrame(
                                    reporter_data,
                                    columns=["기자명", "직책", "연락처"]
                                )
                                st.dataframe(reporter_df, use_container_width=True)
                            else:
                                st.write("등록된 출입기자 정보가 없습니다.")
                        with st.expander("상세 데이터 (개발자용)"):
                            st.json(media_info.get('raw_data', {}))
                    else:
                        st.warning(f"'{media_search}' 언론사 정보를 찾을 수 없습니다.")
                        st.info("등록되지 않은 언론사일 수 있습니다. 정확한 언론사명을 입력해주세요.")
                        with st.expander("등록된 언론사 목록 확인"):
                            try:
                                with open('data/master_data.json', 'r', encoding='utf-8') as f:
                                    master_data = json.load(f)
                                media_list = list(master_data.get('media_contacts', {}).keys())
                                st.markdown("**등록된 언론사 목록:**")
                                cols = st.columns(3)
                                for i, media in enumerate(media_list):
                                    cols[i % 3].write(f"• {media}")
                            except Exception as e:
                                st.error(f"언론사 목록 로드 실패: {str(e)}")
            else:
                st.error("언론사명을 입력해주세요.")

    # 3) 담당자 정보 검색
    elif menu_option == "담당자 정보 검색":
        st.markdown("### 담당자 정보")
        contact_info = get_contact_info()

        st.markdown("#### 주관부서: 커뮤니케이션실 – 홍보그룹")
        
        main_dept_df = pd.DataFrame(
            [[p["성명"], p["직책"], p["사무실번호"]] for p in contact_info["주관부서"]["담당자"]],
            columns=["성명", "직책", "사무실 번호"]
        )
        st.dataframe(main_dept_df, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 협의체 참여 현업 부서 담당자 (13개 부서)")
        coop_dept_df = pd.DataFrame(
            [[d["부서명"], d["성명"], d["직책"], d["사무실번호"]] for d in contact_info["협의체_참여부서"]],
            columns=["부서명", "성명", "직책", "사무실 번호"]
        )
        st.dataframe(coop_dept_df, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 담당자 검색")
        c1, c2 = st.columns(2)
        with c1:
            search_name = st.text_input("담당자 성명으로 검색:", key="contact_name_search")
        with c2:
            search_dept = st.text_input("부서명으로 검색:", key="contact_dept_search")

        if search_name or search_dept:
            filtered = []
            for p in contact_info["주관부서"]["담당자"]:
                if (not search_name or search_name in p["성명"]) and (not search_dept or search_dept in contact_info["주관부서"]["부서명"]):
                    filtered.append({"부서명": contact_info["주관부서"]["부서명"], "성명": p["성명"], "직책": p["직책"], "사무실번호": p["사무실번호"]})
            for d in contact_info["협의체_참여부서"]:
                if (not search_name or search_name in d["성명"]) and (not search_dept or search_dept in d["부서명"]):
                    filtered.append(d)
            if filtered:
                st.success(f"{len(filtered)}명의 담당자를 찾았습니다.")
                st.dataframe(pd.DataFrame(filtered), use_container_width=True)
            else:
                st.warning("해당 조건에 맞는 담당자를 찾을 수 없습니다.")

    # 4) 기존대응이력 검색
    elif menu_option == "기존대응이력 검색":
        st.markdown("### 기존 대응 이력 검색")
        
        # 필터 옵션 로드
        year_options, stage_options = get_filter_options()
        
        # 3개 열로 필터 배치
        col1, col2, col3 = st.columns(3)
        
        with col1:
            year_filter = st.selectbox(
                "연도 선택",
                options=year_options,
                key="year_filter"
            )
        
        with col2:
            stage_filter = st.selectbox(
                "단계 선택", 
                options=stage_options,
                key="stage_filter"
            )
        
        with col3:
            keyword_search = st.text_input(
                "키워드 검색",
                placeholder="이슈 내용에서 검색",
                key="keyword_search"
            )
        
        # 검색 버튼과 전체 보기
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            search_button = st.button("검색하기", key="filter_search_btn")
        with col_btn2:
            show_all_button = st.button("전체 보기", key="show_all_btn")

        if search_button or show_all_button:
            with st.spinner("대응 이력을 검색하고 있습니다..."):
                if show_all_button:
                    # 전체 보기 - 모든 필터 무시
                    search_results, search_explanation = simple_filter_search("전체", "전체", "")
                else:
                    # 일반 검색
                    search_results, search_explanation = simple_filter_search(year_filter, stage_filter, keyword_search)
                st.info(search_explanation)

                if not search_results.empty:
                    st.markdown(f"#### 검색 결과: 총 {len(search_results)}건")
                    
                    # 간단한 통계 정보
                    if len(search_results) > 0:
                        col_stat1, col_stat2, col_stat3 = st.columns(3)
                        
                        with col_stat1:
                            years = search_results['발생 일시'].astype(str).str[:4].value_counts()
                            st.metric("연도 분포", f"{len(years)}개 연도")
                        
                        with col_stat2:
                            stages = search_results['단계'].value_counts()
                            st.metric("단계 분포", f"{len(stages)}개 단계")
                        
                        with col_stat3:
                            types = search_results['발생 유형'].value_counts() 
                            st.metric("유형 분포", f"{len(types)}개 유형")

                    st.markdown("#### 검색 결과")
                    
                    # 페이징 처리
                    items_per_page = 20
                    total_pages = len(search_results) // items_per_page + (1 if len(search_results) % items_per_page > 0 else 0)
                    
                    if total_pages > 1:
                        page = st.selectbox("페이지 선택:", range(1, total_pages + 1), key="page_select")
                        start_idx = (page - 1) * items_per_page
                        end_idx = start_idx + items_per_page
                        display_data = search_results.iloc[start_idx:end_idx]
                    else:
                        display_data = search_results
                    
                    st.dataframe(display_data, use_container_width=True)

                    # 다운로드 버튼
                    csv_data = search_results.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="검색 결과 다운로드 (CSV)",
                        data=csv_data,
                        file_name=f"대응이력_검색결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning("검색 조건에 맞는 대응 이력을 찾을 수 없습니다.")
                    st.info("다른 연도, 단계 또는 키워드로 검색해보세요.")



if __name__ == "__main__":
    main()
