"""
keyword_insight.py
P-IRIS 키워드 인사이트 브리핑 페이지
streamlit_app.py의 page_keyword_insight() 함수에서 호출됨
"""
import streamlit as st

from modules.naver_news import fetch_naver_news, get_latest_articles
from modules.naver_datalab import safe_fetch_trend, extract_trend_data
from modules.journalist_db import load_journalist_db, match_journalists
from modules.response_history import load_response_history, search_response_history
from modules.insight_generator import generate_insight
from modules.ui_components import (
    inject_custom_css,
    render_page_header,
    render_section_header,
    render_kpi_cards,
    render_tone_bar,
    render_cross_analysis,
    render_latest_articles,
    render_news_volume_chart,
    render_trend_chart,
    render_top_media_chart,
    render_issue_clusters,
    render_company_exposure,
    render_competitor_table,
    render_journalist_matches,
    render_past_responses,
    render_risk_opportunity,
    render_action_cards,
    render_footer,
)


@st.cache_data(ttl=600)
def _cached_fetch_news(keyword: str):
    return fetch_naver_news(keyword)


@st.cache_data(ttl=600)
def _cached_fetch_trend_30d(keyword: str):
    return safe_fetch_trend(keyword, days=30, time_unit="date")


@st.cache_data(ttl=600)
def _cached_fetch_trend_1y(keyword: str):
    return safe_fetch_trend(keyword, days=365, time_unit="month")


def render_keyword_insight_page():
    """키워드 인사이트 페이지 진입점"""
    inject_custom_css()
    render_page_header()

    # ── 키워드 입력 ──
    col_input, col_btn = st.columns([5, 1], gap="small")
    with col_input:
        keyword = st.text_input(
            "검색 키워드",
            placeholder="예: 구동모터코어, LNG벙커링, 팜오일",
            key="ki_keyword_input",
            label_visibility="collapsed",
        )
    with col_btn:
        analyze_btn = st.button("🔍 분석", type="primary", use_container_width=True, key="ki_analyze_btn")

    if not (analyze_btn and keyword):
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; color:#475569">
            <div style="font-size:40px; margin-bottom:16px">🔍</div>
            <div style="font-size:16px; font-weight:600; color:#64748b">키워드를 입력하고 분석을 시작하세요</div>
            <div style="font-size:13px; color:#475569; margin-top:8px">
                뉴스 보도량·검색 트렌드·내부 DB를 교차 분석한 임원용 브리핑을 생성합니다
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── 헤더 재렌더 (키워드 포함) ──
    render_page_header(keyword)

    # ── Step 1-A: 뉴스 수집 ──
    with st.spinner("📰 뉴스 수집 중..."):
        news_items = _cached_fetch_news(keyword)

    if not news_items:
        st.warning(f"'{keyword}'에 대한 뉴스 검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
        return

    latest_articles = get_latest_articles(news_items, n=5)

    # ── Step 1-B: 검색 트렌드 ──
    with st.spinner("📊 검색 트렌드 수집 중..."):
        trend_30d = _cached_fetch_trend_30d(keyword)
        trend_1y  = _cached_fetch_trend_1y(keyword)

    # ── Step 2: 내부 DB 조회 ──
    with st.spinner("🗂️ 내부 데이터 조회 중..."):
        journalist_db = load_journalist_db()
        history_db    = load_response_history()
        journalists   = match_journalists(keyword, news_items, journalist_db)
        history       = search_response_history(keyword, history_db)

    # ── Step 3: GPT 분석 ──
    with st.spinner("🤖 AI 분석 중... (30~60초 소요)"):
        insight = generate_insight(
            keyword=keyword,
            news_items=news_items,
            trend_30d=trend_30d,
            trend_1y=trend_1y,
            journalists=journalists.to_dict("records") if not journalists.empty else [],
            history=history.to_dict("records") if not history.empty else [],
        )

    # ── Step 4: UI 렌더링 ──
    st.markdown("---")

    # KPI 카드 (상단 5열)
    _render_kpi(insight)

    # ─── 섹션 A: 상황 인식 ───
    render_section_header("📡", "상황 인식")
    col_a1, col_a2 = st.columns(2, gap="medium")
    with col_a1:
        render_news_volume_chart(news_items, keyword)
    with col_a2:
        trend_data_30d = extract_trend_data(trend_30d)
        render_trend_chart(trend_data_30d, "검색 관심도 추이 (최근 30일)", time_unit="date")

    sta = insight.get("search_trend_analysis", {})
    render_cross_analysis(sta.get("news_vs_search", "비활성이슈"), sta.get("summary", ""))

    col_b1, col_b2 = st.columns(2, gap="medium")
    with col_b1:
        mp = insight.get("media_pulse", {})
        render_section_header("🎭", "보도 논조 분석")
        render_tone_bar(
            mp.get("tone_positive_pct", 0),
            mp.get("tone_neutral_pct", 0),
            mp.get("tone_negative_pct", 0),
        )
        st.markdown(f'<div style="font-size:13px; color:#94a3b8; margin-top:8px">{mp.get("summary", "")}</div>', unsafe_allow_html=True)

        trend_data_1y = extract_trend_data(trend_1y)
        render_trend_chart(trend_data_1y, "검색 관심도 추이 (최근 1년, 월별)", time_unit="month")

    with col_b2:
        render_top_media_chart(mp.get("top_media", []))

    render_issue_clusters(insight.get("issue_clusters", []))

    # ─── 섹션 B: 최신기사 TOP 5 ───
    st.markdown("---")
    render_latest_articles(latest_articles)

    # ─── 섹션 C: 자사 포지션 ───
    st.markdown("---")
    col_c1, col_c2 = st.columns(2, gap="medium")
    with col_c1:
        render_company_exposure(insight.get("company_exposure", {}))
    with col_c2:
        render_competitor_table(insight.get("competitor_landscape", []))

    # ─── 섹션 D: 내부 자산 연결 ───
    st.markdown("---")
    col_d1, col_d2 = st.columns(2, gap="medium")
    with col_d1:
        render_journalist_matches(insight.get("journalist_matches", []))
    with col_d2:
        render_past_responses(insight.get("past_responses", []))

    # ─── 섹션 E: 판단 보조 ───
    st.markdown("---")
    col_e1, col_e2 = st.columns(2, gap="medium")
    with col_e1:
        render_risk_opportunity(insight.get("risk_opportunity", {}))
    with col_e2:
        render_action_cards(insight.get("action_recommendations", []))

    # 푸터
    render_footer(keyword)


def _render_kpi(insight: dict):
    """KPI 카드 5열 렌더링 (ui_components.render_kpi_cards에서 st 직접 사용하면 안 되므로 여기서 처리)"""
    mp  = insight.get("media_pulse", {})
    ro  = insight.get("risk_opportunity", {})
    sta = insight.get("search_trend_analysis", {})

    TREND_ICONS = {"급증": "🔺", "증가": "↑", "보합": "→", "감소": "↓", "급감": "🔻"}

    trend_label = mp.get("trend", "보합")
    trend_icon  = TREND_ICONS.get(trend_label, "→")
    crisis      = ro.get("crisis_level", "관심")
    interest    = sta.get("current_interest", 0)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("7일 기사 수",   f"{mp.get('total_7d', 0):,}건")
    c2.metric("30일 기사 수",  f"{mp.get('total_30d', 0):,}건")
    c3.metric("보도 추세",     f"{trend_icon} {trend_label}")
    c4.metric("검색 관심도",   f"{interest}/100",
              help="네이버 데이터랩 기준 상대값 (최대=100, 절대 검색량 아님)")
    c5.metric("위기 등급",     crisis)
