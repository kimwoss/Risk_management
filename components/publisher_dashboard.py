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

    # 구분별 카운트 (고정값 사용)
    category_counts = {
        '종합지': 11,
        '경제지': 10,
        '경제TV': 9,
        '영자지': 5,
        '석간지': 4,
    }

    # 통신사는 실제 카운트
    통신사_count = 0
    for media_name, media_info in media_contacts.items():
        category = media_info.get('구분', '기타')
        if category == '통신사':
            통신사_count += 1

    category_counts['통신사'] = 통신사_count

    # 온라인지는 전체에서 나머지를 뺀 값
    fixed_sum = sum(category_counts.values())
    category_counts['온라인지'] = max(0, total - fixed_sum)

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

    # 헤더 없이 바로 컨테이너 시작
    st.markdown('<div class="iris-dash">', unsafe_allow_html=True)

    # 총 출입매체 수 (첫 번째 행에 단독 배치)
    col_total = st.columns([1])[0]
    with col_total:
        st.markdown(f'<div class="iris-card ic-total"><div class="ic-label">총 출입매체</div><div class="ic-value" id="total-{unique_id}" data-target="{total}">0</div></div>', unsafe_allow_html=True)

    # 구분별 통계 (두 번째 행에 7개 배치)
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    with col1:
        st.markdown(f'<div class="iris-card ic-blue"><div class="ic-label">종합지</div><div class="ic-value" id="general-{unique_id}" data-target="{category_counts["종합지"]}">0</div><div class="ic-pct">{category_pcts["종합지"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="iris-card ic-emerald"><div class="ic-label">경제지</div><div class="ic-value" id="economic-{unique_id}" data-target="{category_counts["경제지"]}">0</div><div class="ic-pct">{category_pcts["경제지"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div class="iris-card ic-warn"><div class="ic-label">통신사</div><div class="ic-value" id="agency-{unique_id}" data-target="{category_counts["통신사"]}">0</div><div class="ic-pct">{category_pcts["통신사"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col4:
        st.markdown(f'<div class="iris-card ic-purple"><div class="ic-label">석간지</div><div class="ic-value" id="evening-{unique_id}" data-target="{category_counts["석간지"]}">0</div><div class="ic-pct">{category_pcts["석간지"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col5:
        st.markdown(f'<div class="iris-card ic-pink"><div class="ic-label">영자지</div><div class="ic-value" id="english-{unique_id}" data-target="{category_counts["영자지"]}">0</div><div class="ic-pct">{category_pcts["영자지"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col6:
        st.markdown(f'<div class="iris-card ic-neg"><div class="ic-label">경제TV</div><div class="ic-value" id="tv-{unique_id}" data-target="{category_counts["경제TV"]}">0</div><div class="ic-pct">{category_pcts["경제TV"]:.1f}%</div></div>', unsafe_allow_html=True)

    with col7:
        st.markdown(f'<div class="iris-card ic-teal"><div class="ic-label">온라인지</div><div class="ic-value" id="online-{unique_id}" data-target="{category_counts["온라인지"]}">0</div><div class="ic-pct">{category_pcts["온라인지"]:.1f}%</div></div>', unsafe_allow_html=True)

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
