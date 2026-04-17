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

    # 헤더 없이 바로 컨테이너 시작
    st.markdown('<div class="iris-dash">', unsafe_allow_html=True)

    # 한 줄에 5개 카드 배치
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f'<div class="iris-card ic-total"><div class="ic-label">총 건수</div><div class="ic-value" id="total-{unique_id}" data-target="{total}">0</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="iris-card ic-pos"><div class="ic-label">관심</div><div class="ic-value" id="interest-{unique_id}" data-target="{관심_count}">0</div><div class="ic-pct">{관심_pct:.1f}%</div></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div class="iris-card ic-warn"><div class="ic-label">주의</div><div class="ic-value" id="caution-{unique_id}" data-target="{주의_count}">0</div><div class="ic-pct">{주의_pct:.1f}%</div></div>', unsafe_allow_html=True)

    with col4:
        st.markdown(f'<div class="iris-card ic-orange"><div class="ic-label">위기</div><div class="ic-value" id="crisis-{unique_id}" data-target="{위기_count}">0</div><div class="ic-pct">{위기_pct:.1f}%</div></div>', unsafe_allow_html=True)

    with col5:
        st.markdown(f'<div class="iris-card ic-neg"><div class="ic-label">비상</div><div class="ic-value" id="emergency-{unique_id}" data-target="{비상_count}">0</div><div class="ic-pct">{비상_pct:.1f}%</div></div>', unsafe_allow_html=True)

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
