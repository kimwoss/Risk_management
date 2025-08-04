import numpy as np
from datetime import datetime
from typing import List, Dict, Optional
from config.settings import settings
from src.services.embedding_service import EmbeddingService
from src.utils.logger import Logger

class SearchService:
    """유사도 검색 서비스"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.embedding_service = EmbeddingService()
    
    def search_similar_issues(
        self, 
        query: str, 
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """입력 문장에 대해 FAISS에서 유사하면서 최신 사례 top-k 반환"""
        if top_k is None:
            top_k = settings.DEFAULT_TOP_K
        
        try:
            # 인덱스 로드
            index, mapping = self.embedding_service.load_index()
            
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_service.model.encode([query])
            
            # 유사도 검색
            search_count = min(settings.DEFAULT_SEARCH_COUNT, len(mapping))
            D, I = index.search(query_embedding, search_count)
            
            # 결과 정리 및 날짜별 정렬
            results = self._process_search_results(I[0], mapping)
            
            # 상위 top_k 결과 반환
            top_results = results[:top_k]
            
            self.logger.info(f"검색 완료: 쿼리='{query}', 결과={len(top_results)}개")
            return top_results
            
        except Exception as e:
            error_msg = f"검색 중 오류 발생: {str(e)}"
            self.logger.error(error_msg)
            return []
    
    def _process_search_results(
        self, 
        indices: np.ndarray, 
        mapping: List[Dict]
    ) -> List[Dict]:
        """검색 결과 처리 및 날짜별 정렬"""
        results = []
        
        for idx in indices:
            if idx < len(mapping):
                issue = mapping[idx]
                issue_date = self._parse_date(issue.get('발생 일시', ''))
                results.append({
                    'date': issue_date,
                    'data': issue
                })
        
        # 날짜 내림차순 정렬 (최신순)
        results.sort(reverse=True, key=lambda x: x['date'])
        
        return [result['data'] for result in results]
    
    def _parse_date(self, date_str: str) -> datetime:
        """다양한 형식의 날짜 문자열 파싱"""
        if not date_str:
            return datetime.min
        
        try:
            # 다양한 날짜 형식 시도
            for fmt in settings.DATE_FORMATS:
                try:
                    return datetime.strptime(date_str.split()[0], fmt)
                except (ValueError, IndexError):
                    continue
            
            # 모든 형식 실패시
            return datetime.min
            
        except Exception:
            return datetime.min
    
    def display_search_results(
        self, 
        results: List[Dict], 
        query: str
    ):
        """검색 결과 출력"""
        if not results:
            print("검색 결과가 없습니다.")
            return
        
        print(f"\n📌 '{query}' 검색 결과 (총 {len(results)}건):\n")
        
        for rank, issue in enumerate(results, 1):
            date_str = issue.get('발생 일시', 'N/A')
            content = issue.get('이슈 발생 보고', 'N/A')
            order_num = issue.get('순번', 'N/A')
            
            print(f"[{rank}위] 순번: {order_num} ({date_str})")
            print(f"내용: {content}\n")