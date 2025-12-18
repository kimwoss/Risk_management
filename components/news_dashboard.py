"""
당일 뉴스 모니터링 현황 대시보드 컴포넌트
당일 기사 총 건수와 카테고리별 통계 실시간 표시
"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pytz
import pandas as pd


def render_news_dashboard(news_df: pd.DataFrame, show_live: bool = True):
    """
    당일 뉴스 현황 대시보드 렌더링

    Args:
        news_df: 뉴스 데이터프레임 (columns: 날짜, 검색키워드, 기사제목 등)
        show_live: LIVE 뱃지 표시 여부
    """
    # 오늘 날짜 (KST 기준)
    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst)
    today_str = now_kst.strftime('%Y-%m-%d')

    # 당일 기사만 필터링
    if news_df.empty or "날짜" not in news_df.columns:
        today_news = pd.DataFrame()
    else:
        # 날짜 컬럼이 문자열인 경우를 고려하여 날짜 비교
        today_news = news_df[news_df["날짜"].astype(str).str.startswith(today_str)].copy()

    # 총 당일 기사 수
    total_today = len(today_news)

    # 카테고리별 카운트
    posco_intl_count = 0
    posco_count = 0
    others_count = 0

    if not today_news.empty and "검색키워드" in today_news.columns:
        # 포스코인터내셔널 관련 키워드
        posco_intl_keywords = ["포스코인터내셔널", "POSCO INTERNATIONAL", "포스코인터",
                               "삼척블루파워", "구동모터코아", "구동모터코어",
                               "미얀마 LNG", "포스코모빌리티솔루션"]

        for _, row in today_news.iterrows():
            keyword = str(row.get("검색키워드", ""))
            title = str(row.get("기사제목", ""))

            # 포스코인터내셔널 관련 (키워드 또는 제목에 포함)
            is_posco_intl = False
            for kw in posco_intl_keywords:
                if kw in keyword or kw in title:
                    is_posco_intl = True
                    break

            if is_posco_intl:
                posco_intl_count += 1
            # 포스코 (포스코인터내셔널 제외)
            elif "포스코" in keyword or "포스코" in title or "POSCO" in keyword.upper() or "POSCO" in title.upper():
                posco_count += 1
            # 기타
            else:
                others_count += 1

    # 퍼센트 계산
    posco_intl_pct = (posco_intl_count / total_today * 100) if total_today > 0 else 0
    posco_pct = (posco_count / total_today * 100) if total_today > 0 else 0
    others_pct = (others_count / total_today * 100) if total_today > 0 else 0

    last_updated = now_kst.strftime('%Y-%m-%d %H:%M KST')

    # 애니메이션을 위한 고유 ID
    import random
    import string
    unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))

    # CSS 스타일
    st.markdown("""
    <style>
    div[data-testid="column"] { padding: 0 6px !important; }
    .news-dash-container { background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
    .news-dash-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.08); }
    .news-dash-title { color: #e0e0e0; font-size: 1.1rem; font-weight: 600; }
    .news-live-badge { background: rgba(239,68,68,0.15); color: #ef4444; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; }
    .news-last-updated { color: #888; font-size: 0.75rem; margin-left: 12px; }

    .news-card { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 20px 16px; border-top: 3px solid; text-align: center; transition: all 0.2s ease; min-height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .news-card:hover { background: rgba(255,255,255,0.06); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }

    .news-card.total { border-top-color: #6366f1; background: rgba(99,102,241,0.05); }
    .news-card.posco-intl { border-top-color: #22c55e; }
    .news-card.posco { border-top-color: #f59e0b; }
    .news-card.others { border-top-color: #8b5cf6; }

    .news-label { font-size: 0.8rem; font-weight: 600; margin-bottom: 12px; }
    .news-card.total .news-label { color: #6366f1; }
    .news-card.posco-intl .news-label { color: #22c55e; }
    .news-card.posco .news-label { color: #f59e0b; }
    .news-card.others .news-label { color: #8b5cf6; }

    .news-value { color: #e0e0e0; font-size: 2.2rem; font-weight: 700; margin: 8px 0; }
    .news-card.total .news-value { font-size: 2.8rem; color: #fff; }

    .news-pct { color: #888; font-size: 0.75rem; margin-top: 4px; }

    @media (max-width: 768px) {
        div[data-testid="column"] { flex: 1 1 calc(50% - 12px) !important; min-width: 120px !important; }
    }
    @media (max-width: 480px) {
        div[data-testid="column"] { flex: 1 1 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    live = f'<span class="news-live-badge">LIVE</span>' if show_live else ''

    st.markdown(f'<div class="news-dash-container"><div class="news-dash-header"><span class="news-dash-title">📊 {today_str} 당일 기사 현황</span><span>{live}<span class="news-last-updated">Last updated: {last_updated}</span></span></div>', unsafe_allow_html=True)

    # 4개 카드를 한 줄에 배치
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f'<div class="news-card total"><div class="news-label">당일 기사</div><div class="news-value" id="total-{unique_id}" data-target="{total_today}">0</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="news-card posco-intl"><div class="news-label">포스코인터내셔널</div><div class="news-value" id="posco-intl-{unique_id}" data-target="{posco_intl_count}">0</div><div class="news-pct">{posco_intl_pct:.1f}%</div></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div class="news-card posco"><div class="news-label">포스코</div><div class="news-value" id="posco-{unique_id}" data-target="{posco_count}">0</div><div class="news-pct">{posco_pct:.1f}%</div></div>', unsafe_allow_html=True)

    with col4:
        st.markdown(f'<div class="news-card others"><div class="news-label">기타</div><div class="news-value" id="others-{unique_id}" data-target="{others_count}">0</div><div class="news-pct">{others_pct:.1f}%</div></div>', unsafe_allow_html=True)

    # 카운트 애니메이션 JavaScript
    animation_script = f'''
    <script>
    (function() {{
        function animateCount() {{
            const ids = ['total-{unique_id}', 'posco-intl-{unique_id}', 'posco-{unique_id}', 'others-{unique_id}'];

            function easeOutQuart(t) {{
                return 1 - Math.pow(1 - t, 4);
            }}

            function formatNumber(num) {{
                return num.toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ",");
            }}

            ids.forEach((id, index) => {{
                const elem = window.parent.document.getElementById(id);
                if (!elem) return;

                const target = parseInt(elem.getAttribute('data-target'));
                const duration = 700 + Math.random() * 400; // 700-1100ms
                const startTime = performance.now();

                function animate(currentTime) {{
                    const elapsed = currentTime - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    const easedProgress = easeOutQuart(progress);
                    const current = Math.floor(easedProgress * target);

                    elem.textContent = formatNumber(current);

                    if (progress < 1) {{
                        requestAnimationFrame(animate);
                    }}
                }}

                requestAnimationFrame(animate);
            }});
        }}

        // DOM이 로드된 후 실행
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', animateCount);
        }} else {{
            animateCount();
        }}
    }})();
    </script>
    '''

    components.html(animation_script, height=0)

    st.markdown('</div>', unsafe_allow_html=True)
