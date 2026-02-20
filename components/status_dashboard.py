"""
전문적인 실시간 모니터링 대시보드 카드 컴포넌트
한 줄 5개 카드 레이아웃 (총건수/관심/주의/위기/비상)
"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pytz


def render_status_dashboard(total: int, status_counts: dict, year: int = None, show_live: bool = True):
    if year is None:
        year = datetime.now().year
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

    # 애니메이션 제어를 위한 고유 ID
    import random
    import string
    unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))

    st.markdown("""
    <style>
    .dash-container { background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
    .dash-container * { text-align: center; }
    .dash-container div[data-testid="column"] { padding: 0 6px !important; }

    .status-card { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 20px 16px; border-top: 3px solid; transition: all 0.2s ease; min-height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .status-card:hover { background: rgba(255,255,255,0.06); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
    
    .status-card.total { border-top-color: #6366f1; background: rgba(99,102,241,0.05); }
    .status-card.interest { border-top-color: #22c55e; }
    .status-card.caution { border-top-color: #f59e0b; }
    .status-card.crisis { border-top-color: #f97316; }
    .status-card.emergency { border-top-color: #ef4444; }
    
    .status-label { font-size: 0.8rem; font-weight: 600; margin-bottom: 12px; }
    .status-card.total .status-label { color: #6366f1; }
    .status-card.interest .status-label { color: #22c55e; }
    .status-card.caution .status-label { color: #f59e0b; }
    .status-card.crisis .status-label { color: #f97316; }
    .status-card.emergency .status-label { color: #ef4444; }
    
    .status-value { color: #e0e0e0; font-size: 2.2rem; font-weight: 700; margin: 8px 0; }
    .status-card.total .status-value { font-size: 2.8rem; color: #fff; }
    
    .status-pct { color: #888; font-size: 0.75rem; margin-top: 4px; }
    
    @media (max-width: 768px) {
        .dash-container div[data-testid="column"] { flex: 1 1 calc(33.333% - 12px) !important; min-width: 100px !important; }
    }
    @media (max-width: 480px) {
        .dash-container div[data-testid="column"] { flex: 1 1 calc(50% - 12px) !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    # 헤더 없이 바로 컨테이너 시작
    st.markdown('<div class="dash-container">', unsafe_allow_html=True)
    
    # 한 줄에 5개 카드 배치
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f'<div class="status-card total"><div class="status-label">총 건수</div><div class="status-value" id="total-{unique_id}" data-target="{total}">0</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="status-card interest"><div class="status-label">관심</div><div class="status-value" id="interest-{unique_id}" data-target="{관심_count}">0</div><div class="status-pct">{관심_pct:.1f}%</div></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div class="status-card caution"><div class="status-label">주의</div><div class="status-value" id="caution-{unique_id}" data-target="{주의_count}">0</div><div class="status-pct">{주의_pct:.1f}%</div></div>', unsafe_allow_html=True)

    with col4:
        st.markdown(f'<div class="status-card crisis"><div class="status-label">위기</div><div class="status-value" id="crisis-{unique_id}" data-target="{위기_count}">0</div><div class="status-pct">{위기_pct:.1f}%</div></div>', unsafe_allow_html=True)

    with col5:
        st.markdown(f'<div class="status-card emergency"><div class="status-label">비상</div><div class="status-value" id="emergency-{unique_id}" data-target="{비상_count}">0</div><div class="status-pct">{비상_pct:.1f}%</div></div>', unsafe_allow_html=True)

    # 카운트 애니메이션 JavaScript
    animation_script = f'''
    <script>
    (function() {{
        function animateCount() {{
            const ids = ['total-{unique_id}', 'interest-{unique_id}', 'caution-{unique_id}', 'crisis-{unique_id}', 'emergency-{unique_id}'];

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
