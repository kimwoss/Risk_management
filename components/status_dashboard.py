"""
전문적인 실시간 모니터링 대시보드 카드 컴포넌트

다크 테마 기반의 깔끔한 대시보드 UI를 제공합니다.
카운트업 애니메이션으로 실시간 집계 느낌을 줍니다.
"""
import streamlit as st
from datetime import datetime
import pytz


def render_status_dashboard(
    total: int,
    status_counts: dict,
    year: int = 2025,
    show_live: bool = True
):
    """
    실시간 모니터링 스타일의 대시보드 카드를 렌더링합니다.

    Args:
        total: 총 건수
        status_counts: 상태별 건수 딕셔너리 {'관심': 263, '주의': 26, '위기': 1, '비상': 0}
        year: 표시할 연도 (기본값: 2025)
        show_live: LIVE 배지 표시 여부 (기본값: True)
    """

    # 각 상태별 건수 및 비율 계산
    관심_count = status_counts.get('관심', 0)
    주의_count = status_counts.get('주의', 0)
    위기_count = status_counts.get('위기', 0)
    비상_count = status_counts.get('비상', 0)

    관심_pct = (관심_count / total * 100) if total > 0 else 0
    주의_pct = (주의_count / total * 100) if total > 0 else 0
    위기_pct = (위기_count / total * 100) if total > 0 else 0
    비상_pct = (비상_count / total * 100) if total > 0 else 0

    # 현재 시간 (KST)
    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst)
    last_updated = now_kst.strftime('%Y-%m-%d %H:%M KST')

    # LIVE 배지 HTML (조건부, 한 줄로)
    live_badge_html = '<div class="live-badge"><div class="live-dot"></div>LIVE</div>' if show_live else ''

    # 애니메이션 플래그 체크 (리런 시 재애니메이션 방지)
    # 고유 키를 사용하여 이 대시보드의 애니메이션 여부를 추적
    dashboard_key = f"dashboard_animated_{year}"
    if dashboard_key not in st.session_state:
        st.session_state[dashboard_key] = False
        should_animate = True
    else:
        should_animate = False

    # 애니메이션 실행 후 플래그 설정
    if should_animate:
        st.session_state[dashboard_key] = True

    # CSS + HTML을 하나의 블록으로 렌더링
    st.markdown(f"""
<style>
.dashboard-card {{
    background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}}

.dashboard-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}}

.dashboard-title {{
    color: #e0e0e0;
    font-size: 0.95em;
    font-weight: 600;
    letter-spacing: 0.3px;
}}

.dashboard-meta {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.live-badge {{
    display: inline-flex;
    align-items: center;
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.75em;
    font-weight: 700;
    letter-spacing: 0.5px;
}}

.live-dot {{
    width: 6px;
    height: 6px;
    background: #ef4444;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s ease-in-out infinite;
}}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.4; }}
}}

.last-updated {{
    color: #888;
    font-size: 0.75em;
    font-weight: 500;
}}

/* 한 줄 5개 카드 레이아웃 */
.status-row {{
    display: flex;
    gap: 16px;
    align-items: stretch;
}}

.status-card {{
    flex: 1;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    padding: 20px 16px;
    border-top: 3px solid;
    transition: all 0.2s ease;
    min-width: 0; /* flex 자식 요소가 넘치지 않도록 */
}}

.status-card:hover {{
    background: rgba(255, 255, 255, 0.06);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}}

/* 총 건수 카드 - 가장 강조 */
.status-card.total {{
    border-top-color: #6366f1;
    background: rgba(99, 102, 241, 0.05);
}}

.status-card.interest {{ border-top-color: #22c55e; }}
.status-card.caution {{ border-top-color: #f59e0b; }}
.status-card.crisis {{ border-top-color: #f97316; }}
.status-card.emergency {{ border-top-color: #ef4444; }}

.status-label {{
    font-size: 0.8em;
    font-weight: 600;
    margin-bottom: 12px;
    letter-spacing: 0.3px;
    color: #999;
}}

.status-card.total .status-label {{ color: #6366f1; }}
.status-card.interest .status-label {{ color: #22c55e; }}
.status-card.caution .status-label {{ color: #f59e0b; }}
.status-card.crisis .status-label {{ color: #f97316; }}
.status-card.emergency .status-label {{ color: #ef4444; }}

.status-value {{
    color: #e0e0e0;
    font-size: 2.2em;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 8px;
    font-variant-numeric: tabular-nums; /* 숫자 정렬 */
}}

/* 총 건수는 더 크게 */
.status-card.total .status-value {{
    font-size: 2.8em;
    color: #ffffff;
}}

.status-percentage {{
    color: #888;
    font-size: 0.75em;
    font-weight: 500;
}}

/* 반응형: 768px 이하에서 3+2 레이아웃 */
@media (max-width: 768px) {{
    .status-row {{
        flex-wrap: wrap;
    }}

    .status-card {{
        flex: 1 1 calc(33.333% - 12px); /* 3개씩 */
        min-width: 100px;
    }}

    /* 총 건수는 첫 줄에 혼자 */
    .status-card.total {{
        flex: 1 1 100%;
    }}
}}

/* 더 작은 화면에서는 2열 */
@media (max-width: 480px) {{
    .status-card {{
        flex: 1 1 calc(50% - 8px);
    }}
}}
</style>

<div class="dashboard-card">
    <div class="dashboard-header">
        <div class="dashboard-title">📊 {year} 누적 이슈 현황</div>
        <div class="dashboard-meta">
            {live_badge_html}
            <div class="last-updated">Last updated: {last_updated}</div>
        </div>
    </div>

    <div class="status-row">
        <!-- 총 건수 -->
        <div class="status-card total">
            <div class="status-label">총 건수</div>
            <div class="status-value" data-target="{total}" data-animate="{str(should_animate).lower()}">{total if not should_animate else 0:,}</div>
        </div>

        <!-- 관심 -->
        <div class="status-card interest">
            <div class="status-label">관심</div>
            <div class="status-value" data-target="{관심_count}" data-animate="{str(should_animate).lower()}">{관심_count if not should_animate else 0:,}</div>
            <div class="status-percentage">{관심_pct:.1f}%</div>
        </div>

        <!-- 주의 -->
        <div class="status-card caution">
            <div class="status-label">주의</div>
            <div class="status-value" data-target="{주의_count}" data-animate="{str(should_animate).lower()}">{주의_count if not should_animate else 0:,}</div>
            <div class="status-percentage">{주의_pct:.1f}%</div>
        </div>

        <!-- 위기 -->
        <div class="status-card crisis">
            <div class="status-label">위기</div>
            <div class="status-value" data-target="{위기_count}" data-animate="{str(should_animate).lower()}">{위기_count if not should_animate else 0:,}</div>
            <div class="status-percentage">{위기_pct:.1f}%</div>
        </div>

        <!-- 비상 -->
        <div class="status-card emergency">
            <div class="status-label">비상</div>
            <div class="status-value" data-target="{비상_count}" data-animate="{str(should_animate).lower()}">{비상_count if not should_animate else 0:,}</div>
            <div class="status-percentage">{비상_pct:.1f}%</div>
        </div>
    </div>
</div>

<script>
(function() {{
    // 이미 실행된 경우 스킵
    const cards = document.querySelectorAll('.status-value[data-animate="true"]');
    if (cards.length === 0) return;

    // 카운트업 애니메이션 함수
    function animateCounter(element, target, duration) {{
        const start = 0;
        const range = target - start;
        const startTime = performance.now();

        function update(currentTime) {{
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // easeOutQuad 이징 함수 (부드러운 감속)
            const easeProgress = progress * (2 - progress);
            const current = Math.floor(start + range * easeProgress);

            // 천단위 콤마 포맷팅
            element.textContent = current.toLocaleString();

            if (progress < 1) {{
                requestAnimationFrame(update);
            }} else {{
                element.textContent = target.toLocaleString();
            }}
        }}

        requestAnimationFrame(update);
    }}

    // 각 카드에 랜덤 duration 적용 (700~1100ms)
    cards.forEach(card => {{
        const target = parseInt(card.getAttribute('data-target'));
        const duration = 700 + Math.random() * 400; // 700~1100ms
        animateCounter(card, target, duration);
    }});
}})();
</script>
""", unsafe_allow_html=True)
