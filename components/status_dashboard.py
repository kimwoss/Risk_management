"""
전문적인 실시간 모니터링 대시보드 카드 컴포넌트

다크 테마 기반의 깔끔한 대시보드 UI를 제공합니다.
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

    # LIVE 배지 HTML
    live_badge_html = f"""
        <div class="live-badge">
            <div class="live-dot"></div>
            LIVE
        </div>
    """ if show_live else ""

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
        margin-bottom: 24px;
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

    .dashboard-body {{
        display: grid;
        grid-template-columns: 1fr 2fr;
        gap: 32px;
        align-items: center;
    }}

    .total-section {{
        text-align: left;
        padding-right: 24px;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .total-label {{
        color: #999;
        font-size: 0.85em;
        font-weight: 500;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }}

    .total-number {{
        color: #ffffff;
        font-size: 3.2em;
        font-weight: 700;
        line-height: 1;
        letter-spacing: -1px;
    }}

    .status-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }}

    .status-card {{
        background: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        padding: 14px 16px;
        border-left: 3px solid;
        transition: all 0.2s ease;
    }}

    .status-card:hover {{
        background: rgba(255, 255, 255, 0.06);
        transform: translateX(2px);
    }}

    .status-card.interest {{
        border-left-color: #22c55e;
    }}

    .status-card.caution {{
        border-left-color: #f59e0b;
    }}

    .status-card.crisis {{
        border-left-color: #f97316;
    }}

    .status-card.emergency {{
        border-left-color: #ef4444;
    }}

    .status-label {{
        font-size: 0.8em;
        font-weight: 600;
        margin-bottom: 6px;
        letter-spacing: 0.3px;
    }}

    .status-card.interest .status-label {{
        color: #22c55e;
    }}

    .status-card.caution .status-label {{
        color: #f59e0b;
    }}

    .status-card.crisis .status-label {{
        color: #f97316;
    }}

    .status-card.emergency .status-label {{
        color: #ef4444;
    }}

    .status-value {{
        color: #e0e0e0;
        font-size: 1.6em;
        font-weight: 700;
        line-height: 1;
        margin-bottom: 4px;
    }}

    .status-percentage {{
        color: #888;
        font-size: 0.75em;
        font-weight: 500;
    }}

    /* 반응형 디자인 */
    @media (max-width: 768px) {{
        .dashboard-body {{
            grid-template-columns: 1fr;
            gap: 24px;
        }}

        .total-section {{
            border-right: none;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-right: 0;
            padding-bottom: 24px;
        }}

        .status-grid {{
            grid-template-columns: 1fr;
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

        <div class="dashboard-body">
            <div class="total-section">
                <div class="total-label">총 건수</div>
                <div class="total-number">{total:,}</div>
            </div>

            <div class="status-grid">
                <div class="status-card interest">
                    <div class="status-label">관심</div>
                    <div class="status-value">{관심_count:,}</div>
                    <div class="status-percentage">{관심_pct:.1f}%</div>
                </div>

                <div class="status-card caution">
                    <div class="status-label">주의</div>
                    <div class="status-value">{주의_count:,}</div>
                    <div class="status-percentage">{주의_pct:.1f}%</div>
                </div>

                <div class="status-card crisis">
                    <div class="status-label">위기</div>
                    <div class="status-value">{위기_count:,}</div>
                    <div class="status-percentage">{위기_pct:.1f}%</div>
                </div>

                <div class="status-card emergency">
                    <div class="status-label">비상</div>
                    <div class="status-value">{비상_count:,}</div>
                    <div class="status-percentage">{비상_pct:.1f}%</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
