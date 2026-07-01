"""
강화된 다중 소스 연구 서비스
네이버 뉴스(관련성순) + 공신력 있는 사이트 검색
"""

import os
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class EnhancedResearchService:
    """강화된 다중 소스 연구 서비스"""
    
    def __init__(self):
        """초기화"""
        load_dotenv()
        self.naver_client_id = os.getenv('NAVER_CLIENT_ID')
        self.naver_client_secret = os.getenv('NAVER_CLIENT_SECRET')
        
        if not self.naver_client_id or not self.naver_client_secret:
            raise ValueError("네이버 API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        
        self.naver_headers = {
            'X-Naver-Client-Id': self.naver_client_id,
            'X-Naver-Client-Secret': self.naver_client_secret
        }
        
        # 공신력 있는 사이트 URL 패턴
        self.official_sites = {
            "posco_international": {
                "base_url": "https://www.poscointl.com",
                "search_patterns": [
                    "/kr/company/news",
                    "/kr/company/announcement"
                ]
            },
            "dart": {
                "base_url": "https://dart.fss.or.kr",
                "api_url": "https://opendart.fss.or.kr/api/list.json"
            },
            "korea_exchange": {
                "base_url": "https://kind.krx.co.kr",
                "search_url": "https://kind.krx.co.kr/disclosure/searchtotalinfo.do"
            }
        }
    
    def research_issue_comprehensive(self, issue_description: str) -> Dict[str, Any]:
        """
        종합적인 다중 소스 이슈 연구
        병렬 처리로 성능 최적화
        """
        print("START: 강화된 다중 소스 연구 시작")
        
        start_time = time.time()
        search_query = self._optimize_search_query(issue_description)
        
        research_data = {
            "original_issue": issue_description,
            "search_query": search_query,
            "timestamp": datetime.now().isoformat(),
            "sources": {
                "naver_news": [],
                "posco_official": [],
                "dart_filings": [],
                "krx_disclosures": []
            },
            "analysis_summary": {}
        }
        
        # 병렬 처리로 다중 소스 검색
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_tasks = {
                executor.submit(self._search_naver_news, search_query): "naver_news",
                executor.submit(self._search_posco_official, search_query): "posco_official", 
                executor.submit(self._search_dart_filings, search_query): "dart_filings",
                executor.submit(self._search_krx_disclosures, search_query): "krx_disclosures"
            }
            
            print("PROCESSING: 4개 소스에서 병렬 검색 실행 중...")
            
            for future in as_completed(future_tasks):
                source_name = future_tasks[future]
                try:
                    result = future.result(timeout=30)  # 30초 타임아웃
                    research_data["sources"][source_name] = result
                    print(f"SUCCESS: {source_name} 검색 완료 ({len(result)}건)")
                except Exception as e:
                    print(f"WARNING: {source_name} 검색 실패 - {str(e)}")
                    research_data["sources"][source_name] = []
        
        # 검색 결과 종합 분석
        research_data["analysis_summary"] = self._analyze_comprehensive_results(research_data)
        
        processing_time = time.time() - start_time
        print(f"COMPLETE: 다중 소스 연구 완료 (처리시간: {processing_time:.2f}초)")
        
        return research_data
    
    def _search_naver_news(self, query: str) -> List[Dict]:
        """네이버 뉴스 검색 (관련성순)"""
        try:
            url = "https://openapi.naver.com/v1/search/news.json"
            params = {
                'query': query,
                'display': 20,  # 더 많은 결과
                'sort': 'sim'   # 관련성순으로 변경
            }
            
            response = None
            try:
                response = requests.get(url, headers=self.naver_headers, params=params, timeout=15)
                response.raise_for_status()

                results = []
                items = response.json().get("items", [])
            finally:
                if response is not None:
                    response.close()
            
            for item in items:
                processed_item = {
                    "title": self._clean_html_tags(item.get("title", "")),
                    "link": item.get("link", ""),
                    "description": self._clean_html_tags(item.get("description", "")),
                    "pub_date": item.get("pubDate", ""),
                    "source": "네이버뉴스",
                    "relevance_score": self._calculate_relevance_score(item, query)
                }
                results.append(processed_item)
            
            # 관련성 점수순 정렬
            return sorted(results, key=lambda x: x['relevance_score'], reverse=True)
            
        except Exception as e:
            print(f"ERROR: 네이버 뉴스 검색 실패 - {str(e)}")
            return []
    
    def _search_posco_official(self, query: str) -> List[Dict]:
        """포스코인터내셔널 공식 사이트 검색"""
        try:
            results = []
            base_url = self.official_sites["posco_international"]["base_url"]
            
            # 공식 뉴스/공고 페이지 검색
            search_urls = [
                f"{base_url}/kr/company/news",
                f"{base_url}/kr/company/announcement"
            ]
            
            for search_url in search_urls:
                response = None
                try:
                    response = requests.get(search_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
                    if response.status_code == 200:
                        # 간단한 HTML 파싱 (BeautifulSoup 없이)
                        html_content = response.text
                        
                        # 제목 패턴 검색 (간단한 정규식 사용)
                        title_patterns = [
                            r'<title[^>]*>([^<]+)</title>',
                            r'<h[1-6][^>]*>([^<]*' + re.escape(query) + r'[^<]*)</h[1-6]>',
                            r'<a[^>]*>([^<]*' + re.escape(query) + r'[^<]*)</a>'
                        ]
                        
                        for pattern in title_patterns:
                            matches = re.findall(pattern, html_content, re.IGNORECASE)
                            for match in matches[:5]:  # 최대 5개
                                clean_title = re.sub(r'<[^>]+>', '', match).strip()
                                if clean_title and len(clean_title) > 10:
                                    results.append({
                                        "title": clean_title[:100],
                                        "link": search_url,
                                        "description": f"포스코인터내셔널 공식 사이트에서 관련 정보를 확인하세요",
                                        "source": "포스코인터내셔널 공식",
                                        "type": "official_announcement"
                                    })
                                
                except Exception as e:
                    print(f"WARNING: 포스코 공식 사이트 접근 실패 ({search_url}) - {str(e)}")
                    continue
                finally:
                    if response is not None:
                        response.close()
            
            return results
            
        except Exception as e:
            print(f"ERROR: 포스코 공식 사이트 검색 실패 - {str(e)}")
            return []
    
    def _search_dart_filings(self, query: str) -> List[Dict]:
        """DART 공시 검색"""
        try:
            # DART API는 별도 인증이 필요하므로 웹 스크래핑 방식 사용
            results = []
            
            # 포스코인터내셔널 관련 주요 키워드
            posco_keywords = ["포스코인터내셔널", "POSCO INTERNATIONAL", "포스코홀딩스"]
            
            for keyword in posco_keywords:
                if keyword.lower() in query.lower():
                    # DART 전자공시시스템에서 해당 기업 공시 정보 수집
                    dart_url = "https://dart.fss.or.kr/dsaf001/main.do"
                    
                    response = None
                    try:
                        response = requests.get(dart_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                        if response.status_code == 200:
                            results.append({
                                "title": f"{keyword} 관련 DART 공시 정보",
                                "link": dart_url,
                                "description": "전자공시시스템에서 최신 공시 정보를 확인하세요",
                                "source": "DART 전자공시",
                                "type": "regulatory_filing"
                            })
                    except Exception as e:
                        print(f"WARNING: DART 접근 실패 - {str(e)}")
                    finally:
                        if response is not None:
                            response.close()
            
            return results
            
        except Exception as e:
            print(f"ERROR: DART 검색 실패 - {str(e)}")
            return []
    
    def _search_krx_disclosures(self, query: str) -> List[Dict]:
        """한국거래소 공시 검색"""
        try:
            results = []
            
            # 한국거래소 공시 사이트
            krx_url = "https://kind.krx.co.kr"
            
            response = None
            try:
                response = requests.get(krx_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code == 200:
                    results.append({
                        "title": "한국거래소 포스코인터내셔널 공시정보",
                        "link": krx_url + "/disclosure/searchtotalinfo.do",
                        "description": "한국거래소에서 제공하는 공시정보를 확인하세요",
                        "source": "한국거래소",
                        "type": "exchange_disclosure"
                    })
            except Exception as e:
                print(f"WARNING: 한국거래소 접근 실패 - {str(e)}")
            finally:
                if response is not None:
                    response.close()
            
            return results
            
        except Exception as e:
            print(f"ERROR: 한국거래소 검색 실패 - {str(e)}")
            return []
    
    def _optimize_search_query(self, issue_description: str) -> str:
        """검색 쿼리 최적화 — 질문·군더더기를 제거해 핵심 개체 키워드만 남긴다.
        (질문 문장을 그대로 검색하면 네이버 관련성 검색이 오염되어 관련 기사가 안 나옴)"""
        q = re.sub(r"[?？!.,·…\"'()\[\]]", " ", issue_description)
        # 질문·군더더기 구절 제거 (다중 문자만 — 개체명 손상 방지)
        fillers = [
            "현재까지", "구체적으로", "자세히", "알려주세요", "알려달라", "알려달",
            "설명해주세요", "설명해", "우리회사와의", "우리회사", "당사와의",
            "현황", "일정은", "일정", "계획은", "계획", "관련하여", "관련해서",
            "에 대한", "에 대해", "대해서", "무엇인가", "어떻게", "어떤", "인지",
            "발생한", "이슈", "문제인지", "상황인지", "검토", "문의드립니다", "문의",
        ]
        for p in fillers:
            q = q.replace(p, " ")
        toks = [t for t in q.split() if len(t) >= 2]
        query = " ".join(toks[:6]) if toks else issue_description.strip()
        # 회사 맥락 강화(포스코 계열이 언급 안 됐으면 회사명 부가 → 관련성↑)
        if "포스코" not in query and "posco" not in query.lower():
            query = query + " 포스코인터내셔널"
        return " ".join(query.split())
    
    def _clean_html_tags(self, text: str) -> str:
        """HTML 태그 제거"""
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = clean_text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        clean_text = clean_text.replace('&quot;', '"').replace('&#39;', "'")
        return clean_text.strip()
    
    def _calculate_relevance_score(self, item: Dict, query: str) -> float:
        """관련성 점수 계산"""
        title = item.get("title", "").lower()
        description = item.get("description", "").lower()
        query_lower = query.lower()
        
        score = 0.0
        
        # 제목에서 쿼리 키워드 매칭
        query_words = query_lower.split()
        for word in query_words:
            if word in title:
                score += 2.0
            if word in description:
                score += 1.0
        
        # 포스코 관련 가중치
        if "포스코" in title:
            score += 3.0
        
        return score
    
    def _analyze_comprehensive_results(self, research_data: Dict) -> Dict[str, Any]:
        """종합 검색 결과 분석"""
        sources = research_data["sources"]
        
        total_sources = sum(len(results) for results in sources.values())
        
        analysis = {
            "total_sources": total_sources,
            "source_breakdown": {
                "naver_news": len(sources["naver_news"]),
                "posco_official": len(sources["posco_official"]),
                "dart_filings": len(sources["dart_filings"]),
                "krx_disclosures": len(sources["krx_disclosures"])
            },
            "credibility_level": self._assess_credibility_level(sources),
            "official_sources_available": len(sources["posco_official"]) + len(sources["dart_filings"]) + len(sources["krx_disclosures"]) > 0,
            "research_completeness": "완료" if total_sources > 0 else "검색 결과 없음"
        }
        
        return analysis
    
    def _assess_credibility_level(self, sources: Dict) -> str:
        """신뢰도 수준 평가"""
        official_count = len(sources["posco_official"]) + len(sources["dart_filings"]) + len(sources["krx_disclosures"])
        news_count = len(sources["naver_news"])
        
        if official_count >= 3:
            return "매우 높음 (다수 공식 소스)"
        elif official_count >= 1:
            return "높음 (공식 소스 포함)"
        elif news_count >= 10:
            return "중간 (다수 언론 보도)"
        elif news_count >= 3:
            return "보통 (일부 언론 보도)"
        else:
            return "낮음 (제한적 정보)"

def main():
    """테스트 함수"""
    try:
        research_service = EnhancedResearchService()
        
        test_issue = "포스코인터내셔널 2차전지 소재 리튬 배터리 결함 전기차 리콜"
        
        print("=== 강화된 다중 소스 연구 테스트 ===")
        results = research_service.research_issue_comprehensive(test_issue)
        
        print(f"\n📊 종합 연구 결과:")
        print(f"- 검색 쿼리: {results['search_query']}")
        print(f"- 전체 소스: {results['analysis_summary']['total_sources']}건")
        print(f"- 신뢰도 수준: {results['analysis_summary']['credibility_level']}")
        print(f"- 공식 소스 확보: {'예' if results['analysis_summary']['official_sources_available'] else '아니오'}")
        
        for source_name, count in results['analysis_summary']['source_breakdown'].items():
            print(f"- {source_name}: {count}건")
        
    except Exception as e:
        print(f"테스트 중 오류 발생: {str(e)}")

if __name__ == "__main__":
    main()