"""
insight_generator.py
GPT-4.1 기반 키워드 인사이트 브리핑 생성
API 호출 원칙: 검색 1회당 GPT 최대 1회, session_state 1시간 캐시
"""
import json
import os
import time
import openai
import streamlit as st
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)

SYSTEM_PROMPT = """당신은 한국 기업 언론홍보 전문가입니다.
아래 뉴스 기사 목록을 분석하여 JSON 형식으로만 응답하세요.
한국어로 작성하며 각 항목은 간결하게 작성합니다."""

USER_PROMPT_TEMPLATE = """[키워드]: {keyword}
[기사 목록]: {news_json}

다음 JSON 구조로만 응답 (JSON 외 텍스트 절대 포함 금지):
{{
  "summary": "2~3줄 핵심 요약",
  "trend": "급증|증가|보합|감소|급감",
  "crisis_level": "관심|주의|경계|심각",
  "sentiment": {{"positive": 0, "neutral": 0, "negative": 0}},
  "top_media": ["매체1", "매체2", "매체3", "매체4", "매체5"],
  "issues": [{{"title": "이슈 제목", "description": "1줄 설명"}}],
  "competitors": [{{"name": "기관명", "count": 0, "trend": "1줄 동향"}}],
  "risks": ["리스크 항목 (3개 이내)"],
  "opportunities": ["기회 항목 (3개 이내)"],
  "actions": ["액션 제안 (3개 이내)"]
}}

작성 기준:
- issues는 정확히 3개
- sentiment 합계는 반드시 100
- crisis_level은 4단계(관심/주의/경계/심각) 중 하나
- trend는 최근 기사 날짜 분포 기반으로 판단"""


def _resolve_api_key() -> str:
    key = os.environ.get("OPEN_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        key = st.secrets.get("OPEN_API_KEY") or st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return ""


def _get_cache_key(keyword: str) -> str:
    return f"ki_cache_{keyword}"


def _load_from_session(keyword: str) -> dict | None:
    """session_state에서 1시간 이내 캐시 반환, 만료 시 None"""
    key = _get_cache_key(keyword)
    cached = st.session_state.get(key)
    if not cached:
        return None
    if time.time() - cached.get("timestamp", 0) > 3600:
        del st.session_state[key]
        return None
    return cached.get("gpt_result")


def _save_to_session(keyword: str, gpt_result: dict):
    """session_state에 GPT 결과 저장"""
    key = _get_cache_key(keyword)
    st.session_state[key] = {
        "timestamp": time.time(),
        "gpt_result": gpt_result,
    }


def call_gpt_once(keyword: str, news_items: list[dict]) -> dict:
    """
    GPT 단일 호출로 인사이트 전체 생성.
    session_state 1시간 캐시 우선 사용.
    타 섹션에서 재호출 금지 — 이 함수만 사용.
    """
    cached = _load_from_session(keyword)
    if cached is not None:
        return cached

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

    news_for_prompt = [
        {
            "title":   item["title_clean"],
            "media":   item["media_name"],
            "date":    item["pub_date_str"],
            "summary": item["desc_clean"][:200],
        }
        for item in news_items[:100]
    ]

    user_prompt = USER_PROMPT_TEMPLATE.format(
        keyword=keyword,
        news_json=json.dumps(news_for_prompt, ensure_ascii=False),
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-2025-04-14",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        result = json.loads(raw)
    except openai.APIConnectionError:
        st.error("⚠️ OpenAI API 연결 실패. 네트워크를 확인해주세요.")
        st.stop()
    except openai.RateLimitError as e:
        err_body = str(e).lower()
        if "insufficient_quota" in err_body or "exceeded your current quota" in err_body:
            st.error("⚠️ OpenAI API 크레딧이 소진되었습니다. platform.openai.com/account/billing 에서 잔액을 확인해주세요.")
        else:
            st.error("⚠️ OpenAI API 분당 요청 한도 초과. 잠시 후 다시 시도해주세요.")
        st.stop()
    except openai.AuthenticationError:
        st.error("⚠️ OpenAI API 키가 유효하지 않습니다. .env 또는 Streamlit secrets를 확인해주세요.")
        st.stop()
    except openai.APIStatusError as e:
        st.error(f"⚠️ OpenAI API 오류 (HTTP {e.status_code}): {getattr(e, 'code', '')} — {str(e)[:120]}")
        st.stop()
    except json.JSONDecodeError:
        st.error("⚠️ AI 응답 파싱 실패. 다시 시도해주세요.")
        st.stop()

    _save_to_session(keyword, result)
    return result


# ── 하위 호환: 기존 generate_insight 호출부 대비 ──
def generate_insight(
    keyword: str,
    news_items: list[dict],
    trend_30d=None,
    trend_1y=None,
    journalists=None,
    history=None,
    max_retries: int = 2,
) -> dict:
    """하위 호환 래퍼 — 내부적으로 call_gpt_once() 사용"""
    return call_gpt_once(keyword, news_items)
