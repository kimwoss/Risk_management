"""
keyword_insight.py
P-IRIS 키워드 인사이트 브리핑 페이지 (리팩토링)

API 호출 원칙:
  - 네이버 뉴스 검색: 1회 (최대 100건)
  - 네이버 데이터랩 트렌드: 1회 (30일)
  - GPT: 1회 (call_gpt_once — 재호출 금지)
  - 동일 키워드 1시간 이내 재검색: session_state 캐시 사용
"""
import time
import streamlit as st

from modules.naver_news import fetch_naver_news, get_latest_articles
from modules.naver_datalab import safe_fetch_trend, extract_trend_data
from modules.response_history import load_response_history, search_response_history
from modules.insight_generator import call_gpt_once
from modules.ui_components import (
    inject_custom_css,
    render_page_header,
    render_section_header,
    render_tone_bar,
    render_news_volume_chart,
    render_top_media_chart,
    render_issue_clusters,
    render_competitor_table,
    render_past_responses,
    render_risk_signals,
    render_action_list,
    render_footer,
    render_summary_box,
)

# ── 캐시 키 상수 ──
_CACHE_PREFIX = "ki_raw_"
_CACHE_TTL    = 3600  # 1시간


# ─────────────────────────────────────────────────────────────
# 내부 헬퍼: 원시 데이터 session_state 캐시
# ─────────────────────────────────────────────────────────────

def _raw_cache_key(keyword: str) -> str:
    return f"{_CACHE_PREFIX}{keyword}"


def _load_raw(keyword: str) -> dict | None:
    entry = st.session_state.get(_raw_cache_key(keyword))
    if not entry:
        return None
    if time.time() - entry.get("ts", 0) > _CACHE_TTL:
        del st.session_state[_raw_cache_key(keyword)]
        return None
    return entry


def _save_raw(keyword: str, news_items: list, trend_data: list):
    st.session_state[_raw_cache_key(keyword)] = {
        "ts":         time.time(),
        "news_items": news_items,
        "trend_data": trend_data,
    }


# ─────────────────────────────────────────────────────────────
# 섹션 렌더 함수
# ─────────────────────────────────────────────────────────────

def render_kpi_bar(news_items: list[dict], trend_data: list[dict], gpt: dict):
    """② 핵심 지표 바: 7일 기사 수 / 30일 기사 수 / 보도 추세 / 검색 관심도 / 위기 등급"""
    count_7d  = sum(1 for a in news_items if a.get("is_within_7d"))
    count_30d = sum(1 for a in news_items if a.get("is_within_30d"))

    trend_label = gpt.get("trend", "보합")
    TREND_ICONS = {"급증": "🔺", "증가": "↑", "보합": "→", "감소": "↓", "급감": "🔻"}
    trend_icon  = TREND_ICONS.get(trend_label, "→")

    interest = max((d.get("ratio", 0) for d in trend_data), default=0) if trend_data else 0
    crisis   = gpt.get("crisis_level", "관심")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("7일 기사 수",  f"{count_7d:,}건")
    c2.metric("30일 기사 수", f"{count_30d:,}건")
    c3.metric("보도 추세",    f"{trend_icon} {trend_label}")
    c4.metric("검색 관심도",  f"{int(interest)}/100",
              help="네이버 데이터랩 기준 상대값 (최대=100, 절대 검색량 아님)")
    c5.metric("위기 등급",    crisis)


def render_summary(gpt: dict):
    """③ AI 요약 강조 박스"""
    render_summary_box(gpt.get("summary", "요약 정보 없음"))


def render_charts(news_items: list[dict], trend_data: list[dict], gpt: dict, keyword: str):
    """④ 보도량 추이 차트 + 논조 바 + TOP 5 매체 (가로 배치)"""
    render_section_header("📊", "보도 현황")

    col_chart, col_right = st.columns([2, 1], gap="medium")

    with col_chart:
        render_news_volume_chart(news_items, keyword)

        # 논조 바 (1줄)
        sent = gpt.get("sentiment", {})
        pos  = sent.get("positive", 0)
        neu  = sent.get("neutral",  0)
        neg  = sent.get("negative", 0)
        render_tone_bar(pos, neu, neg)

    with col_right:
        top_media = gpt.get("top_media", [])
        render_top_media_chart(top_media)


def render_issues(gpt: dict):
    """⑤ 이슈 클러스터: 카드 3개, 제목+1줄"""
    render_issue_clusters(gpt.get("issues", []))


def render_articles(news_items: list[dict]):
    """⑥ 최신 기사 TOP 5"""
    render_section_header("📰", "최신 기사 TOP 5", "네이버 뉴스 API 기준 최신순")
    articles = get_latest_articles(news_items, n=5)
    if not articles:
        st.info("수집된 기사가 없습니다.")
        return
    for a in articles:
        desc = a.get("description", "")
        desc_preview = desc[:120] + ("..." if len(desc) > 120 else "")
        st.markdown(f"""
        <div class="article-card">
            <a href="{a.get('link', '#')}" target="_blank" class="article-title">
                {a.get('title', '제목 없음')}
            </a>
            <div class="article-meta">
                <span class="badge badge-blue">{a.get('media', '')}</span>
                &nbsp; {a.get('date', '')} {a.get('time', '')}
            </div>
            <div class="article-desc">{desc_preview}</div>
        </div>
        """, unsafe_allow_html=True)


def render_competitors(gpt: dict):
    """⑦ 경쟁사·기관 동향 (간소화 테이블)"""
    render_competitor_table(gpt.get("competitors", []))


def render_risk_action(gpt: dict):
    """⑧ 리스크·기회 시그널 + 커뮤니케이션 액션 제안 (2열 나란히)"""
    col_risk, col_act = st.columns(2, gap="medium")
    with col_risk:
        render_risk_signals(
            risks=gpt.get("risks", []),
            opportunities=gpt.get("opportunities", []),
        )
    with col_act:
        render_action_list(gpt.get("actions", []))


def render_history(keyword: str):
    """⑨ 과거 대응이력: expander 접기 (기본 collapsed)"""
    history_db = load_response_history()
    history    = search_response_history(keyword, history_db)
    records    = history.to_dict("records") if not history.empty else []
    with st.expander("📁 과거 대응이력 (클릭하여 펼치기)", expanded=False):
        render_past_responses(records)


# ─────────────────────────────────────────────────────────────
# 페이지 진입점
# ─────────────────────────────────────────────────────────────

def render_keyword_insight_page():
    """키워드 인사이트 페이지 진입점"""
    inject_custom_css()
    render_page_header()

    # ① 헤더: 키워드 입력 + 검색 버튼
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
                뉴스 보도량·검색 트렌드·AI 분석을 교차 결합한 임원용 브리핑을 생성합니다
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── 헤더 재렌더 (키워드 포함) ──
    render_page_header(keyword)

    # ── 원시 데이터 수집 (캐시 우선) ──
    raw = _load_raw(keyword)
    if raw is None:
        with st.spinner("📰 뉴스 수집 중... (네이버 검색 API 1회)"):
            news_items = fetch_naver_news(keyword)

        if not news_items:
            st.warning(f"'{keyword}'에 대한 뉴스 검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
            return

        with st.spinner("📊 검색 트렌드 수집 중... (데이터랩 API 1회)"):
            trend_30d  = safe_fetch_trend(keyword, days=30, time_unit="date")
            trend_data = extract_trend_data(trend_30d)

        _save_raw(keyword, news_items, trend_data)
    else:
        news_items = raw["news_items"]
        trend_data = raw["trend_data"]

    # ── GPT 단일 호출 (session_state 캐시 내장) ──
    with st.spinner("🤖 AI 분석 중... (GPT 1회 호출)"):
        gpt = call_gpt_once(keyword, news_items)

    st.markdown("---")

    # ② 핵심 지표 바
    render_kpi_bar(news_items, trend_data, gpt)

    st.markdown("---")

    # ③ AI 요약
    render_summary(gpt)

    # ④ 보도량 차트 + 논조 바 + TOP 5 매체
    render_charts(news_items, trend_data, gpt, keyword)

    st.markdown("---")

    # ⑤ 이슈 클러스터
    render_issues(gpt)

    st.markdown("---")

    # ⑥ 최신 기사 TOP 5
    render_articles(news_items)

    st.markdown("---")

    # ⑦ 경쟁사·기관 동향
    render_competitors(gpt)

    st.markdown("---")

    # ⑧ 리스크·기회 + 액션 제안 (2열)
    render_risk_action(gpt)

    st.markdown("---")

    # ⑨ 과거 대응이력 (접힌 상태)
    render_history(keyword)

    # 푸터
    render_footer(keyword)
