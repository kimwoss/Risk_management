"""
insight_generator.py
GPT-4.1 기반 키워드 인사이트 브리핑 생성
"""
import json
import os
import openai
import streamlit as st
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 명시적 경로 로드 (모듈 위치 기준 상위 디렉토리)
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

SYSTEM_PROMPT = """당신은 포스코인터내셔널 커뮤니케이션실 소속 미디어 분석 전문가입니다.
임원급 의사결정자에게 보고하는 1페이지 브리핑 보고서를 작성합니다.

작성 원칙:
1. 사실 기반 서술. 추측이나 과장 금지.
2. 포스코인터내셔널 관점에서 서술 (자사 = 포스코인터내셔널).
3. 임원이 30초 안에 핵심을 파악할 수 있도록 간결하게 작성.
4. 각 섹션은 2~4문장 이내로 요약.
5. 액션 제안은 구체적이고 실행 가능하게 작성.
6. 위기 등급은 반드시 4단계(관심/주의/경계/심각) 중 하나로 판정.
7. 뉴스 보도량과 검색 트렌드(대중 관심도)를 교차 분석하여 인사이트를 도출.
   - 보도량 多 + 검색량 多 = 이슈 활성화
   - 보도량 多 + 검색량 少 = 업계내부이슈 (대중 관심 낮음)
   - 보도량 少 + 검색량 多 = 잠재이슈 (대중 관심 선행, 언론 미반영)
   - 보도량 少 + 검색량 少 = 비활성이슈

반드시 아래 JSON 구조로만 응답하세요. JSON 외 텍스트는 절대 포함하지 마세요."""

USER_PROMPT_TEMPLATE = """
## 분석 요청

**검색 키워드**: {keyword}
**분석 기준일**: {today}

---

### 입력 데이터 1: 최근 뉴스 기사 ({news_count}건)

{news_data_json}

---

### 입력 데이터 2: 네이버 검색 트렌드 (최근 30일, 일별 상대값)

{trend_30d_json}

---

### 입력 데이터 3: 네이버 검색 트렌드 (최근 1년, 월별 상대값)

{trend_1y_json}

---

### 입력 데이터 4: 출입기자 매칭 결과 ({journalist_count}건)

{journalist_data_json}

---

### 입력 데이터 5: 과거 대응이력 ({history_count}건)

{history_data_json}

---

### 출력 형식 (JSON)

{{
  "media_pulse": {{
    "total_7d": <int>,
    "total_30d": <int>,
    "trend": "<급증|증가|보합|감소|급감>",
    "tone_positive_pct": <int>,
    "tone_neutral_pct": <int>,
    "tone_negative_pct": <int>,
    "top_media": ["매체1", "매체2", "매체3", "매체4", "매체5"],
    "summary": "<2~3문장 요약>"
  }},
  "search_trend_analysis": {{
    "current_interest": <int 0~100>,
    "interest_change_30d": "<급증|증가|보합|감소|급감>",
    "interest_change_1y": "<급증|증가|보합|감소|급감>",
    "peak_date": "<최근 30일 중 최고점 날짜 yyyy-mm-dd>",
    "news_vs_search": "<이슈활성화|업계내부이슈|잠재이슈|비활성이슈>",
    "summary": "<2~3문장: 보도량과 대중 관심도의 관계 분석>"
  }},
  "issue_clusters": [
    {{
      "cluster_name": "<클러스터명>",
      "representative_article_title": "<대표 기사 제목>",
      "representative_article_link": "<기사 URL>",
      "summary": "<1~2문장 요약>"
    }}
  ],
  "company_exposure": {{
    "mention_count": <int>,
    "mention_context": "<주체|병렬언급|비교대상|미언급>",
    "tone": "<긍정|중립|부정|해당없음>",
    "summary": "<2~3문장 요약>"
  }},
  "competitor_landscape": [
    {{
      "entity_name": "<경쟁사/기관명>",
      "mention_count": <int>,
      "context_summary": "<1문장 맥락>"
    }}
  ],
  "journalist_matches": [
    {{
      "name": "<기자명>",
      "media": "<매체>",
      "tone": "<우호|중립|비우호>",
      "last_contact": "<최근 접촉일 또는 N/A>",
      "relevance": "<1문장: 매칭 이유>"
    }}
  ],
  "past_responses": [
    {{
      "date": "<YYYY-MM-DD>",
      "issue_summary": "<당시 이슈 한 줄 요약>",
      "response_type": "<대응 유형>",
      "result": "<결과 평가>",
      "lesson": "<이번 상황 시사점 1문장>"
    }}
  ],
  "risk_opportunity": {{
    "crisis_level": "<관심|주의|경계|심각>",
    "risk_signals": ["<리스크 시그널 1>", "<리스크 시그널 2>"],
    "opportunity_signals": ["<기회 시그널 1>", "<기회 시그널 2>"],
    "summary": "<2~3문장 종합 판단>"
  }},
  "action_recommendations": [
    {{
      "priority": <1|2|3>,
      "action": "<구체적 액션>",
      "rationale": "<1문장 근거>"
    }}
  ]
}}
"""


def _resolve_api_key() -> str:
    """환경변수 → st.secrets 순서로 OpenAI API 키 조회"""
    # 1. os.environ (로컬 .env 또는 시스템 환경변수)
    key = os.environ.get("OPEN_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    # 2. st.secrets (Streamlit Cloud 대시보드 secrets)
    try:
        key = st.secrets.get("OPEN_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return ""


def generate_insight(
    keyword: str,
    news_items: list[dict],
    trend_30d: dict | None,
    trend_1y: dict | None,
    journalists: list[dict],
    history: list[dict],
    max_retries: int = 2,
) -> dict:
    """GPT-4.1로 인사이트 브리핑 생성"""
    api_key = _resolve_api_key()
    if not api_key:
        env_keys = [k for k in os.environ if "OPEN" in k or "API" in k]
        st.error(
            f"❌ OpenAI API 키를 찾을 수 없습니다.\n\n"
            f"현재 환경변수 중 관련 키: {env_keys or '없음'}\n\n"
            f".env 파일의 `OPEN_API_KEY` 또는 Streamlit secrets를 확인해주세요."
        )
        st.stop()

    client = openai.OpenAI(api_key=api_key)
    today = datetime.now().strftime("%Y-%m-%d")

    news_for_prompt = [
        {
            "title":       item["title_clean"],
            "description": item["desc_clean"],
            "media":       item["media_name"],
            "date":        item["pub_date_str"],
            "link":        item["originallink"],
        }
        for item in news_items[:100]
    ]

    def _extract_trend_data(t):
        if not t:
            return []
        try:
            return t["results"][0]["data"]
        except (KeyError, IndexError, TypeError):
            return []

    user_prompt = USER_PROMPT_TEMPLATE.format(
        keyword=keyword,
        today=today,
        news_count=len(news_for_prompt),
        news_data_json=json.dumps(news_for_prompt, ensure_ascii=False, indent=2),
        trend_30d_json=json.dumps(_extract_trend_data(trend_30d), ensure_ascii=False),
        trend_1y_json=json.dumps(_extract_trend_data(trend_1y), ensure_ascii=False),
        journalist_count=len(journalists),
        journalist_data_json=json.dumps(journalists, ensure_ascii=False, indent=2),
        history_count=len(history),
        history_data_json=json.dumps(history, ensure_ascii=False, indent=2),
    )

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-2025-04-14",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            return json.loads(raw)
        except openai.APIConnectionError as e:
            last_error = e
            if attempt == max_retries:
                st.error("⚠️ OpenAI API 연결 실패. 네트워크를 확인해주세요.")
                st.stop()
        except openai.RateLimitError as e:
            st.error("⚠️ OpenAI API 호출 한도 초과. 잠시 후 다시 시도해주세요.")
            st.stop()
        except openai.APIStatusError as e:
            st.error(f"⚠️ OpenAI API 오류: {e.status_code}")
            st.stop()
        except json.JSONDecodeError as e:
            last_error = e
            if attempt == max_retries:
                st.error("⚠️ AI 응답 파싱 실패. 다시 시도해주세요.")
                st.stop()

    raise RuntimeError(f"generate_insight 실패: {last_error}")
