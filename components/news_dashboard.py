"""
당일 뉴스 모니터링 현황 대시보드 컴포넌트
당일 기사 총 건수와 해시태그 카테고리별 통계 실시간 표시
"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pytz
import pandas as pd


_CSS = """
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
.ic-total-num {
    font-size: 2.4rem;
    font-weight: 800;
    color: var(--c-text-strong, #fff);
    line-height: 1;
    letter-spacing: -0.01em;
}
.ic-total-unit {
    font-size: 1rem;
    font-weight: 600;
    color: #818cf8;
}
.ic-neg-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 12px;
    border-radius: 99px;
    font-size: 0.82rem;
    font-weight: 700;
    background: rgba(239,68,68,0.14);
    color: #f87171;
    border: 1px solid rgba(239,68,68,0.35);
    white-space: nowrap;
}
.ic-neg-badge.zero {
    background: rgba(148,163,184,0.08);
    color: rgba(148,163,184,0.75);
    border-color: rgba(148,163,184,0.2);
}
.ic-kw-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
    gap: 6px;
    margin-top: 0;
}
.ic-kw-card {
    border-radius: 6px;
    padding: 8px 10px 6px;
    border-left: 2px solid;
    text-align: center;
    transition: background 0.2s;
    min-width: 0;
}
@media (max-width: 480px) {
    .ic-total-hero { padding: 12px 16px; gap: 12px; }
    .ic-total-num { font-size: 2rem; }
    .ic-kw-grid { gap: 5px; }
    .ic-kw-card { padding: 7px 6px 5px; }
}
.ic-kw-card:hover { background: var(--c-surface-h, rgba(255,255,255,0.06)) !important; }
.ic-kw-label {
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 3px;
}
.ic-kw-num {
    font-weight: 700;
    color: var(--c-text-strong, #fff);
    line-height: 1;
    margin-bottom: 3px;
}
.ic-kw-pct { color: var(--c-text-mute, rgba(255,255,255,0.5)); }

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

/* ── 카드 클릭 필터 ──
   카드는 HTML 그대로 두고, 같은 칸에 투명 버튼을 겹쳐 클릭을 받는다.
   (HTML 링크로 만들면 페이지가 새로 로드돼 세션·로그인이 끊긴다) */
.st-key-ic_kw_grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
    gap: 6px !important;
}
[class*="st-key-ic_card_"] { position: relative; gap: 0 !important; }
[class*="st-key-ic_card_"] [data-testid="stMarkdownContainer"] { margin: 0 !important; }
[class*="st-key-ic_card_"] .ic-kw-card { cursor: pointer; height: 100%; box-sizing: border-box; }
[class*="st-key-ic_btn_"] {
    position: absolute !important; inset: 0; z-index: 2;
    width: 100% !important; height: 100% !important; margin: 0 !important;
}
[class*="st-key-ic_btn_"] .stButton,
[class*="st-key-ic_btn_"] button {
    width: 100% !important; height: 100% !important; min-height: 0 !important;
    opacity: 0 !important; cursor: pointer; padding: 0 !important; margin: 0 !important;
}
.ic-kw-card.ic-kw-active { box-shadow: 0 0 0 2px currentColor inset; }
.ic-kw-card.ic-kw-active .ic-kw-label::after { content: " ✓"; }
.ic-kw-card.ic-kw-dim { opacity: 0.4; }
</style>
"""


# 대시보드 카드 정의: (분류 코드, 표시 라벨, 스타일 단계, 카운트 애니메이션 id 접두어)
CATEGORIES = [
    ("intl",     "#포스코인터내셔널",     1, "posco-intl"),
    ("posco",    "#포스코",              2, "posco"),
    ("mobility", "#포스코모빌리티솔루션", 3, "mobility"),
    ("samcheok", "#삼척블루파워",         4, "samcheok"),
    ("others",   "#기타",               5, "others"),
]
CATEGORY_LABELS = {c[0]: c[1] for c in CATEGORIES}

# 선택한 카드(분류 코드)를 보관하는 세션 키 — 아래 기사 목록이 이 값으로 필터링된다
FILTER_STATE_KEY = "news_cat_filter"


def classify_category(keyword: str, title: str) -> str:
    """기사 1건을 대시보드 카드 분류로 매핑. 카드 건수와 목록 필터가 같은 기준을 쓰도록 한 곳에 둔다."""
    keyword, title = str(keyword), str(title)
    if any(kw in keyword or kw in title for kw in ["포스코인터내셔널", "POSCO INTERNATIONAL", "포스코인터"]):
        return "intl"
    if "포스코모빌리티솔루션" in keyword or "포스코모빌리티솔루션" in title:
        return "mobility"
    if "삼척블루파워" in keyword or "삼척블루파워" in title:
        return "samcheok"
    if "포스코" in keyword or "포스코" in title or "POSCO" in keyword.upper() or "POSCO" in title.upper():
        return "posco"
    return "others"


def _toggle_filter(cat: str):
    # 같은 카드를 다시 누르면 해제(전체 보기)
    cur = st.session_state.get(FILTER_STATE_KEY)
    st.session_state[FILTER_STATE_KEY] = None if cur == cat else cat


def render_news_dashboard(news_df: pd.DataFrame, show_live: bool = True):
    """
    당일 뉴스 현황 대시보드 렌더링

    Args:
        news_df: 뉴스 데이터프레임 (columns: 날짜, 검색키워드, 기사제목 등)
        show_live: LIVE 뱃지 표시 여부
    """
    # CSS를 st.markdown으로 단독 주입 (components.html은 iframe 샌드박스라 parent에 미적용)
    st.markdown(_CSS, unsafe_allow_html=True)

    # 오늘 날짜 (KST 기준)
    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst)
    today_str = now_kst.strftime('%Y-%m-%d')

    # 당일 기사만 필터링
    if news_df.empty or "날짜" not in news_df.columns:
        today_news = pd.DataFrame()
    else:
        today_news = news_df[news_df["날짜"].astype(str).str.startswith(today_str)].copy()

    total_today = len(today_news)

    # 카테고리별 카운트
    total_neg = 0
    counts = {c[0]: 0 for c in CATEGORIES}

    if not today_news.empty and "검색키워드" in today_news.columns:
        for _, row in today_news.iterrows():
            if str(row.get("sentiment", "pos")) == "neg":
                total_neg += 1
            counts[classify_category(row.get("검색키워드", ""), row.get("기사제목", ""))] += 1

    display_date = now_kst.strftime('%Y.%m.%d')

    import random, string
    unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))

    # ── 상단: 총합 카드 (부정 기사 건수 배지 포함 — 위기 감지 핵심 지표) ──
    _neg_cls = "" if total_neg > 0 else " zero"
    st.markdown(f'''
<div class="ic-total-hero">
    <div class="ic-total-date">{display_date}</div>
    <div class="ic-total-sep"></div>
    <div class="ic-total-count">
        <span class="ic-total-num" id="total-{unique_id}" data-target="{total_today}">0</span>
        <span class="ic-total-unit">건</span>
    </div>
    <div class="ic-total-sep"></div>
    <div class="ic-neg-badge{_neg_cls}">🔻 부정 {total_neg}건</div>
</div>
''', unsafe_allow_html=True)

    # ── 하단: 키워드 카드 5개 (누르면 아래 기사 목록을 그 분류로 필터링) ──
    selected = st.session_state.get(FILTER_STATE_KEY)
    with st.container(key="ic_kw_grid"):
        for cat, label, tier, id_prefix in CATEGORIES:
            cnt = counts[cat]
            pct = (cnt / total_today * 100) if total_today > 0 else 0
            state = "" if not selected else (" ic-kw-active" if selected == cat else " ic-kw-dim")
            with st.container(key=f"ic_card_{cat}"):
                st.markdown(f'''
<div class="ic-kw-card ic-kw-{tier}{state}">
  <div class="ic-kw-label">{label}</div>
  <div class="ic-kw-num" id="{id_prefix}-{unique_id}" data-target="{cnt}">0</div>
  <div class="ic-kw-pct">{pct:.1f}%</div>
</div>
''', unsafe_allow_html=True)
                st.button(f"{label} 기사만 보기", key=f"ic_btn_{cat}",
                          on_click=_toggle_filter, args=(cat,),
                          help=f"{label} 기사만 보기 (다시 누르면 전체)")

    # 카운트 애니메이션
    components.html(f'''
<script>
(function() {{
    var ids = ['total-{unique_id}','posco-intl-{unique_id}','posco-{unique_id}',
               'mobility-{unique_id}','samcheok-{unique_id}','others-{unique_id}'];

    function easeOutQuart(t) {{ return 1 - Math.pow(1 - t, 4); }}

    ids.forEach(function(id) {{
        var elem = window.parent.document.getElementById(id);
        if (!elem) return;
        var target = parseInt(elem.getAttribute('data-target'));
        var duration = 700 + Math.random() * 400;
        var startTime = performance.now();
        function animate(now) {{
            var p = Math.min((now - startTime) / duration, 1);
            elem.textContent = Math.floor(easeOutQuart(p) * target);
            if (p < 1) requestAnimationFrame(animate);
        }}
        requestAnimationFrame(animate);
    }});
}})();
</script>
''', height=0)
