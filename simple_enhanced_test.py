#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 강화된 연구 서비스 테스트
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_enhanced_research():
    """기본 강화된 연구 서비스 테스트"""
    print("=== 간단한 강화된 연구 서비스 테스트 ===")
    
    try:
        from enhanced_research_service import EnhancedResearchService
        
        research_service = EnhancedResearchService()
        print("SUCCESS: 강화된 연구 서비스 초기화 완료")
        
        # 간단한 네이버 검색만 테스트
        test_query = "포스코인터내셔널"
        print(f"TEST: {test_query} 검색 중...")
        
        naver_results = research_service._search_naver_news(test_query)
        print(f"SUCCESS: 네이버 뉴스 {len(naver_results)}건 수집")
        
        if naver_results:
            print("\n상위 3개 결과:")
            for i, item in enumerate(naver_results[:3], 1):
                print(f"{i}. {item.get('title', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_data_based_llm_import():
    """DataBasedLLM 가져오기 테스트"""
    print("\n=== DataBasedLLM 가져오기 테스트 ===")
    
    try:
        from data_based_llm import DataBasedLLM
        print("SUCCESS: DataBasedLLM 모듈 가져오기 성공")
        
        # 간단한 초기화 테스트
        llm = DataBasedLLM()
        print("SUCCESS: DataBasedLLM 초기화 성공")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    """메인 테스트"""
    print("START: 간단한 강화된 시스템 테스트")
    print("=" * 50)
    
    # 1. 강화된 연구 서비스 테스트
    research_success = test_basic_enhanced_research()
    
    # 2. DataBasedLLM 테스트
    llm_success = test_data_based_llm_import()
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    print(f"- 강화된 연구 서비스: {'SUCCESS' if research_success else 'FAILED'}")
    print(f"- DataBasedLLM: {'SUCCESS' if llm_success else 'FAILED'}")
    
    if research_success and llm_success:
        print("\nCOMPLETE: 기본 컴포넌트 테스트 성공!")
        print("강화된 사실확인 시스템 준비 완료")
    else:
        print("\nWARNING: 일부 컴포넌트 테스트 실패")
    
    print("\n테스트 완료.")

if __name__ == "__main__":
    main()