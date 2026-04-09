"""
naver_news.py
네이버 검색 API (뉴스) 래퍼
"""
import requests
import streamlit as st
from datetime import datetime, timedelta
from .media_utils import clean_html, extract_media_name, parse_pub_datetime


def _get_headers() -> dict:
    cid = st.secrets.get("NAVER_CLIENT_ID", "")
    csec = st.secrets.get("NAVER_CLIENT_SECRET", "")
    if not cid or not csec:
        st.error("❌ 네이버 API 키가 없습니다. secrets를 확인해주세요.")
        st.stop()
    return {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec}


def fetch_naver_news(keyword: str, display: int = 100, sort: str = "date") -> list[dict]:
    """
    네이버 검색 API - 뉴스 검색 (최대 300건 페이지네이션)
    반환: 전처리된 dict 리스트
    """
    url = "https://openapi.naver.com/v1/search/news.json"
    headers = _get_headers()
    raw_items = []

    for start in range(1, 301, 100):
        try:
            params = {"query": keyword, "display": display, "start": start, "sort": sort}
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            if not items:
                break
            raw_items.extend(items)
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else 0
            if code == 429:
                st.error("⚠️ 네이버 뉴스 API 호출 한도 초과. 잠시 후 다시 시도해주세요.")
            elif code == 401:
                st.error("❌ 네이버 API 인증 실패. API 키를 확인해주세요.")
            else:
                st.error(f"❌ 네이버 뉴스 API 오류: HTTP {code}")
            st.stop()
        except requests.exceptions.RequestException as e:
            st.error(f"❌ 네이버 뉴스 API 연결 실패: {e}")
            st.stop()

    if not raw_items:
        return []

    # 전처리
    now = datetime.now()
    cutoff_30d = now - timedelta(days=30)
    cutoff_7d = now - timedelta(days=7)

    seen_links = set()
    processed = []
    for item in raw_items:
        link = item.get("originallink") or item.get("link", "")
        if link in seen_links:
            continue
        seen_links.add(link)

        dt, date_str, time_str = parse_pub_datetime(item.get("pubDate", ""))
        processed.append({
            "title_clean":    clean_html(item.get("title", "")),
            "desc_clean":     clean_html(item.get("description", "")),
            "media_name":     extract_media_name(link),
            "pub_dt":         dt,
            "pub_date_str":   date_str,
            "pub_time_str":   time_str,
            "originallink":   link,
            "link":           item.get("link", link),
            "is_within_7d":   dt.replace(tzinfo=None) >= cutoff_7d.replace(tzinfo=None) if dt.tzinfo else dt >= cutoff_7d,
            "is_within_30d":  dt.replace(tzinfo=None) >= cutoff_30d.replace(tzinfo=None) if dt.tzinfo else dt >= cutoff_30d,
        })

    return processed


def get_latest_articles(news_items: list[dict], n: int = 5) -> list[dict]:
    """
    전처리된 뉴스 리스트에서 최신 n건 추출.
    sort=date 기준 이미 최신순이므로 앞에서 n건.
    """
    latest = news_items[:n]
    return [
        {
            "title":       item["title_clean"],
            "media":       item["media_name"],
            "date":        item["pub_date_str"],
            "time":        item["pub_time_str"],
            "link":        item["originallink"] or item["link"],
            "description": item["desc_clean"],
        }
        for item in latest
    ]
