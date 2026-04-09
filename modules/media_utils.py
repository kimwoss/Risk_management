"""
media_utils.py
HTML 클리닝, 매체명 추출, 날짜/시간 파싱 유틸리티
"""
import re
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from datetime import datetime

# 도메인 → 매체명 매핑 (30~50개 주요 매체)
DOMAIN_TO_MEDIA = {
    "news.naver.com":       "네이버뉴스",
    "chosun.com":           "조선일보",
    "donga.com":            "동아일보",
    "joongang.co.kr":       "중앙일보",
    "joins.com":            "중앙일보",
    "hani.co.kr":           "한겨레",
    "ohmynews.com":         "오마이뉴스",
    "khan.co.kr":           "경향신문",
    "kmib.co.kr":           "국민일보",
    "munhwa.com":           "문화일보",
    "segye.com":            "세계일보",
    "seoul.co.kr":          "서울신문",
    "hankookilbo.com":      "한국일보",
    "newsis.com":           "뉴시스",
    "yonhapnews.co.kr":     "연합뉴스",
    "yna.co.kr":            "연합뉴스",
    "news1.kr":             "뉴스1",
    "newspim.com":          "뉴스핌",
    "mt.co.kr":             "머니투데이",
    "edaily.co.kr":         "이데일리",
    "hankyung.com":         "한국경제",
    "mk.co.kr":             "매일경제",
    "sedaily.com":          "서울경제",
    "fnnews.com":           "파이낸셜뉴스",
    "inews24.com":          "아이뉴스24",
    "zdnet.co.kr":          "ZDNet Korea",
    "etnews.com":           "전자신문",
    "dt.co.kr":             "디지털타임스",
    "itbiz.co.kr":          "IT비즈뉴스",
    "thebell.co.kr":        "더벨",
    "bloter.net":           "블로터",
    "businesspost.co.kr":   "비즈니스포스트",
    "bizhankook.com":       "비즈한국",
    "ebn.co.kr":            "EBN",
    "steelguru.com":        "SteelGuru",
    "posri.re.kr":          "포스코경영연구원",
    "steel-n.com":          "스틸앤",
    "kbi.re.kr":            "한국철강협회",
    "businesskorea.co.kr":  "Business Korea",
    "koreatimes.co.kr":     "Korea Times",
    "koreaherald.com":      "Korea Herald",
    "jtbc.co.kr":           "JTBC",
    "sbs.co.kr":            "SBS",
    "kbs.co.kr":            "KBS",
    "mbc.co.kr":            "MBC",
    "ytn.co.kr":            "YTN",
    "tvchosun.com":         "TV조선",
    "mbn.co.kr":            "MBN",
}


def clean_html(text: str) -> str:
    """HTML 태그 및 특수문자 제거"""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">") \
               .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    return text.strip()


def extract_media_name(url: str) -> str:
    """URL에서 매체명 추출"""
    if not url:
        return "알 수 없음"
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # www. 제거
        domain = re.sub(r"^www\.", "", domain)
        # 매핑 딕셔너리에서 직접 검색
        for key, name in DOMAIN_TO_MEDIA.items():
            if key in domain:
                return name
        # 도메인에서 추출 (2단계: example.co.kr → example)
        parts = domain.split(".")
        if len(parts) >= 2:
            return parts[-2].upper() if len(parts[-2]) <= 3 else parts[-2].capitalize()
        return domain
    except Exception:
        return "알 수 없음"


def parse_pub_datetime(pub_date_str: str):
    """
    네이버 뉴스 pubDate 파싱 → (datetime 객체, date_str 'YYYY-MM-DD', time_str 'HH:MM')
    """
    try:
        dt = parsedate_to_datetime(pub_date_str)
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M")
        return dt, date_str, time_str
    except Exception:
        now = datetime.now()
        return now, now.strftime("%Y-%m-%d"), now.strftime("%H:%M")
