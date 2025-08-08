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

# 페이지 설정
st.set_page_config(
    page_title="포스코인터내셔널 언론대응 시스템",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일 - 프리미엄 디자인
def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@100;300;400;500;700&display=swap');
    
    /* 전체 배경 및 기본 스타일 */
    .main {
        background: radial-gradient(ellipse at center, #1A1A1A 0%, #0B0B0B 100%);
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #FFFFFF;
        min-height: 100vh;
    }
    
    /* 전체 앱 배경 */
    .stApp {
        background: radial-gradient(ellipse at center, #1A1A1A 0%, #0B0B0B 100%);
    }
    
    /* 메인 컨테이너 */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* 헤더 스타일 */
    .header-container {
        background: linear-gradient(135deg, rgba(26, 26, 26, 0.95) 0%, rgba(11, 11, 11, 0.98) 100%);
        padding: 4rem 3rem;
        border-radius: 2px;
        border: 1px solid rgba(212, 175, 55, 0.1);
        box-shadow: 
            0 25px 50px -12px rgba(0, 0, 0, 0.8),
            0 0 0 1px rgba(212, 175, 55, 0.05),
            inset 0 1px 0 rgba(255, 255, 255, 0.02);
        margin-bottom: 4rem;
        backdrop-filter: blur(20px);
        position: relative;
        overflow: hidden;
    }
    
    .header-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.3), transparent);
    }
    
    .header-title {
        color: #FFFFFF;
        font-size: 3.2rem;
        font-weight: 100;
        text-align: center;
        margin: 0;
        letter-spacing: -0.02em;
        line-height: 1.1;
        text-shadow: 0 2px 40px rgba(0, 0, 0, 0.8);
    }
    
    .header-subtitle {
        color: #C0C0C0;
        font-size: 1.1rem;
        text-align: center;
        margin-top: 1.5rem;
        font-weight: 300;
        letter-spacing: 0.3em;
        text-transform: uppercase;
        opacity: 0.8;
    }
    
    /* 카드 스타일 */
    .card {
        background: linear-gradient(135deg, rgba(26, 26, 26, 0.6) 0%, rgba(17, 17, 17, 0.8) 100%);
        padding: 3rem;
        border-radius: 1px;
        border: 1px solid rgba(192, 192, 192, 0.08);
        margin-bottom: 2rem;
        box-shadow: 
            0 20px 40px -8px rgba(0, 0, 0, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        position: relative;
    }
    
    .card:hover {
        border-color: rgba(212, 175, 55, 0.15);
        box-shadow: 
            0 25px 50px -12px rgba(0, 0, 0, 0.7),
            0 0 0 1px rgba(212, 175, 55, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.03);
        transform: translateY(-2px);
    }
    
    .input-card {
        background: linear-gradient(135deg, rgba(26, 26, 26, 0.7) 0%, rgba(17, 17, 17, 0.9) 100%);
        border-left: 1px solid rgba(212, 175, 55, 0.3);
    }
    
    .result-card {
        background: linear-gradient(135deg, rgba(22, 22, 22, 0.7) 0%, rgba(15, 15, 15, 0.9) 100%);
        border-left: 1px solid rgba(136, 136, 136, 0.3);
    }
    
    /* 입력 필드 스타일 */
    .stSelectbox > div > div > div {
        background: rgba(11, 11, 11, 0.8) !important;
        border: 1px solid rgba(192, 192, 192, 0.1) !important;
        border-radius: 1px !important;
        color: #FFFFFF !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div > div:hover {
        border-color: rgba(212, 175, 55, 0.3) !important;
    }
    
    .stTextInput > div > div > input {
        background: rgba(11, 11, 11, 0.8) !important;
        border: 1px solid rgba(192, 192, 192, 0.1) !important;
        border-radius: 1px !important;
        color: #FFFFFF !important;
        font-size: 1rem;
        font-weight: 300;
        padding: 1rem !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(212, 175, 55, 0.4) !important;
        box-shadow: 0 0 0 1px rgba(212, 175, 55, 0.1) !important;
    }
    
    .stTextArea > div > div > textarea {
        background: rgba(11, 11, 11, 0.8) !important;
        border: 1px solid rgba(192, 192, 192, 0.1) !important;
        border-radius: 1px !important;
        color: #FFFFFF !important;
        font-size: 1rem;
        font-weight: 300;
        padding: 1rem !important;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        min-height: 150px !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(212, 175, 55, 0.4) !important;
        box-shadow: 0 0 0 1px rgba(212, 175, 55, 0.1) !important;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        background: transparent !important;
        color: #D4AF37 !important;
        border: 1px solid rgba(212, 175, 55, 0.3) !important;
        border-radius: 1px !important;
        padding: 1rem 2.5rem !important;
        font-size: 0.95rem !important;
        font-weight: 300 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(212, 175, 55, 0.1), transparent);
        transition: left 0.5s ease;
    }
    
    .stButton > button:hover {
        border-color: rgba(212, 175, 55, 0.5) !important;
        color: #FFFFFF !important;
        box-shadow: 
            0 10px 30px -5px rgba(212, 175, 55, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* 라벨 스타일 */
    label {
        color: #C0C0C0 !important;
        font-weight: 300 !important;
        font-size: 0.9rem !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 0.8rem !important;
    }
    
    /* 결과 영역 스타일 */
    .result-container {
        background: linear-gradient(135deg, rgba(17, 17, 17, 0.8) 0%, rgba(11, 11, 11, 0.9) 100%);
        padding: 3rem;
        border-radius: 1px;
        border: 1px solid rgba(136, 136, 136, 0.1);
        box-shadow: 
            0 20px 40px -8px rgba(0, 0, 0, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(20px);
    }
    
    .result-title {
        color: #FFFFFF;
        font-size: 1.3rem;
        font-weight: 300;
        margin-bottom: 2rem;
        letter-spacing: 0.02em;
    }
    
    .result-content {
        background: rgba(11, 11, 11, 0.4);
        padding: 2rem;
        border-radius: 1px;
        border: 1px solid rgba(192, 192, 192, 0.05);
        font-size: 1rem;
        line-height: 1.8;
        color: #C0C0C0;
        white-space: pre-wrap;
        font-weight: 300;
    }
    
    /* 사이드바 스타일 */
    .css-1d391kg {
        background: linear-gradient(180deg, rgba(17, 17, 17, 0.95) 0%, rgba(11, 11, 11, 0.98) 100%) !important;
        border-right: 1px solid rgba(192, 192, 192, 0.08) !important;
    }
    
    .css-1d391kg .css-17eq0hr {
        color: #FFFFFF !important;
    }
    
    /* 메트릭 카드 */
    .metric-card {
        background: linear-gradient(135deg, rgba(26, 26, 26, 0.6) 0%, rgba(17, 17, 17, 0.8) 100%);
        padding: 2rem;
        border-radius: 1px;
        text-align: center;
        border: 1px solid rgba(192, 192, 192, 0.08);
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: rgba(212, 175, 55, 0.15);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 100;
        color: #D4AF37;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: #888888;
        font-weight: 300;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    
    /* 성공/오류 메시지 */
    .success-message {
        background: linear-gradient(90deg, rgba(136, 136, 136, 0.2) 0%, rgba(136, 136, 136, 0.1) 100%);
        color: #C0C0C0;
        padding: 1.5rem;
        border-radius: 1px;
        border-left: 2px solid #888888;
        margin: 1.5rem 0;
        font-weight: 300;
    }
    
    .error-message {
        background: linear-gradient(90deg, rgba(100, 100, 100, 0.2) 0%, rgba(80, 80, 80, 0.1) 100%);
        color: #C0C0C0;
        padding: 1.5rem;
        border-radius: 1px;
        border-left: 2px solid #606060;
        margin: 1.5rem 0;
        font-weight: 300;
    }
    
    /* 로고 영역 */
    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 3rem;
        filter: brightness(0.9) contrast(1.1);
    }
    
    /* 로딩 애니메이션 */
    .loading {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 3rem 0;
    }
    
    .spinner {
        border: 1px solid rgba(192, 192, 192, 0.1);
        border-top: 1px solid #D4AF37;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        animation: spin 2s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* 데이터프레임 스타일 */
    .stDataFrame {
        background: rgba(11, 11, 11, 0.6) !important;
        border-radius: 1px !important;
        border: 1px solid rgba(192, 192, 192, 0.08) !important;
    }
    
    /* 애니메이션 효과 */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .card {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* 스크롤바 스타일 */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(11, 11, 11, 0.5);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(212, 175, 55, 0.3);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(212, 175, 55, 0.5);
    }
    
    /* 헤딩 스타일 */
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
        font-weight: 300 !important;
        letter-spacing: -0.01em !important;
    }
    
    h3 {
        font-size: 1.5rem !important;
        margin-bottom: 2rem !important;
        border-bottom: 1px solid rgba(192, 192, 192, 0.1) !important;
        padding-bottom: 1rem !important;
    }
    
    /* 일반 텍스트 */
    p, div, span {
        color: #C0C0C0 !important;
        font-weight: 300 !important;
        line-height: 1.6 !important;
    }
    </style>
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

def search_response_history(search_query):
    """기존 대응 이력 검색"""
    try:
        df = pd.read_csv('data/언론대응내역.csv', encoding='utf-8')
        
        if search_query.strip() == "":
            return df
        
        # 검색어가 있는 경우 필터링
        search_results = df[
            df.astype(str).apply(
                lambda row: row.str.contains(search_query, case=False, na=False).any(), 
                axis=1
            )
        ]
        
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
    """개선된 LLM을 사용하여 이슈 발생 보고서 생성"""
    try:
        # DataBasedLLM 초기화
        data_llm = DataBasedLLM()
        
        # 개선된 이슈발생보고서 생성 메소드 사용 (템플릿 변수 치환 적용)
        response = data_llm.generate_issue_report(media_name, reporter_name, issue_description)
        return response
        
    except Exception as e:
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
    
    # CSS 로드
    load_css()
    
    # 데이터 로드
    load_data()
    
    # 헤더 영역
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # 로고 표시
        logo = load_logo()
        if logo:
            st.image(logo, width=300)
        else:
            st.markdown("""
            <div class="logo-container">
                <h1 style="color: #1e3c72; font-size: 2rem; font-weight: 700;">
                    POSCO INTERNATIONAL
                </h1>
            </div>
            """, unsafe_allow_html=True)
    
    # 메인 헤더
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">위기관리커뮤니케이션 AI 자동화 솔루션</h1>
        <p class="header-subtitle">AI 기반 스마트 언론대응 솔루션</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 사이드바 메뉴 구성
    with st.sidebar:
        st.markdown("""
        <div style="background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%); 
                    padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem;">
            <h3 style="color: white; text-align: center; margin: 0;">메뉴</h3>
        </div>
        """, unsafe_allow_html=True)
        
        menu_option = st.selectbox(
            "카테고리 선택",
            ["이슈발생보고 생성", "언론사 정보 검색", "담당자 정보 검색", "기존대응이력 검색"]
        )
    
    # 선택된 메뉴에 따른 콘텐츠 표시
    if menu_option == "이슈발생보고 생성":
        # 메인 콘텐츠 영역
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("""
            <div class="card input-card">
                <h3 style="color: #1f2937; margin-bottom: 1.5rem;">이슈 정보 입력</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # 언론사 입력
            selected_media = st.text_input(
                "언론사명",
                placeholder="언론사명을 입력하세요 (예: 조선일보, 동아일보, 한국경제 등)",
                key="media_input"
            )
            
            # 기자명 입력
            selected_reporter = st.text_input(
                "기자명",
                placeholder="담당 기자명을 입력하세요",
                key="reporter_input"
            )
                
            # 발생 이슈 입력
            issue_description = st.text_area(
                "발생 이슈",
                placeholder="발생한 이슈에 대해 상세히 기술해주세요...",
                height=150,
                key="issue_input"
            )
            
            # 생성 버튼
            generate_button = st.button(
                "이슈발생보고 생성",
                key="generate_btn",
                use_container_width=True
            )
        
        with col2:
            st.markdown("""
            <div class="card result-card">
                <h3 style="color: #1f2937; margin-bottom: 1.5rem;">생성 결과</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # 보고서 생성 및 표시
            if generate_button:
                if not selected_media.strip():
                    st.error("언론사명을 입력해주세요.")
                elif not selected_reporter.strip():
                    st.error("기자명을 입력해주세요.")
                elif not issue_description.strip():
                    st.error("발생 이슈를 입력해주세요.")
                else:
                    # 로딩 표시
                    with st.spinner("AI가 분석하고 있습니다..."):
                        # 기본 보고서 생성
                        report = generate_issue_report(
                            selected_media, 
                            selected_reporter, 
                            issue_description
                        )
                        
                        st.markdown("### 생성된 이슈 발생 보고서")
                        st.write(report)
                    
                    # 다운로드 버튼
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
    
    
    elif menu_option == "언론사 정보 검색":
        st.markdown("### 📰 언론사 정보 조회")
        
        media_search = st.text_input("언론사명을 입력하세요:", key="media_search", placeholder="예: 조선일보, 중앙일보, 한국경제 등")
        
        if st.button("🔍 언론사 정보 조회", key="media_info_btn"):
            if media_search:
                with st.spinner("언론사 정보를 검색하고 있습니다..."):
                    media_info = search_media_info(media_search)
                    
                    if media_info:
                        st.success(f"✅ '{media_search}' 언론사 정보를 찾았습니다!")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📋 기본 정보")
                            st.info(f"""
                            **언론사명**: {media_info.get('name', 'N/A')}
                            **분류**: {media_info.get('type', 'N/A')}  
                            **담당자**: {media_info.get('contact_person', 'N/A')}
                            **출입기자 수**: {len(media_info.get('reporters', []))}명
                            """)
                        
                        with col2:
                            st.markdown("#### 👥 출입기자 정보")
                            reporters = media_info.get('reporters', [])
                            if reporters:
                                st.markdown("**등록된 출입기자:**")
                                for i, reporter in enumerate(reporters, 1):
                                    st.write(f"{i}. {reporter}")
                            else:
                                st.write("등록된 출입기자 정보가 없습니다.")
                        
                        # 원본 데이터 표시 (디버깅용)
                        with st.expander("🔍 상세 데이터 (개발자용)"):
                            st.json(media_info.get('raw_data', {}))
                            
                    else:
                        st.warning(f"❌ '{media_search}' 언론사 정보를 찾을 수 없습니다.")
                        st.info("등록되지 않은 언론사일 수 있습니다. 정확한 언론사명을 입력해주세요.")
                        
                        # 사용 가능한 언론사 목록 표시
                        with st.expander("📋 등록된 언론사 목록 확인"):
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
    
    elif menu_option == "담당자 정보 검색":
        st.markdown("### 👥 담당자 정보")
        
        contact_info = get_contact_info()
        
        # 주관부서 정보
        st.markdown("#### 🔷 주관부서: 커뮤니케이션실 – 홍보그룹")
        
        # 주관부서 담당자 테이블
        main_dept_data = []
        for person in contact_info["주관부서"]["담당자"]:
            main_dept_data.append([person["성명"], person["직책"], person["사무실번호"]])
        
        main_dept_df = pd.DataFrame(main_dept_data, columns=["성명", "직책", "사무실 번호"])
        st.dataframe(main_dept_df, use_container_width=True)
        
        st.markdown("---")
        
        # 협의체 참여 부서 정보
        st.markdown("#### 🔷 협의체 참여 현업 부서 담당자 (13개 부서)")
        
        # 협의체 부서 담당자 테이블
        coop_dept_data = []
        for dept in contact_info["협의체_참여부서"]:
            coop_dept_data.append([dept["부서명"], dept["성명"], dept["직책"], dept["사무실번호"]])
        
        coop_dept_df = pd.DataFrame(coop_dept_data, columns=["부서명", "성명", "직책", "사무실 번호"])
        st.dataframe(coop_dept_df, use_container_width=True)
        
        # 검색 기능 추가
        st.markdown("---")
        st.markdown("#### 🔍 담당자 검색")
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_name = st.text_input("담당자 성명으로 검색:", key="contact_name_search")
        
        with col2:
            search_dept = st.text_input("부서명으로 검색:", key="contact_dept_search")
        
        if search_name or search_dept:
            filtered_contacts = []
            
            # 주관부서에서 검색
            for person in contact_info["주관부서"]["담당자"]:
                if (not search_name or search_name in person["성명"]) and \
                   (not search_dept or search_dept in contact_info["주관부서"]["부서명"]):
                    filtered_contacts.append({
                        "부서명": contact_info["주관부서"]["부서명"],
                        "성명": person["성명"],
                        "직책": person["직책"],
                        "사무실번호": person["사무실번호"]
                    })
            
            # 협의체 부서에서 검색
            for dept in contact_info["협의체_참여부서"]:
                if (not search_name or search_name in dept["성명"]) and \
                   (not search_dept or search_dept in dept["부서명"]):
                    filtered_contacts.append(dept)
            
            if filtered_contacts:
                st.success(f"✅ {len(filtered_contacts)}명의 담당자를 찾았습니다.")
                filtered_df = pd.DataFrame(filtered_contacts)
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.warning("❌ 해당 조건에 맞는 담당자를 찾을 수 없습니다.")
    
    elif menu_option == "기존대응이력 검색":
        st.markdown("### 📊 기존 대응 이력 검색")
        
        # 검색창
        search_query = st.text_input(
            "검색어를 입력하세요:",
            key="history_search",
            placeholder="예: 2025년 4월, 대응단계, 언론사명 등"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_button = st.button("🔍 검색", key="history_search_btn")
        
        with col2:
            show_all_button = st.button("📋 전체 이력 보기", key="show_all_btn")
        
        if search_button or show_all_button:
            with st.spinner("대응 이력을 검색하고 있습니다..."):
                if show_all_button:
                    search_query = ""
                
                search_results = search_response_history(search_query)
                
                if not search_results.empty:
                    # 검색 결과 통계
                    st.markdown(f"#### 📈 검색 결과: 총 {len(search_results)}건")
                    
                    # 분석 결과 표시
                    if search_query:
                        analysis = analyze_response_history(search_results, search_query)
                        
                        if analysis:
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if '대응단계별_통계' in analysis:
                                    st.markdown("##### 🎯 대응단계별 통계")
                                    for stage, count in analysis['대응단계별_통계'].items():
                                        st.metric(f"{stage}", f"{count}건")
                            
                            with col2:
                                if '언론사별_통계' in analysis:
                                    st.markdown("##### 📰 주요 언론사")
                                    for media, count in list(analysis['언론사별_통계'].items())[:5]:
                                        st.metric(f"{media}", f"{count}건")
                            
                            with col3:
                                if '이슈유형별_통계' in analysis:
                                    st.markdown("##### 📋 이슈 유형")
                                    for issue_type, count in list(analysis['이슈유형별_통계'].items())[:5]:
                                        st.metric(f"{issue_type}", f"{count}건")
                    
                    # 상세 데이터 테이블
                    st.markdown("#### 📊 상세 대응 이력")
                    
                    # 페이지네이션
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
                        label="📄 검색 결과 다운로드 (CSV)",
                        data=csv_data,
                        file_name=f"대응이력_검색결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("❌ 검색 조건에 맞는 대응 이력을 찾을 수 없습니다.")
        
        # 추가: 빠른 검색 버튼들
        st.markdown("---")
        st.markdown("#### ⚡ 빠른 검색")
        
        quick_search_col1, quick_search_col2, quick_search_col3 = st.columns(3)
        
        with quick_search_col1:
            if st.button("📅 최근 한 달", key="recent_month"):
                st.session_state.history_search = "2025년"
                st.rerun()
        
        with quick_search_col2:
            if st.button("🚨 위기단계별", key="crisis_level"):
                st.session_state.history_search = "단계"
                st.rerun()
        
        with quick_search_col3:
            if st.button("📰 주요 언론사", key="major_media"):
                st.session_state.history_search = "조선일보"
                st.rerun()

if __name__ == "__main__":
    main()
