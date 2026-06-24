"""
전문적인 실시간 모니터링 대시보드 카드 컴포넌트
대응이력 현황: 총건수 히어로 바 + 관심/주의/위기/비상 카드 4개
"""
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import pytz


_CSS = """
<style>
.sta-hero {
    background: linear-gradient(120deg, rgba(99,102,241,0.18) 0%, rgba(59,130,246,0.10) 100%);
    border: 1px solid rgba(99,102,241,0.35);
    border-radius: 10px;
    padding: 14px 28px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
}
.sta-hero-label {
    font-size: 1.05rem;
    font-weight: 700;
    color: #a5b4fc;
    letter-spacing: 0.04em;
    white-space: nowrap;
}
.sta-hero-sep {
    width: 1px;
    height: 32px;
    background: rgba(99,102,241,0.45);
    flex-shrink: 0;
}
.sta-hero-count {
    display: flex;
    align-items: baseline;
    gap: 5px;
}
.sta-hero-num {
    font-size: 2.4rem;
    font-weight: 800;
    color: #fff;
    line-height: 1;
    letter-spacing: -0.01em;
}
.sta-hero-unit {
    font-size: 1rem;
    font-weight: 600;
    color: #818cf8;
}
.sta-kw-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 6px;
    margin-top: 0;
}
.sta-kw-card {
    border-radius: 6px;
    padding: 8px 10px 6px;
    border-left: 2px solid;
    text-align: center;
    transition: background 0.2s;
}
.sta-kw-card:hover { background: rgba(255,255,255,0.06) !important; }
.sta-kw-label {
    font-size: 0.72rem;
    font-weight: 600;
    margin-bottom: 3px;
}
.sta-kw-num {
    font-size: 1.45rem;
    font-weight: 700;
    color: #fff;
    line-height: 1;
    margin-bottom: 3px;
}
.sta-kw-pct { font-size: 0.68rem; color: rgba(255,255,255,0.38); }

.sta-kw-1 { border-left-color: #22c55e; background: rgba(34,197,94,0.07); }
.sta-kw-1 .sta-kw-label { color: #4ade80; }

.sta-kw-2 { border-left-color: #f59e0b; background: rgba(245,158,11,0.07); }
.sta-kw-2 .sta-kw-label { color: #fbbf24; }

.sta-kw-3 { border-left-color: #f97316; background: rgba(249,115,22,0.07); }
.sta-kw-3 .sta-kw-label { color: #fb923c; }

.sta-kw-4 { border-left-color: #ef4444; background: rgba(239,68,68,0.07); }
.sta-kw-4 .sta-kw-label { color: #f87171; }
</style>
"""


def render_status_dashboard(total: int, status_counts: dict, year: int = None, show_live: bool = True):
    if year is None:
        year = datetime.now().year

    관심 = status_counts.get('관심', 0)
    주의 = status_counts.get('주의', 0)
    위기 = status_counts.get('위기', 0)
    비상 = status_counts.get('비상', 0)

    def pct(count):
        return (count / total * 100) if total > 0 else 0

    import random, string
    uid = ''.join(random.choices(string.ascii_lowercase, k=8))

    # CSS 주입 (항상 HTML과 함께 — 캐시 의존 없음)
    st.markdown(_CSS, unsafe_allow_html=True)

    # ── 상단: 총합 히어로 바 ──────────────────────────────────
    st.markdown(f'''
<div class="sta-hero">
    <div class="sta-hero-label">{year}년 대응이력</div>
    <div class="sta-hero-sep"></div>
    <div class="sta-hero-count">
        <span class="sta-hero-num" id="sta-total-{uid}" data-target="{total}">0</span>
        <span class="sta-hero-unit">건</span>
    </div>
</div>
''', unsafe_allow_html=True)

    # ── 하단: 등급별 카드 4개 ────────────────────────────────
    st.markdown(f'''
<div class="sta-kw-grid">
  <div class="sta-kw-card sta-kw-1">
    <div class="sta-kw-label">관심</div>
    <div class="sta-kw-num" id="sta-int-{uid}" data-target="{관심}">0</div>
    <div class="sta-kw-pct">{pct(관심):.1f}%</div>
  </div>
  <div class="sta-kw-card sta-kw-2">
    <div class="sta-kw-label">주의</div>
    <div class="sta-kw-num" id="sta-cau-{uid}" data-target="{주의}">0</div>
    <div class="sta-kw-pct">{pct(주의):.1f}%</div>
  </div>
  <div class="sta-kw-card sta-kw-3">
    <div class="sta-kw-label">위기</div>
    <div class="sta-kw-num" id="sta-cri-{uid}" data-target="{위기}">0</div>
    <div class="sta-kw-pct">{pct(위기):.1f}%</div>
  </div>
  <div class="sta-kw-card sta-kw-4">
    <div class="sta-kw-label">비상</div>
    <div class="sta-kw-num" id="sta-eme-{uid}" data-target="{비상}">0</div>
    <div class="sta-kw-pct">{pct(비상):.1f}%</div>
  </div>
</div>
''', unsafe_allow_html=True)

    components.html(f'''
<script>
(function() {{
    var ids = ['sta-total-{uid}','sta-int-{uid}','sta-cau-{uid}','sta-cri-{uid}','sta-eme-{uid}'];
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
