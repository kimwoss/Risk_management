#!/usr/bin/env python3
"""
FAISS 인덱스 생성 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.services import EmbeddingService
from src.utils import DataLoader, Logger

def main():
    """FAISS 인덱스 생성 메인 함수"""
    logger = Logger.get_logger("build_index")
    
    try:
        print("🔍 기자문의 데이터 로드 중...")
        
        # 데이터 로드
        data_loader = DataLoader()
        df = data_loader.load_csv()
        
        if df.empty:
            print("⚠️ 처리할 데이터가 없습니다.")
            return
        
        print(f"✅ {len(df)}건의 데이터 로드 완료")
        
        # 임베딩 서비스 초기화
        embedding_service = EmbeddingService()
        
        print("📐 임베딩 생성 및 인덱스 구축 중...")
        
        # 인덱스 생성
        index, mapping = embedding_service.build_index_from_dataframe(df)
        
        print("✅ FAISS 인덱스 생성 완료!")
        print(f"📊 인덱스 크기: {index.ntotal}개 벡터")
        
        # 테스트 검색
        from src.services import SearchService
        search_service = SearchService()
        
        print("\n🔍 테스트 검색 실행...")
        sample_query = "메탄 누출 의혹에 대한 대응"
        results = search_service.search_similar_issues(sample_query)
        search_service.display_search_results(results, sample_query)
        
    except Exception as e:
        logger.error(f"인덱스 생성 중 오류: {e}")
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()