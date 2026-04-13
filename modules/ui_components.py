"""
ui_components.py
P-IRIS 키워드 인사이트 — UI 렌더링 컴포넌트 (다크 테마)
"""
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# ── 컬러 팔레트 (다크 테마) ──
COLORS = {
    "primary":           "#60a5fa",
    "secondary":         "#a78bfa",
    "positive":          "#34d399",
    "negative":          "#f87171",
    "warning":           "#fbbf24",
    "neutral":           "#94a3b8",
    "text_primary":      "#f1f5f9",
    "text_body":         "#cbd5e1",
    "text_sub":          "#64748b",
    "text_link":         "#60a5fa",
    "bg_page":           "#0f172a",
    "bg_card":           "#1e293b",
    "bg_card_hover":     "#334155",
    "bg_elevated":       "#293548",
    "bg_input":          "#1e293b",
    "border":            "#334155",
    "border_light":      "#475569",
    "chart_bar":         "#475569",
    "chart_bar_accent":  "#60a5fa",
    "chart_line":        "#34d399",
    "chart_grid":        "#1e293b",
}

# ── Plotly 공통 테마 (다크) ──
PLOTLY_THEME = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Pretendard, Apple SD Gothic Neo, sans-serif", size=12, color="#94a3b8"),
    margin=dict(l=0, r=0, t=36, b=0),
    xaxis=dict(
        gridcolor="#1e293b", showline=False,
        tickfont=dict(size=10, color="#64748b"),
    ),
    yaxis=dict(
        gridcolor="#1e293b", showline=False, zeroline=False,
        tickfont=dict(size=10, color="#64748b"),
    ),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02,
        xanchor="right", x=1, font=dict(size=11, color="#94a3b8"),
    ),
)

CHART_COLORS = {
    "bar_default":  "#475569",
    "bar_accent":   "#60a5fa",
    "line_trend":   "#34d399",
    "tone_pos":     "#10b981",
    "tone_neu":     "#64748b",
    "tone_neg":     "#ef4444",
}

# ── 위기 등급 색상 ──
CRISIS_COLORS = {
    "관심": ("badge-green",  "#34d399"),
    "주의": ("badge-yellow", "#fbbf24"),
    "경계": ("badge-yellow", "#f97316"),
    "심각": ("badge-red",    "#f87171"),
}

TREND_COLORS = {
    "급증": ("badge-red",    "🔺"),
    "증가": ("badge-yellow", "↑"),
    "보합": ("badge-gray",   "→"),
    "감소": ("badge-blue",   "↓"),
    "급감": ("badge-blue",   "🔻"),
}


def inject_custom_css():
    st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    html, body, [class*="css"] {
        font-family: 'Pretendard', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
    }

    .stApp { background: #0f172a; }

    .stApp p, .stApp span, .stApp label, .stApp li { color: #cbd5e1; }
    .stApp h1, .stApp h2, .stApp h3 { color: #f1f5f9 !important; }

    .stTextInput > div > div > input {
        background: #1e293b !important; color: #f1f5f9 !important;
        border: 1px solid #334155 !important; border-radius: 10px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 2px rgba(96,165,250,0.2) !important;
    }
    .stTextInput label { color: #94a3b8 !important; font-size: 13px !important; }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
        border: none !important; border-radius: 10px !important;
        color: #fff !important; font-weight: 600 !important;
    }

    [data-testid="stMetric"] {
        background: #1e293b; border: 1px solid #334155;
        border-radius: 12px; padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricLabel"] { font-size: 12px !important; color: #64748b !important; font-weight: 500 !important; }
    [data-testid="stMetricValue"] { font-size: 26px !important; font-weight: 700 !important; color: #f1f5f9 !important; }
    [data-testid="stMetricDelta"] { font-size: 12px !important; }

    hr {
        border: none; height: 1px;
        background: linear-gradient(90deg, #3b82f6, #10b981, transparent);
        margin: 24px 0;
    }

    .insight-card {
        background: #1e293b; border: 1px solid #334155; border-radius: 12px;
        padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); margin-bottom: 12px;
    }
    .insight-card-accent {
        background: #1e293b; border: 1px solid #334155;
        border-left: 3px solid #60a5fa; border-radius: 0 12px 12px 0;
        padding: 16px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); margin-bottom: 10px;
    }

    .section-header {
        font-size: 15px; font-weight: 700; color: #f1f5f9;
        margin: 28px 0 14px; display: flex; align-items: center; gap: 8px;
    }
    .section-sub { font-size: 12px; color: #64748b; font-weight: 400; margin-left: 4px; }

    .badge {
        display: inline-block; padding: 2px 10px; border-radius: 12px;
        font-size: 11px; font-weight: 600;
    }
    .badge-blue   { color: #93c5fd; background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.3); }
    .badge-green  { color: #6ee7b7; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.3); }
    .badge-red    { color: #fca5a5; background: rgba(239,68,68,0.15);  border: 1px solid rgba(239,68,68,0.3); }
    .badge-yellow { color: #fcd34d; background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.3); }
    .badge-purple { color: #c4b5fd; background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.3); }
    .badge-gray   { color: #94a3b8; background: rgba(148,163,184,0.1); border: 1px solid rgba(148,163,184,0.2); }

    .tone-bar { display: flex; border-radius: 8px; overflow: hidden; height: 28px; margin: 8px 0; }
    .tone-pos { background: #10b981; }
    .tone-neu { background: #64748b; }
    .tone-neg { background: #ef4444; }
    .tone-segment {
        display: flex; align-items: center; justify-content: center;
        color: #fff; font-size: 11px; font-weight: 600;
    }

    .article-card {
        background: #1e293b; border: 1px solid #334155; border-radius: 10px;
        padding: 14px 18px; margin-bottom: 8px; transition: all 0.2s;
    }
    .article-card:hover { background: #293548; border-color: #475569; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .article-title { font-size: 14px; font-weight: 600; color: #e2e8f0; text-decoration: none; line-height: 1.4; }
    .article-title:hover { color: #60a5fa; }
    .article-meta { font-size: 11px; color: #64748b; margin-top: 4px; }
    .article-desc { font-size: 12px; color: #94a3b8; margin-top: 6px; line-height: 1.5; }

    .cross-analysis { border-radius: 10px; padding: 14px 18px; margin-bottom: 14px; }
    .cross-active   { background: rgba(239,68,68,0.08);  border: 1px solid rgba(239,68,68,0.25); }
    .cross-internal { background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.25); }
    .cross-latent   { background: rgba(249,115,22,0.08); border: 1px solid rgba(249,115,22,0.25); }
    .cross-inactive { background: rgba(34,197,94,0.08);  border: 1px solid rgba(34,197,94,0.25); }

    .action-card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px; margin-bottom: 10px; }
    .action-card-primary {
        background: linear-gradient(135deg, rgba(30,58,95,0.8), rgba(37,99,235,0.15));
        border: 1px solid rgba(96,165,250,0.3);
    }
    .action-number {
        display: inline-flex; align-items: center; justify-content: center;
        width: 24px; height: 24px; border-radius: 8px; color: #fff;
        font-size: 12px; font-weight: 700; margin-right: 10px; flex-shrink: 0;
    }

    .signal-risk { padding: 4px 0 4px 12px; border-left: 2px solid #f87171; font-size: 12px; color: #cbd5e1; margin-bottom: 4px; line-height: 1.5; }
    .signal-opp  { padding: 4px 0 4px 12px; border-left: 2px solid #34d399; font-size: 12px; color: #cbd5e1; margin-bottom: 4px; line-height: 1.5; }

    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .custom-table th { text-align: left; padding: 10px 14px; font-weight: 600; color: #64748b; font-size: 11px; background: #0f172a; border-bottom: 1px solid #334155; }
    .custom-table td { padding: 10px 14px; color: #cbd5e1; border-bottom: 1px solid #1e293b; }

    .report-footer { text-align: center; padding: 20px 0 8px; border-top: 1px solid #334155; margin-top: 24px; font-size: 11px; color: #64748b; }

    .stAlert { background: #1e293b !important; border: 1px solid #334155 !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)


def render_page_header(keyword: str = ""):
    title_text = f'"{keyword}" 인사이트 브리핑' if keyword else "키워드 인사이트 브리핑"
    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px">
        <div style="display:flex; align-items:center; gap:10px">
            <div style="width:36px; height:36px; border-radius:10px;
                        background: linear-gradient(135deg, #1e3a5f, #3b82f6);
                        display:flex; align-items:center; justify-content:center;
                        color:#fff; font-size:15px; font-weight:700;">P</div>
            <div>
                <div style="font-size:11px; color:#64748b; font-weight:500; letter-spacing:0.05em">
                    P-IRIS KEYWORD INSIGHT
                </div>
                <div style="font-size:20px; font-weight:800; color:#f1f5f9; letter-spacing:-0.02em">
                    {title_text}
                </div>
            </div>
        </div>
        <div style="text-align:right">
            <div style="font-size:11px; color:#64748b">분석 기준일</div>
            <div style="font-size:13px; font-weight:600; color:#cbd5e1">
                {datetime.now().strftime('%Y-%m-%d')}
            </div>
        </div>
    </div>
    <div style="height:2px; background:linear-gradient(90deg, #3b82f6, #10b981, transparent);
                border-radius:1px; margin-bottom:20px"></div>
    """, unsafe_allow_html=True)


def render_section_header(icon: str, title: str, subtitle: str = ""):
    sub_html = f'<span class="section-sub">{subtitle}</span>' if subtitle else ""
    st.markdown(f'<div class="section-header">{icon} {title}{sub_html}</div>', unsafe_allow_html=True)


def render_kpi_cards(insight: dict):
    # 실제 KPI 렌더링은 pages/keyword_insight.py의 _render_kpi()에서 처리
    pass


def render_tone_bar(pos: int, neu: int, neg: int):
    # 합계가 100이 되도록 정규화
    total = pos + neu + neg
    if total == 0:
        pos, neu, neg = 0, 100, 0
        total = 100
    p = round(pos / total * 100)
    n = round(neu / total * 100)
    g = 100 - p - n
    _st().markdown(f"""
    <div class="tone-bar">
        <div class="tone-segment tone-pos" style="width:{p}%">{'긍정 ' + str(p) + '%' if p >= 10 else ''}</div>
        <div class="tone-segment tone-neu" style="width:{n}%">{'중립 ' + str(n) + '%' if n >= 10 else ''}</div>
        <div class="tone-segment tone-neg" style="width:{g}%">{str(g) + '%' if g >= 10 else ''}</div>
    </div>
    """, unsafe_allow_html=True)


def render_cross_analysis(news_vs_search: str, summary: str):
    class_map = {
        "이슈활성화": "cross-active",
        "업계내부이슈": "cross-internal",
        "잠재이슈":    "cross-latent",
        "비활성이슈":  "cross-inactive",
    }
    badge_map = {
        "이슈활성화": "badge-red",
        "업계내부이슈": "badge-yellow",
        "잠재이슈":    "badge-yellow",
        "비활성이슈":  "badge-green",
    }
    _st().markdown(f"""
    <div class="cross-analysis {class_map.get(news_vs_search, '')}">
        <span class="badge {badge_map.get(news_vs_search, 'badge-gray')}">
            보도-검색 교차분석: {news_vs_search}
        </span>
        <div style="font-size:13px; color:#cbd5e1; margin-top:6px; line-height:1.6">{summary}</div>
    </div>
    """, unsafe_allow_html=True)


def render_latest_articles(latest_articles: list[dict]):
    render_section_header("📰", "최신 기사 TOP 5", "네이버 뉴스 API 기준 최신순")
    if not latest_articles:
        _st().info("수집된 기사가 없습니다.")
        return
    for article in latest_articles:
        desc = article.get("description", "")
        desc_preview = desc[:120] + ("..." if len(desc) > 120 else "")
        _st().markdown(f"""
        <div class="article-card">
            <a href="{article.get('link', '#')}" target="_blank" class="article-title">
                {article.get('title', '제목 없음')}
            </a>
            <div class="article-meta">
                <span class="badge badge-blue">{article.get('media', '')}</span>
                &nbsp; {article.get('date', '')} {article.get('time', '')}
            </div>
            <div class="article-desc">{desc_preview}</div>
        </div>
        """, unsafe_allow_html=True)


def render_news_volume_chart(news_items: list[dict], keyword: str):
    """날짜별 보도 건수 막대차트"""
    from collections import Counter
    dates = [item["pub_date_str"] for item in news_items if item.get("is_within_30d")]
    if not dates:
        _st().info("최근 30일 내 기사 데이터가 없습니다.")
        return
    counts = Counter(dates)
    sorted_dates = sorted(counts.keys())
    values = [counts[d] for d in sorted_dates]

    fig = go.Figure(go.Bar(
        x=sorted_dates, y=values,
        marker_color=[CHART_COLORS["bar_accent"] if v == max(values) else CHART_COLORS["bar_default"] for v in values],
        hovertemplate="%{x}: %{y}건<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_THEME, height=250, title_text="뉴스 보도량 추이 (최근 30일)", title_font_color="#94a3b8", title_font_size=13)
    _st().plotly_chart(fig, use_container_width=True)


def render_trend_chart(trend_data: list[dict], label: str, time_unit: str = "date"):
    """검색 관심도 라인 차트"""
    if not trend_data:
        _st().info(f"검색 트렌드 데이터 없음")
        return
    periods = [item.get("period", "") for item in trend_data]
    ratios = [item.get("ratio", 0) for item in trend_data]
    fig = go.Figure(go.Scatter(
        x=periods, y=ratios,
        mode="lines+markers",
        line=dict(color=CHART_COLORS["line_trend"], width=2),
        marker=dict(size=4, color=CHART_COLORS["line_trend"]),
        fill="tozeroy",
        fillcolor="rgba(52,211,153,0.08)",
        hovertemplate="%{x}: %{y}<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_THEME, height=250, title_text=label, title_font_color="#94a3b8", title_font_size=13)
    _st().plotly_chart(fig, use_container_width=True)


def render_top_media_chart(top_media: list[str]):
    """TOP 5 보도 매체 수평 막대"""
    if not top_media:
        return
    labels = list(reversed(top_media[:5]))
    values = list(range(len(labels), 0, -1))
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=CHART_COLORS["bar_accent"],
        hovertemplate="%{y}<extra></extra>",
    ))
    theme = {k: v for k, v in PLOTLY_THEME.items() if k not in ("xaxis", "yaxis")}
    fig.update_layout(**theme, height=220, title_text="TOP 5 보도 매체", title_font_color="#94a3b8", title_font_size=13,
                      xaxis=dict(visible=False), yaxis=dict(tickfont=dict(size=11, color="#cbd5e1")))
    _st().plotly_chart(fig, use_container_width=True)


def render_issue_clusters(clusters: list[dict]):
    render_section_header("🗂️", "이슈 클러스터", "주요 논점 그룹")
    if not clusters:
        return
    cols = _st().columns(min(len(clusters), 2))
    for i, cluster in enumerate(clusters):
        with cols[i % 2]:
            link = cluster.get("representative_article_link", "#")
            title = cluster.get("representative_article_title", "")
            _st().markdown(f"""
            <div class="insight-card-accent">
                <div style="font-size:13px; font-weight:700; color:#f1f5f9; margin-bottom:6px">
                    {cluster.get('cluster_name', '')}
                </div>
                <div style="font-size:12px; color:#94a3b8; margin-bottom:6px">
                    <a href="{link}" target="_blank" style="color:#60a5fa; text-decoration:none">{title[:60]}{'...' if len(title)>60 else ''}</a>
                </div>
                <div style="font-size:12px; color:#94a3b8; line-height:1.5">{cluster.get('summary', '')}</div>
            </div>
            """, unsafe_allow_html=True)


def render_company_exposure(ce: dict):
    render_section_header("🏢", "자사 노출 분석")
    tone = ce.get("tone", "중립")
    tone_color = {"긍정": "#34d399", "중립": "#94a3b8", "부정": "#f87171", "해당없음": "#64748b"}.get(tone, "#94a3b8")
    _st().markdown(f"""
    <div class="insight-card">
        <div style="display:flex; gap:16px; margin-bottom:10px; flex-wrap:wrap">
            <div>
                <div style="font-size:11px; color:#64748b">언급 횟수</div>
                <div style="font-size:22px; font-weight:700; color:#f1f5f9">{ce.get('mention_count', 0)}건</div>
            </div>
            <div>
                <div style="font-size:11px; color:#64748b">언급 맥락</div>
                <div style="font-size:14px; font-weight:600; color:#cbd5e1">{ce.get('mention_context', '-')}</div>
            </div>
            <div>
                <div style="font-size:11px; color:#64748b">논조</div>
                <div style="font-size:14px; font-weight:600; color:{tone_color}">{tone}</div>
            </div>
        </div>
        <div style="font-size:13px; color:#94a3b8; line-height:1.6">{ce.get('summary', '')}</div>
    </div>
    """, unsafe_allow_html=True)


def render_competitor_table(competitors: list[dict]):
    if not competitors:
        return
    render_section_header("⚔️", "경쟁사·기관 동향")
    rows_html = ""
    for c in competitors:
        rows_html += f"""<tr>
            <td>{c.get('entity_name', '')}</td>
            <td style="text-align:center">{c.get('mention_count', 0)}</td>
            <td>{c.get('context_summary', '')}</td>
        </tr>"""
    _st().markdown(f"""
    <div class="insight-card" style="padding:0; overflow:hidden">
        <table class="custom-table">
            <thead><tr><th>기관/기업</th><th style="text-align:center">언급</th><th>맥락</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)


def render_journalist_matches(matches: list[dict]):
    render_section_header("👤", "출입기자 매칭", "관련 기자 리스트")
    if not matches:
        _st().markdown('<div class="insight-card"><div style="color:#64748b; font-size:13px">매칭된 기자 정보가 없습니다.</div></div>', unsafe_allow_html=True)
        return
    tone_badge = {"우호": "badge-green", "중립": "badge-gray", "비우호": "badge-red"}
    rows_html = ""
    for j in matches:
        t = j.get("tone", "중립")
        rows_html += f"""<tr>
            <td><strong style="color:#f1f5f9">{j.get('name', '')}</strong></td>
            <td>{j.get('media', '')}</td>
            <td><span class="badge {tone_badge.get(t, 'badge-gray')}">{t}</span></td>
            <td>{j.get('last_contact', 'N/A')}</td>
            <td style="color:#94a3b8">{j.get('relevance', '')}</td>
        </tr>"""
    _st().markdown(f"""
    <div class="insight-card" style="padding:0; overflow:hidden">
        <table class="custom-table">
            <thead><tr><th>이름</th><th>매체</th><th>논조</th><th>최근 접촉</th><th>매칭 이유</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)


def render_past_responses(responses: list[dict]):
    render_section_header("📁", "과거 대응이력", "유사 이슈 사례 — 최신순")
    if not responses:
        _st().markdown('<div class="insight-card"><div style="color:#64748b; font-size:13px">유사 대응이력이 없습니다.</div></div>', unsafe_allow_html=True)
        return

    # 최신순 정렬
    sorted_responses = sorted(responses, key=lambda x: x.get("date", ""), reverse=True)

    for i, r in enumerate(sorted_responses):
        date          = r.get("date", "날짜 미상")
        issue_summary = r.get("issue_summary", "")
        response_type = r.get("response_type", "")
        result        = r.get("result", "")
        lesson        = r.get("lesson", "")

        label = f"📅 {date}　|　{issue_summary}"
        with _st().expander(label, expanded=(i == 0)):
            col_left, col_right = _st().columns([1, 2], gap="medium")
            with col_left:
                _st().markdown(f"""
                <div style="background:#1e293b; border-radius:8px; padding:14px 16px; height:100%">
                    <div style="font-size:11px; color:#64748b; margin-bottom:6px; text-transform:uppercase; letter-spacing:.5px">대응 유형</div>
                    <div style="font-size:14px; font-weight:700; color:#cbd5e1">{response_type or "—"}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_right:
                _st().markdown(f"""
                <div style="background:#1e293b; border-radius:8px; padding:14px 16px">
                    <div style="font-size:11px; color:#64748b; margin-bottom:6px; text-transform:uppercase; letter-spacing:.5px">대응 결과</div>
                    <div style="font-size:13px; color:#e2e8f0; line-height:1.7">{result or "—"}</div>
                </div>
                """, unsafe_allow_html=True)
            _st().markdown(f"""
            <div style="background:#0f172a; border-radius:8px; padding:14px 16px; margin-top:10px;
                        border-left:3px solid #3b82f6">
                <div style="font-size:11px; color:#64748b; margin-bottom:6px; text-transform:uppercase; letter-spacing:.5px">💡 시사점</div>
                <div style="font-size:13px; color:#60a5fa; line-height:1.7">{lesson or "—"}</div>
            </div>
            """, unsafe_allow_html=True)


def render_risk_opportunity(ro: dict):
    render_section_header("⚡", "리스크 · 기회 시그널")
    risks_html = "".join(f'<div class="signal-risk">{s}</div>' for s in ro.get("risk_signals", []))
    opps_html  = "".join(f'<div class="signal-opp">{s}</div>'  for s in ro.get("opportunity_signals", []))
    _st().markdown(f"""
    <div class="insight-card">
        <div style="font-size:12px; font-weight:600; color:#f87171; margin-bottom:6px">🔻 리스크</div>
        {risks_html or '<div style="color:#64748b; font-size:12px">리스크 시그널 없음</div>'}
        <div style="font-size:12px; font-weight:600; color:#34d399; margin:12px 0 6px">🔺 기회</div>
        {opps_html or '<div style="color:#64748b; font-size:12px">기회 시그널 없음</div>'}
        <div style="margin-top:12px; font-size:13px; color:#cbd5e1; line-height:1.6;
                    background:#0f172a; border-radius:8px; padding:10px 12px">
            {ro.get('summary', '')}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_action_cards(actions: list[dict]):
    render_section_header("🚀", "커뮤니케이션 액션 제안")
    color_map = {1: "#3b82f6", 2: "#8b5cf6", 3: "#64748b"}
    for a in actions:
        p = a.get("priority", 3)
        card_class = "action-card action-card-primary" if p == 1 else "action-card"
        _st().markdown(f"""
        <div class="{card_class}">
            <div style="display:flex; align-items:flex-start">
                <span class="action-number" style="background:{color_map.get(p, '#64748b')}">{p}</span>
                <div>
                    <div style="font-size:13px; font-weight:600; color:#f1f5f9; margin-bottom:2px">{a.get('action', '')}</div>
                    <div style="font-size:11px; color:#64748b">{a.get('rationale', '')}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_footer(keyword: str):
    _st().markdown(f"""
    <div class="report-footer">
        P-IRIS Keyword Insight &middot; GPT-4.1 분석 &middot; 네이버 뉴스 API + 데이터랩 API
        &middot; {datetime.now().strftime('%Y-%m-%d %H:%M')} 생성<br>
        <span style="font-size:10px; color:#475569">
            ※ 검색 관심도는 네이버 데이터랩 기준 상대값(최대=100)이며 절대 검색량이 아닙니다.
        </span>
    </div>
    """, unsafe_allow_html=True)


def _st():
    """streamlit 모듈 반환 (순환참조 방지용 헬퍼)"""
    return st
