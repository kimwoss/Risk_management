"""
당일 뉴스 모니터링 현황 대시보드 컴포넌트
당일 기사 총 건수와 해시태그 카테고리별 통계 실시간 표시
"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pytz
import pandas as pd


# CSS는 한 번만 주입 (Streamlit이 <style> 태그를 markdown 내에서 strip하는 문제 방지)
_CSS_INJECTED = False

def _inject_css():
    global _CSS_INJECTED
    if _CSS_INJECTED:
        return
    _CSS_INJECTED = True
    components.html("""
    <style>
    .ic-total-hero {
        background: linear-gradient(120deg, rgba(99,102,241,0.18) 0%, rgba(59,130,246,0.10) 100%);
        border: 1px solid rgba(99,102,241,0.35);
        border-radius: 10px;
        padding: 14px 28px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
    }
    .ic-total-date {
        font-size: 1.05rem;
        font-weight: 700;
        color: #a5b4fc;
        letter-spacing: 0.06em;
        white-space: nowrap;
    }
    .ic-total-sep {
        width: 1px;
        height: 32px;
        background: rgba(99,102,241,0.45);
        flex-shrink: 0;
    }
    .ic-total-count {
        display: flex;
        align-items: baseline;
        gap: 5px;
    }
    .ic-total-value {
        font-size: 2.4rem;
        font-weight: 800;
        color: #fff;
        line-height: 1;
        letter-spacing: -0.01em;
    }
    .ic-total-unit {
        font-size: 1rem;
        font-weight: 600;
        color: #818cf8;
    }
    .ic-kw-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 6px;
        margin-top: 0;
    }
    .ic-kw-card {
        border-radius: 6px;
        padding: 8px 10px 6px;
        border-left: 2px solid;
        text-align: center;
        transition: background 0.2s;
    }
    .ic-kw-card:hover { background: rgba(255,255,255,0.06) !important; }
    .ic-kw-label {
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 3px;
    }
    .ic-kw-num {
        font-weight: 700;
        color: #fff;
        line-height: 1;
        margin-bottom: 3px;
    }
    .ic-kw-pct { color: rgba(255,255,255,0.38); }

    .ic-kw-1 { border-left-color: #22c55e; background: rgba(34,197,94,0.07); }
    .ic-kw-1 .ic-kw-label { font-size: 0.72rem; color: #4ade80; }
    .ic-kw-1 .ic-kw-num   { font-size: 1.45rem; }
    .ic-kw-1 .ic-kw-pct   { font-size: 0.68rem; }

    .ic-kw-2 { border-left-color: #f59e0b; background: rgba(245,158,11,0.07); }
    .ic-kw-2 .ic-kw-label { font-size: 0.72rem; color: #fbbf24; }
    .ic-kw-2 .ic-kw-num   { font-size: 1.3rem; }
    .ic-kw-2 .ic-kw-pct   { font-size: 0.66rem; }

    .ic-kw-3 { border-left-color: #3b82f6; background: rgba(59,130,246,0.06); }
    .ic-kw-3 .ic-kw-label { font-size: 0.68rem; color: #60a5fa; }
    .ic-kw-3 .ic-kw-num   { font-size: 1.15rem; }
    .ic-kw-3 .ic-kw-pct   { font-size: 0.64rem; }

    .ic-kw-4 { border-left-color: #ec4899; background: rgba(236,72,153,0.05); }
    .ic-kw-4 .ic-kw-label { font-size: 0.68rem; color: #f472b6; opacity: 0.85; }
    .ic-kw-4 .ic-kw-num   { font-size: 1.05rem; opacity: 0.88; }
    .ic-kw-4 .ic-kw-pct   { font-size: 0.63rem; }

    .ic-kw-5 { border-left-color: #a855f7; background: rgba(168,85,247,0.04); }
    .ic-kw-5 .ic-kw-label { font-size: 0.67rem; color: #c084fc; opacity: 0.72; }
    .ic-kw-5 .ic-kw-num   { font-size: 0.95rem; opacity: 0.72; }
    .ic-kw-5 .ic-kw-pct   { font-size: 0.62rem; }
    </style>
    """, height=0)


def render_news_dashboard(news_df: pd.DataFrame, show_live: bool = True):
    """
    당일 뉴스 현황 대시보드 렌더링

    Args:
        news_df: 뉴스 데이터프레임 (columns: 날짜, 검색키워드, 기사제목 등)
        show_live: LIVE 뱃지 표시 여부
    """
    _inject_css()

    # 오늘 날짜 (KST 기준)
    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst)
    today_str = now_kst.strftime('%Y-%m-%d')

    # 당일 기사만 필터링
    if news_df.empty or "날짜" not in news_df.columns:
        today_news = pd.DataFrame()
    else:
        today_news = news_df[news_df["날짜"].astype(str).str.startswith(today_str)].copy()

    # 총 당일 기사 수
    total_today = len(today_news)

    # 카테고리별 카운트
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

            is_pos = sentiment == "pos"
            is_neg = sentiment == "neg"

            if is_pos:
                total_pos += 1
            elif is_neg:
                total_neg += 1

            if any(kw in keyword or kw in title for kw in ["포스코인터내셔널", "POSCO INTERNATIONAL", "포스코인터"]):
                posco_intl_count += 1
                if is_pos: posco_intl_pos += 1
                elif is_neg: posco_intl_neg += 1
            elif "포스코모빌리티솔루션" in keyword or "포스코모빌리티솔루션" in title:
                posco_mobility_count += 1
                if is_pos: posco_mobility_pos += 1
                elif is_neg: posco_mobility_neg += 1
            elif "삼척블루파워" in keyword or "삼척블루파워" in title:
                samcheok_count += 1
                if is_pos: samcheok_pos += 1
                elif is_neg: samcheok_neg += 1
            elif "포스코" in keyword or "포스코" in title or "POSCO" in keyword.upper() or "POSCO" in title.upper():
                posco_count += 1
                if is_pos: posco_pos += 1
                elif is_neg: posco_neg += 1
            else:
                others_count += 1
                if is_pos: others_pos += 1
                elif is_neg: others_neg += 1

    # 퍼센트 계산
    posco_intl_pct    = (posco_intl_count    / total_today * 100) if total_today > 0 else 0
    posco_mobility_pct= (posco_mobility_count/ total_today * 100) if total_today > 0 else 0
    samcheok_pct      = (samcheok_count      / total_today * 100) if total_today > 0 else 0
    posco_pct         = (posco_count         / total_today * 100) if total_today > 0 else 0
    others_pct        = (others_count        / total_today * 100) if total_today > 0 else 0

    display_date = now_kst.strftime('%Y.%m.%d')

    import random, string
    unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))

    # ── 상단: 총합 카드 (중앙 정렬, 강조) ────────────────────────
    st.markdown(f'''
    <div class="ic-total-hero">
        <div class="ic-total-date">{display_date}</div>
        <div class="ic-total-sep"></div>
        <div class="ic-total-count">
            <span class="ic-total-value" id="total-{unique_id}" data-target="{total_today}">0</span>
            <span class="ic-total-unit">건</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # ── 하단: 키워드 카드 5개 ────────────────────────────────────
    st.markdown(f'''
    <div class="ic-kw-grid">
      <div class="ic-kw-card ic-kw-1">
        <div class="ic-kw-label">#포스코인터내셔널</div>
        <div class="ic-kw-num" id="posco-intl-{unique_id}" data-target="{posco_intl_count}">0</div>
        <div class="ic-kw-pct">{posco_intl_pct:.1f}%</div>
      </div>
      <div class="ic-kw-card ic-kw-2">
        <div class="ic-kw-label">#포스코</div>
        <div class="ic-kw-num" id="posco-{unique_id}" data-target="{posco_count}">0</div>
        <div class="ic-kw-pct">{posco_pct:.1f}%</div>
      </div>
      <div class="ic-kw-card ic-kw-3">
        <div class="ic-kw-label">#포스코모빌리티솔루션</div>
        <div class="ic-kw-num" id="mobility-{unique_id}" data-target="{posco_mobility_count}">0</div>
        <div class="ic-kw-pct">{posco_mobility_pct:.1f}%</div>
      </div>
      <div class="ic-kw-card ic-kw-4">
        <div class="ic-kw-label">#삼척블루파워</div>
        <div class="ic-kw-num" id="samcheok-{unique_id}" data-target="{samcheok_count}">0</div>
        <div class="ic-kw-pct">{samcheok_pct:.1f}%</div>
      </div>
      <div class="ic-kw-card ic-kw-5">
        <div class="ic-kw-label">#기타</div>
        <div class="ic-kw-num" id="others-{unique_id}" data-target="{others_count}">0</div>
        <div class="ic-kw-pct">{others_pct:.1f}%</div>
      </div>
    </div>
    ''', unsafe_allow_html=True)

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

            ids.forEach((id) => {{
                const elem = window.parent.document.getElementById(id);
                if (!elem) return;

                const target = parseInt(elem.getAttribute('data-target'));
                const duration = 700 + Math.random() * 400;
                const startTime = performance.now();

                function animate(currentTime) {{
                    const elapsed = currentTime - startTime;
                    const progress = Math.min(elapsed / duration, 1);
                    const easedProgress = easeOutQuart(progress);
                    const current = Math.floor(easedProgress * target);
                    elem.textContent = formatNumber(current);
                    if (progress < 1) requestAnimationFrame(animate);
                }}

                requestAnimationFrame(animate);
            }});
        }}

        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', animateCount);
        }} else {{
            animateCount();
        }}
    }})();
    </script>
    '''

    components.html(animation_script, height=0)
