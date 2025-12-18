"""
전문적인 실시간 모니터링 대시보드 카드 컴포넌트
"""
import streamlit as st
from datetime import datetime
import pytz


def render_status_dashboard(total: int, status_counts: dict, year: int = 2025, show_live: bool = True):
    관심_count = status_counts.get('관심', 0)
    주의_count = status_counts.get('주의', 0)
    위기_count = status_counts.get('위기', 0)
    비상_count = status_counts.get('비상', 0)

    관심_pct = (관심_count / total * 100) if total > 0 else 0
    주의_pct = (주의_count / total * 100) if total > 0 else 0
    위기_pct = (위기_count / total * 100) if total > 0 else 0
    비상_pct = (비상_count / total * 100) if total > 0 else 0

    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst)
    last_updated = now_kst.strftime('%Y-%m-%d %H:%M KST')

    st.markdown("""
    <style>
    div[data-testid="column"] { padding: 0 8px !important; }
    .dash-container { background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 24px; }
    .dash-header { display: flex; justify-content: space-between; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.08); }
    .dash-title { color: #e0e0e0; font-size: 1.1rem; font-weight: 600; }
    .live-badge { background: rgba(239,68,68,0.15); color: #ef4444; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; }
    .last-updated { color: #888; font-size: 0.75rem; margin-left: 12px; }
    .total-card { background: rgba(99,102,241,0.05); border: 1px solid rgba(99,102,241,0.2); border-radius: 12px; padding: 24px; text-align: center; }
    .total-label { color: #6366f1; font-size: 0.9rem; font-weight: 600; margin-bottom: 12px; }
    .total-value { color: #fff; font-size: 3rem; font-weight: 700; margin: 0; }
    .status-card { background: rgba(255,255,255,0.03); border-radius: 10px; padding: 16px; border-left: 3px solid; margin-bottom: 8px; }
    .status-card.interest { border-left-color: #22c55e; }
    .status-card.caution { border-left-color: #f59e0b; }
    .status-card.crisis { border-left-color: #f97316; }
    .status-card.emergency { border-left-color: #ef4444; }
    .status-label { font-size: 0.85rem; font-weight: 600; margin-bottom: 8px; }
    .status-card.interest .status-label { color: #22c55e; }
    .status-card.caution .status-label { color: #f59e0b; }
    .status-card.crisis .status-label { color: #f97316; }
    .status-card.emergency .status-label { color: #ef4444; }
    .status-value { color: #e0e0e0; font-size: 1.8rem; font-weight: 700; margin: 0 0 4px 0; }
    .status-pct { color: #888; font-size: 0.8rem; margin: 0; }
    </style>
    """, unsafe_allow_html=True)

    live = f'<span class="live-badge">LIVE</span>' if show_live else ''
    
    st.markdown(f'<div class="dash-container"><div class="dash-header"><span class="dash-title">📊 {year} 누적 이슈 현황</span><span>{live}<span class="last-updated">Last updated: {last_updated}</span></span></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f'<div class="total-card"><div class="total-label">총 건수</div><h1 class="total-value">{total:,}</h1></div>', unsafe_allow_html=True)
    
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="status-card interest"><div class="status-label">관심</div><h2 class="status-value">{관심_count:,}</h2><p class="status-pct">{관심_pct:.1f}%</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="status-card crisis"><div class="status-label">위기</div><h2 class="status-value">{위기_count:,}</h2><p class="status-pct">{위기_pct:.1f}%</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="status-card caution"><div class="status-label">주의</div><h2 class="status-value">{주의_count:,}</h2><p class="status-pct">{주의_pct:.1f}%</p></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="status-card emergency"><div class="status-label">비상</div><h2 class="status-value">{비상_count:,}</h2><p class="status-pct">{비상_pct:.1f}%</p></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
