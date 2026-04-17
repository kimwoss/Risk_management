"""
당일 뉴스 모니터링 현황 대시보드 컴포넌트
당일 기사 총 건수와 해시태그 카테고리별 통계 실시간 표시
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

    # 카테고리별 카운트 (긍정/부정 분리)
    total_pos = total_neg = 0
    posco_intl_count = posco_intl_pos = posco_intl_neg = 0
    posco_mobility_count = posco_mobility_pos = posco_mobility_neg = 0
    samcheok_count = samcheok_pos = samcheok_neg = 0
    posco_count = posco_pos = posco_neg = 0
    others_count = others_pos = others_neg = 0

    if not today_news.empty and "검색키워드" in today_news.columns:
        for _, row in today_news.iterrows():
            keyword = str(row.get("검색키워드", ""))
            title = str(row.get("기사제목", ""))
            sentiment = str(row.get("sentiment", "pos"))

            # sentiment 카운트
            is_pos = sentiment == "pos"
            is_neg = sentiment == "neg"

            # 전체 sentiment 카운트
            if is_pos:
                total_pos += 1
            elif is_neg:
                total_neg += 1

            # 1순위: 포스코인터내셔널 (POSCO INTERNATIONAL, 포스코인터 포함)
            if any(kw in keyword or kw in title for kw in ["포스코인터내셔널", "POSCO INTERNATIONAL", "포스코인터"]):
                posco_intl_count += 1
                if is_pos:
                    posco_intl_pos += 1
                elif is_neg:
                    posco_intl_neg += 1
            # 2순위: 포스코모빌리티솔루션
            elif "포스코모빌리티솔루션" in keyword or "포스코모빌리티솔루션" in title:
                posco_mobility_count += 1
                if is_pos:
                    posco_mobility_pos += 1
                elif is_neg:
                    posco_mobility_neg += 1
            # 3순위: 삼척블루파워
            elif "삼척블루파워" in keyword or "삼척블루파워" in title:
                samcheok_count += 1
                if is_pos:
                    samcheok_pos += 1
                elif is_neg:
                    samcheok_neg += 1
            # 4순위: 포스코 (위 항목 제외)
            elif "포스코" in keyword or "포스코" in title or "POSCO" in keyword.upper() or "POSCO" in title.upper():
                posco_count += 1
                if is_pos:
                    posco_pos += 1
                elif is_neg:
                    posco_neg += 1
            # 5순위: 기타
            else:
                others_count += 1
                if is_pos:
                    others_pos += 1
                elif is_neg:
                    others_neg += 1

    # 퍼센트 계산
    posco_intl_pct = (posco_intl_count / total_today * 100) if total_today > 0 else 0
    posco_mobility_pct = (posco_mobility_count / total_today * 100) if total_today > 0 else 0
    samcheok_pct = (samcheok_count / total_today * 100) if total_today > 0 else 0
    posco_pct = (posco_count / total_today * 100) if total_today > 0 else 0
    others_pct = (others_count / total_today * 100) if total_today > 0 else 0

    last_updated = now_kst.strftime('%Y-%m-%d %H:%M KST')

    # 애니메이션을 위한 고유 ID
    import random
    import string
    unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))

    # 6개 카드를 한 줄에 배치
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.markdown(f'''<div class="iris-card ic-total">
            <div class="ic-label">당일 기사</div>
            <div class="ic-value" id="total-{unique_id}" data-target="{total_today}">0</div>
            <div class="ic-pill-row">
                <span class="ic-pill pos">{total_pos}</span>
                <span class="ic-pill neg">{total_neg}</span>
            </div>
        </div>''', unsafe_allow_html=True)

    with col2:
        st.markdown(f'''<div class="iris-card ic-pos">
            <div class="ic-label">#포스코인터내셔널</div>
            <div class="ic-value" id="posco-intl-{unique_id}" data-target="{posco_intl_count}">0</div>
            <div class="ic-pct">{posco_intl_pct:.1f}%</div>
            <div class="ic-pill-row">
                <span class="ic-pill pos">{posco_intl_pos}</span>
                <span class="ic-pill neg">{posco_intl_neg}</span>
            </div>
        </div>''', unsafe_allow_html=True)

    with col3:
        st.markdown(f'''<div class="iris-card ic-amber">
            <div class="ic-label">#포스코</div>
            <div class="ic-value" id="posco-{unique_id}" data-target="{posco_count}">0</div>
            <div class="ic-pct">{posco_pct:.1f}%</div>
            <div class="ic-pill-row">
                <span class="ic-pill pos">{posco_pos}</span>
                <span class="ic-pill neg">{posco_neg}</span>
            </div>
        </div>''', unsafe_allow_html=True)

    with col4:
        st.markdown(f'''<div class="iris-card ic-blue">
            <div class="ic-label">#포스코모빌리티솔루션</div>
            <div class="ic-value" id="mobility-{unique_id}" data-target="{posco_mobility_count}">0</div>
            <div class="ic-pct">{posco_mobility_pct:.1f}%</div>
            <div class="ic-pill-row">
                <span class="ic-pill pos">{posco_mobility_pos}</span>
                <span class="ic-pill neg">{posco_mobility_neg}</span>
            </div>
        </div>''', unsafe_allow_html=True)

    with col5:
        st.markdown(f'''<div class="iris-card ic-pink">
            <div class="ic-label">#삼척블루파워</div>
            <div class="ic-value" id="samcheok-{unique_id}" data-target="{samcheok_count}">0</div>
            <div class="ic-pct">{samcheok_pct:.1f}%</div>
            <div class="ic-pill-row">
                <span class="ic-pill pos">{samcheok_pos}</span>
                <span class="ic-pill neg">{samcheok_neg}</span>
            </div>
        </div>''', unsafe_allow_html=True)

    with col6:
        st.markdown(f'''<div class="iris-card ic-purple">
            <div class="ic-label">#기타</div>
            <div class="ic-value" id="others-{unique_id}" data-target="{others_count}">0</div>
            <div class="ic-pct">{others_pct:.1f}%</div>
            <div class="ic-pill-row">
                <span class="ic-pill pos">{others_pos}</span>
                <span class="ic-pill neg">{others_neg}</span>
            </div>
        </div>''', unsafe_allow_html=True)

    # 카운트 애니메이션 JavaScript
    animation_script = f'''
    <script>
    (function() {{
        function animateCount() {{
            const ids = ['total-{unique_id}', 'posco-intl-{unique_id}', 'posco-{unique_id}', 'mobility-{unique_id}', 'samcheok-{unique_id}', 'others-{unique_id}'];

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
