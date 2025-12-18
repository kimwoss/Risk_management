"""
출입매체 현황 대시보드 컴포넌트
총 출입매체 수와 구분별(종합지, 경제지, 통신사, 석간지, 영자지, 경제TV, 온라인지) 통계 표시
"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pytz


def render_publisher_dashboard(media_contacts: dict, show_live: bool = True):
    """
    출입매체 현황 대시보드 렌더링

    Args:
        media_contacts: 언론사 정보 딕셔너리 {언론사명: {구분: "종합지", ...}}
        show_live: LIVE 뱃지 표시 여부
    """
    # 통계 계산
    total = len(media_contacts)

    # 구분별 카운트
    category_counts = {
        '종합지': 0,
        '경제지': 0,
        '통신사': 0,
        '석간지': 0,
        '영자지': 0,
        '경제TV': 0,
        '온라인지': 0
    }

    for media_name, media_info in media_contacts.items():
        category = media_info.get('구분', '기타')
        if category in category_counts:
            category_counts[category] += 1

    # 퍼센트 계산
    category_pcts = {}
    for cat, count in category_counts.items():
        category_pcts[cat] = (count / total * 100) if total > 0 else 0

    kst = pytz.timezone('Asia/Seoul')
    now_kst = datetime.now(kst)
    last_updated = now_kst.strftime('%Y-%m-%d %H:%M KST')

    # 애니메이션을 위한 고유 ID
    import random
    import string
    unique_id = ''.join(random.choices(string.ascii_lowercase, k=8))

    # CSS 스타일
    st.markdown("""
    <style>
    div[data-testid="column"] { padding: 0 4px !important; }
    .pub-dash-container { background: linear-gradient(145deg, #1a1a2e 0%, #16213e 100%); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
    .pub-dash-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.08); }
    .pub-dash-title { color: #e0e0e0; font-size: 1.1rem; font-weight: 600; }
    .pub-live-badge { background: rgba(239,68,68,0.15); color: #ef4444; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 700; }
    .pub-last-updated { color: #888; font-size: 0.75rem; margin-left: 12px; }

    .pub-card { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 16px 12px; border-top: 3px solid; text-align: center; transition: all 0.2s ease; min-height: 120px; display: flex; flex-direction: column; justify-content: center; }
    .pub-card:hover { background: rgba(255,255,255,0.06); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }

    .pub-card.total { border-top-color: #6366f1; background: rgba(99,102,241,0.05); }
    .pub-card.general { border-top-color: #3b82f6; }
    .pub-card.economic { border-top-color: #10b981; }
    .pub-card.agency { border-top-color: #f59e0b; }
    .pub-card.evening { border-top-color: #8b5cf6; }
    .pub-card.english { border-top-color: #ec4899; }
    .pub-card.tv { border-top-color: #ef4444; }
    .pub-card.online { border-top-color: #06b6d4; }

    .pub-label { font-size: 0.75rem; font-weight: 600; margin-bottom: 8px; }
    .pub-card.total .pub-label { color: #6366f1; }
    .pub-card.general .pub-label { color: #3b82f6; }
    .pub-card.economic .pub-label { color: #10b981; }
    .pub-card.agency .pub-label { color: #f59e0b; }
    .pub-card.evening .pub-label { color: #8b5cf6; }
    .pub-card.english .pub-label { color: #ec4899; }
    .pub-card.tv .pub-label { color: #ef4444; }
    .pub-card.online .pub-label { color: #06b6d4; }

    .pub-value { color: #e0e0e0; font-size: 1.8rem; font-weight: 700; margin: 6px 0; }
    .pub-card.total .pub-value { font-size: 2.4rem; color: #fff; }

    .pub-pct { color: #888; font-size: 0.7rem; margin-top: 4px; }

    @media (max-width: 1200px) {
        div[data-testid="column"] { flex: 1 1 calc(25% - 8px) !important; min-width: 120px !important; }
    }
    @media (max-width: 768px) {
        div[data-testid="column"] { flex: 1 1 calc(33.333% - 8px) !important; min-width: 100px !important; }
    }
    @media (max-width: 480px) {
        div[data-testid="column"] { flex: 1 1 calc(50% - 8px) !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    live = f'<span class="pub-live-badge">LIVE</span>' if show_live else ''

    st.markdown(f'<div class="pub-dash-container"><div class="pub-dash-header"><span class="pub-dash-title">📰 출입매체 현황</span><span>{live}<span class="pub-last-updated">Last updated: {last_updated}</span></span></div>', unsafe_allow_html=True)

    # 총 출입매체 수 (첫 번째 행에 단독 배치)
    col_total = st.columns([1])[0]
    with col_total:
        st.markdown(f'<div class="pub-card total"><div class="pub-label">총 출입매체</div><div class="pub-value" id="total-{unique_id}" data-target="{total}">0</div></div>', unsafe_allow_html=True)

    # 구분별 통계 (두 번째 행에 7개 배치)
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    with col1:
        st.markdown(f'<div class="pub-card general"><div class="pub-label">종합지</div><div class="pub-value" id="general-{unique_id}" data-target="{category_counts["종합지"]}">0</div><div class="pub-pct">{category_pcts["종합지"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="pub-card economic"><div class="pub-label">경제지</div><div class="pub-value" id="economic-{unique_id}" data-target="{category_counts["경제지"]}">0</div><div class="pub-pct">{category_pcts["경제지"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div class="pub-card agency"><div class="pub-label">통신사</div><div class="pub-value" id="agency-{unique_id}" data-target="{category_counts["통신사"]}">0</div><div class="pub-pct">{category_pcts["통신사"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col4:
        st.markdown(f'<div class="pub-card evening"><div class="pub-label">석간지</div><div class="pub-value" id="evening-{unique_id}" data-target="{category_counts["석간지"]}">0</div><div class="pub-pct">{category_pcts["석간지"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col5:
        st.markdown(f'<div class="pub-card english"><div class="pub-label">영자지</div><div class="pub-value" id="english-{unique_id}" data-target="{category_counts["영자지"]}">0</div><div class="pub-pct">{category_pcts["영자지"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col6:
        st.markdown(f'<div class="pub-card tv"><div class="pub-label">경제TV</div><div class="pub-value" id="tv-{unique_id}" data-target="{category_counts["경제TV"]}">0</div><div class="pub-pct">{category_pcts["경제TV"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col7:
        st.markdown(f'<div class="pub-card online"><div class="pub-label">온라인지</div><div class="pub-value" id="online-{unique_id}" data-target="{category_counts["온라인지"]}">0</div><div class="pub-pct">{category_pcts["온라인지"]:.1f}%</div></div>', unsafe_allow_html=True)

    # 카운트 애니메이션 JavaScript
    animation_script = f'''
    <script>
    (function() {{
        function animateCount() {{
            const ids = ['total-{unique_id}', 'general-{unique_id}', 'economic-{unique_id}', 'agency-{unique_id}', 'evening-{unique_id}', 'english-{unique_id}', 'tv-{unique_id}', 'online-{unique_id}'];

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
