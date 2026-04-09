"""
naver_datalab.py
네이버 데이터랩 - 검색어 트렌드 API 래퍼
"""
import json
import requests
import streamlit as st
from datetime import datetime, timedelta


def _get_headers() -> dict:
    cid = st.secrets.get("NAVER_CLIENT_ID", "")
    csec = st.secrets.get("NAVER_CLIENT_SECRET", "")
    return {
        "X-Naver-Client-Id": cid,
        "X-Naver-Client-Secret": csec,
        "Content-Type": "application/json",
    }


def fetch_search_trend(
    keyword: str,
    days: int = 30,
    time_unit: str = "date",
    related_keywords: list | None = None,
) -> dict:
    """
    네이버 데이터랩 - 검색어 트렌드 조회
    time_unit: "date" (일별) | "week" (주별) | "month" (월별)
    """
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = _get_headers()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    keywords_list = [keyword]
    if related_keywords:
        keywords_list.extend(related_keywords[:4])  # 최대 5개

    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate":   end_date.strftime("%Y-%m-%d"),
        "timeUnit":  time_unit,
        "keywordGroups": [
            {"groupName": keyword, "keywords": keywords_list}
        ],
        "device": "",
        "ages":   [],
        "gender": "",
    }

    resp = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
    resp.raise_for_status()
    return resp.json()


def safe_fetch_trend(keyword: str, days: int, time_unit: str) -> dict | None:
    """
    데이터랩 호출 실패 시 None 반환 (graceful degradation)
    전체 분석은 계속 진행됨.
    """
    try:
        return fetch_search_trend(keyword, days=days, time_unit=time_unit)
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response else 0
        if code == 429:
            st.warning("⚠️ 데이터랩 일일 조회 한도 초과. 검색 트렌드 없이 분석합니다.")
        else:
            st.warning(f"⚠️ 데이터랩 API 오류 (HTTP {code}). 검색 트렌드 없이 분석합니다.")
        return None
    except requests.exceptions.RequestException:
        st.warning("⚠️ 데이터랩 연결 실패. 검색 트렌드 없이 분석합니다.")
        return None
    except Exception:
        st.warning("⚠️ 데이터랩 처리 중 오류. 검색 트렌드 없이 분석합니다.")
        return None


def extract_trend_data(trend_result: dict | None) -> list[dict]:
    """데이터랩 응답에서 data 배열만 추출"""
    if not trend_result:
        return []
    try:
        return trend_result["results"][0]["data"]
    except (KeyError, IndexError, TypeError):
        return []
