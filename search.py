#!/usr/bin/env python3
"""
유사도 검색 실행 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.services import SearchService
from src.utils import Logger

def main():
    """검색 메인 함수"""
    logger = Logger.get_logger("search")
    
    try:
        search_service = SearchService()
        
        if len(sys.argv) > 1:
            # 명령행 인수로 쿼리 받기
            query = " ".join(sys.argv[1:])
            print(f"🔍 검색 쿼리: {query}")
            
            results = search_service.search_similar_issues(query)
            search_service.display_search_results(results, query)
        else:
            # 대화형 모드
            print("🔍 유사도 검색 시스템")
            print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")
            
            while True:
                query = input("검색어를 입력하세요: ").strip()
                
                if query.lower() in ['quit', 'exit', '종료']:
                    print("👋 검색을 종료합니다.")
                    break
                
                if not query:
                    print("⚠️ 검색어를 입력해주세요.")
                    continue
                
                results = search_service.search_similar_issues(query)
                search_service.display_search_results(results, query)
                print("\n" + "="*50 + "\n")
        
    except Exception as e:
        logger.error(f"검색 중 오류: {e}")
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()