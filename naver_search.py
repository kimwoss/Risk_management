"""
네이버 검색 API 연동 모듈
언론 총괄담당자를 위한 이슈 관련 정보 검색
"""
import os
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

class NaverSearchAPI:
    """네이버 검색 API 클래스"""
    
    def __init__(self):
        """네이버 검색 API 초기화"""
        load_dotenv()
        self.client_id = os.getenv('NAVER_CLIENT_ID')
        self.client_secret = os.getenv('NAVER_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("네이버 API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        
        self.base_url = "https://openapi.naver.com/v1/search"
        self.headers = {
            'X-Naver-Client-Id': self.client_id,
            'X-Naver-Client-Secret': self.client_secret
        }
    
    def search_news(self, query: str, display: int = 10, sort: str = "date") -> Dict[str, Any]:
        """
        뉴스 검색
        
        Args:
            query (str): 검색 쿼리
            display (int): 검색 결과 개수 (1~100)
            sort (str): 정렬 방식 ("sim": 정확도순, "date": 날짜순)
        
        Returns:
            Dict: 검색 결과
        """
        url = f"{self.base_url}/news.json"
        params = {
            'query': query,
            'display': display,
            'sort': sort
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"뉴스 검색 API 호출 오류: {str(e)}")
            return {"items": []}
    
    def search_blog(self, query: str, display: int = 10, sort: str = "date") -> Dict[str, Any]:
        """
        블로그 검색
        
        Args:
            query (str): 검색 쿼리
            display (int): 검색 결과 개수 (1~100)
            sort (str): 정렬 방식 ("sim": 정확도순, "date": 날짜순)
        
        Returns:
            Dict: 검색 결과
        """
        url = f"{self.base_url}/blog.json"
        params = {
            'query': query,
            'display': display,
            'sort': sort
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"블로그 검색 API 호출 오류: {str(e)}")
            return {"items": []}

class IssueResearchService:
    """발생 이슈 연구 서비스"""
    
    def __init__(self):
        """이슈 연구 서비스 초기화"""
        self.naver_api = NaverSearchAPI()
    
    def research_issue(self, issue_description: str) -> Dict[str, Any]:
        """
        발생 이슈에 대한 종합적인 연구 수행
        
        Args:
            issue_description (str): 발생 이슈 설명
        
        Returns:
            Dict: 연구 결과 (뉴스, 블로그, 분석 정보 포함)
        """
        # 검색 쿼리 최적화
        search_query = self._optimize_search_query(issue_description)
        
        # 다양한 소스에서 정보 수집
        research_data = {
            "original_issue": issue_description,
            "search_query": search_query,
            "timestamp": datetime.now().isoformat(),
            "news_results": [],
            "blog_results": [],
            "analysis_summary": {}
        }
        
        # 뉴스 검색 (최신순)
        print(f"🔍 뉴스 검색 중: {search_query}")
        news_data = self.naver_api.search_news(search_query, display=15, sort="date")
        research_data["news_results"] = self._process_news_results(news_data.get("items", []))
        
        # 블로그 검색 (관련성순)
        print(f"📝 블로그 검색 중: {search_query}")
        blog_data = self.naver_api.search_blog(search_query, display=10, sort="sim")
        research_data["blog_results"] = self._process_blog_results(blog_data.get("items", []))
        
        # 검색 결과 분석
        research_data["analysis_summary"] = self._analyze_search_results(research_data)
        
        return research_data
    
    def _optimize_search_query(self, issue_description: str) -> str:
        """검색 쿼리 최적화"""
        # 기본적인 키워드 추출 및 정제
        query = issue_description.strip()

        # 불필요한 문구 제거
        remove_phrases = ["발생한", "이슈", "문제", "상황", "관련", "대해서", "에 대한"]
        for phrase in remove_phrases:
            query = query.replace(phrase, "")

        # 공백 정리
        query = " ".join(query.split())

        # 정확한 검색이 필요한 복합어 처리
        # "포스코인터내셔널"과 같이 띄어쓰기 없는 고유명사는 큰따옴표로 감싸서 정확한 매칭
        exact_match_keywords = [
            "포스코인터내셔널",
            "POSCO인터내셔널",
            "POSCO INTERNATIONAL"
        ]

        for keyword in exact_match_keywords:
            if keyword in query:
                # 이미 큰따옴표로 감싸져 있지 않은 경우에만 추가
                if f'"{keyword}"' not in query:
                    query = query.replace(keyword, f'"{keyword}"')

        return query
    
    def _process_news_results(self, news_items: List[Dict]) -> List[Dict]:
        """뉴스 검색 결과 처리"""
        processed_news = []
        
        for item in news_items:
            processed_item = {
                "title": self._clean_html_tags(item.get("title", "")),
                "link": item.get("link", ""),
                "description": self._clean_html_tags(item.get("description", "")),
                "pub_date": item.get("pubDate", ""),
                "source_type": "news"
            }
            processed_news.append(processed_item)
        
        return processed_news
    
    def _process_blog_results(self, blog_items: List[Dict]) -> List[Dict]:
        """블로그 검색 결과 처리"""
        processed_blogs = []
        
        for item in blog_items:
            processed_item = {
                "title": self._clean_html_tags(item.get("title", "")),
                "link": item.get("link", ""),
                "description": self._clean_html_tags(item.get("description", "")),
                "blogger_name": item.get("bloggername", ""),
                "post_date": item.get("postdate", ""),
                "source_type": "blog"
            }
            processed_blogs.append(processed_item)
        
        return processed_blogs
    
    def _clean_html_tags(self, text: str) -> str:
        """HTML 태그 제거"""
        import re
        # HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', '', text)
        # HTML 엔티티 변환
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        clean_text = clean_text.replace('&quot;', '"').replace('&#39;', "'")
        
        return clean_text.strip()
    
    def _analyze_search_results(self, research_data: Dict) -> Dict[str, Any]:
        """검색 결과 분석"""
        news_count = len(research_data.get("news_results", []))
        blog_count = len(research_data.get("blog_results", []))
        
        # 최신 뉴스 시간 분석
        latest_news_date = None
        if research_data.get("news_results"):
            # 첫 번째 뉴스가 최신 (date 순으로 정렬했으므로)
            latest_news_date = research_data["news_results"][0].get("pub_date")
        
        analysis = {
            "total_sources": news_count + blog_count,
            "news_count": news_count,
            "blog_count": blog_count,
            "latest_news_date": latest_news_date,
            "coverage_level": self._assess_coverage_level(news_count, blog_count),
            "research_completeness": "완료" if (news_count > 0 or blog_count > 0) else "검색 결과 없음"
        }
        
        return analysis
    
    def _assess_coverage_level(self, news_count: int, blog_count: int) -> str:
        """언론 보도 수준 평가"""
        total_coverage = news_count + blog_count
        
        if total_coverage >= 20:
            return "높음 (광범위한 보도)"
        elif total_coverage >= 10:
            return "중간 (일정 수준의 관심)"
        elif total_coverage >= 5:
            return "낮음 (제한적 보도)"
        elif total_coverage > 0:
            return "매우 낮음 (최소 보도)"
        else:
            return "보도 없음"

def main():
    """테스트 함수"""
    try:
        research_service = IssueResearchService()
        
        # 테스트용 이슈
        test_issue = "전기차 배터리 화재 안전성"
        
        print(f"=== 이슈 연구 테스트: {test_issue} ===")
        results = research_service.research_issue(test_issue)
        
        print(f"\n📊 연구 결과 요약:")
        print(f"- 검색 쿼리: {results['search_query']}")
        print(f"- 뉴스 기사: {results['analysis_summary']['news_count']}건")
        print(f"- 블로그 포스트: {results['analysis_summary']['blog_count']}건")
        print(f"- 보도 수준: {results['analysis_summary']['coverage_level']}")
        
        print(f"\n📰 주요 뉴스 (상위 3건):")
        for i, news in enumerate(results['news_results'][:3], 1):
            print(f"{i}. {news['title']}")
            print(f"   설명: {news['description'][:100]}...")
            print(f"   링크: {news['link']}")
            print()
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()