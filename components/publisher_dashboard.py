"""
출입매체 현황 대시보드 컴포넌트
총 출입매체 수와 구분별(종합지, 경제지, 통신사, 석간지, 영자지, 경제TV, 온라인지) 통계 표시
"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pytz


_CSS = """
<style>
.pub-hero {
    background: linear-gradient(120deg, rgba(59,130,246,0.18) 0%, rgba(16,185,129,0.10) 100%);
    border: 1px solid rgba(59,130,246,0.35);
    border-radius: 10px;
    padding: 14px 28px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
}
.pub-hero-label {
    font-size: 1.05rem;
    font-weight: 700;
    color: #93c5fd;
    letter-spacing: 0.04em;
    white-space: nowrap;
}
.pub-hero-sep {
    width: 1px;
    height: 32px;
    background: rgba(59,130,246,0.45);
    flex-shrink: 0;
}
.pub-hero-count {
    display: flex;
    align-items: baseline;
    gap: 5px;
}
.pub-hero-num {
    font-size: 2.4rem;
    font-weight: 800;
    color: #fff;
    line-height: 1;
    letter-spacing: -0.01em;
}
.pub-hero-unit {
    font-size: 1rem;
    font-weight: 600;
    color: #60a5fa;
}
.pub-kw-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 6px;
    margin-top: 0;
}
.pub-kw-card {
    border-radius: 6px;
    padding: 8px 10px 6px;
    border-left: 2px solid;
    text-align: center;
    transition: background 0.2s;
}
.pub-kw-card:hover { background: rgba(255,255,255,0.06) !important; }
.pub-kw-label {
    font-size: 0.70rem;
    font-weight: 600;
    white-space: nowrap;
    margin-bottom: 3px;
}
.pub-kw-num {
    font-size: 1.3rem;
    font-weight: 700;
    color: #fff;
    line-height: 1;
    margin-bottom: 3px;
}
.pub-kw-pct { font-size: 0.65rem; color: rgba(255,255,255,0.38); }

.pub-kw-1 { border-left-color: #3b82f6; background: rgba(59,130,246,0.07); }
.pub-kw-1 .pub-kw-label { color: #60a5fa; }

.pub-kw-2 { border-left-color: #10b981; background: rgba(16,185,129,0.07); }
.pub-kw-2 .pub-kw-label { color: #34d399; }

.pub-kw-3 { border-left-color: #f59e0b; background: rgba(245,158,11,0.07); }
.pub-kw-3 .pub-kw-label { color: #fbbf24; }

.pub-kw-4 { border-left-color: #a855f7; background: rgba(168,85,247,0.06); }
.pub-kw-4 .pub-kw-label { color: #c084fc; }

.pub-kw-5 { border-left-color: #ec4899; background: rgba(236,72,153,0.06); }
.pub-kw-5 .pub-kw-label { color: #f472b6; }

.pub-kw-6 { border-left-color: #ef4444; background: rgba(239,68,68,0.06); }
.pub-kw-6 .pub-kw-label { color: #f87171; }

.pub-kw-7 { border-left-color: #14b8a6; background: rgba(20,184,166,0.06); }
.pub-kw-7 .pub-kw-label { color: #2dd4bf; }
</style>
"""


def render_publisher_dashboard(media_contacts: dict, show_live: bool = True):
    """
    출입매체 현황 대시보드 렌더링

    Args:
        media_contacts: 언론사 정보 딕셔너리 {언론사명: {구분: "종합지", ...}}
        show_live: LIVE 뱃지 표시 여부
    """
    total = len(media_contacts)

    category_counts = {
        '종합지': 11,
        '경제지': 10,
        '경제TV': 9,
        '영자지': 5,
        '석간지': 4,
    }

    통신사_count = 0
    for media_name, media_info in media_contacts.items():
        if media_info.get('구분', '') == '통신사':
            통신사_count += 1
    category_counts['통신사'] = 통신사_count

    fixed_sum = sum(category_counts.values())
    category_counts['온라인지'] = max(0, total - fixed_sum)

    def pct(count):
        return (count / total * 100) if total > 0 else 0

    import random, string
    uid = ''.join(random.choices(string.ascii_lowercase, k=8))

    # CSS 주입 (항상 HTML과 함께 — 캐시 의존 없음)
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── 상단: 총합 히어로 바 ──────────────────────────────────
    st.markdown(f'''
<div class="pub-hero">
    <div class="pub-hero-label">총 출입매체</div>
    <div class="pub-hero-sep"></div>
    <div class="pub-hero-count">
        <span class="pub-hero-num" id="pub-total-{uid}" data-target="{total}">0</span>
        <span class="pub-hero-unit">개</span>
    </div>
</div>
''', unsafe_allow_html=True)

    # ── 하단: 구분별 카드 7개 ────────────────────────────────
    c = category_counts
    st.markdown(f'''
<div class="pub-kw-grid">
  <div class="pub-kw-card pub-kw-1">
    <div class="pub-kw-label">종합지</div>
    <div class="pub-kw-num" id="pub-gen-{uid}" data-target="{c['종합지']}">0</div>
    <div class="pub-kw-pct">{pct(c['종합지']):.1f}%</div>
  </div>
  <div class="pub-kw-card pub-kw-2">
    <div class="pub-kw-label">경제지</div>
    <div class="pub-kw-num" id="pub-eco-{uid}" data-target="{c['경제지']}">0</div>
    <div class="pub-kw-pct">{pct(c['경제지']):.1f}%</div>
  </div>
  <div class="pub-kw-card pub-kw-3">
    <div class="pub-kw-label">통신사</div>
    <div class="pub-kw-num" id="pub-age-{uid}" data-target="{c['통신사']}">0</div>
    <div class="pub-kw-pct">{pct(c['통신사']):.1f}%</div>
  </div>
  <div class="pub-kw-card pub-kw-4">
    <div class="pub-kw-label">석간지</div>
    <div class="pub-kw-num" id="pub-eve-{uid}" data-target="{c['석간지']}">0</div>
    <div class="pub-kw-pct">{pct(c['석간지']):.1f}%</div>
  </div>
  <div class="pub-kw-card pub-kw-5">
    <div class="pub-kw-label">영자지</div>
    <div class="pub-kw-num" id="pub-eng-{uid}" data-target="{c['영자지']}">0</div>
    <div class="pub-kw-pct">{pct(c['영자지']):.1f}%</div>
  </div>
  <div class="pub-kw-card pub-kw-6">
    <div class="pub-kw-label">경제TV</div>
    <div class="pub-kw-num" id="pub-tv-{uid}" data-target="{c['경제TV']}">0</div>
    <div class="pub-kw-pct">{pct(c['경제TV']):.1f}%</div>
  </div>
  <div class="pub-kw-card pub-kw-7">
    <div class="pub-kw-label">온라인지</div>
    <div class="pub-kw-num" id="pub-onl-{uid}" data-target="{c['온라인지']}">0</div>
    <div class="pub-kw-pct">{pct(c['온라인지']):.1f}%</div>
  </div>
</div>
''', unsafe_allow_html=True)

    components.html(f'''
<script>
(function() {{
    var ids = ['pub-total-{uid}','pub-gen-{uid}','pub-eco-{uid}','pub-age-{uid}',
               'pub-eve-{uid}','pub-eng-{uid}','pub-tv-{uid}','pub-onl-{uid}'];
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
