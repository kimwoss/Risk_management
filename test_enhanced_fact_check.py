#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
강화된 사실확인 시스템 테스트
"""

import sys
import os
from datetime import datetime
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_research():
    """강화된 연구 서비스 단독 테스트"""
    print("=== 강화된 연구 서비스 테스트 ===")
    
    try:
        from enhanced_research_service import EnhancedResearchService
        
        research_service = EnhancedResearchService()
        test_issue = "포스코인터내셔널 2차전지 소재 리튬 배터리 결함 전기차 리콜"
        
        print(f"테스트 이슈: {test_issue}")
        print("-" * 50)
        
        start_time = time.time()
        results = research_service.research_issue_comprehensive(test_issue)
        end_time = time.time()
        
        print(f"\n처리 시간: {end_time - start_time:.2f}초")
        print(f"총 수집 소스: {results['analysis_summary']['total_sources']}건")
        print(f"신뢰도 수준: {results['analysis_summary']['credibility_level']}")
        
        for source_name, count in results['analysis_summary']['source_breakdown'].items():
            print(f"- {source_name}: {count}건")
        
        # 결과 상세 출력
        print("\n=== 수집된 소스 상세 ===")
        for source_type, items in results['sources'].items():
            if items:
                print(f"\nSOURCE: {source_type} ({len(items)}건):")
                for i, item in enumerate(items[:3], 1):
                    print(f"{i}. {item.get('title', 'N/A')}")
                    if item.get('description'):
                        print(f"   {item['description'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"강화된 연구 서비스 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_enhanced_fact_check():
    """강화된 사실확인이 적용된 8단계 프로세스 테스트"""
    print("\n=== 강화된 사실확인 8단계 프로세스 테스트 ===")
    
    try:
        from data_based_llm import DataBasedLLM
        
        # DataBasedLLM 초기화
        llm = DataBasedLLM()
        
        # 테스트 데이터
        media_name = "조선일보"
        reporter_name = "김기자"
        issue_description = "포스코인터내셔널 2차전지 소재에서 리튬 배터리 결함 발견으로 전기차 5만대 리콜 검토"
        
        print(f"언론사: {media_name}")
        print(f"기자명: {reporter_name}")
        print(f"이슈: {issue_description}")
        print("-" * 60)
        
        start_time = time.time()
        
        # 강화된 사실확인이 포함된 완전한 8단계 프로세스 실행
        report = llm.generate_comprehensive_issue_report(
            media_name, 
            reporter_name, 
            issue_description
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"\nSUCCESS: 강화된 8단계 프로세스 완료!")
        print(f"처리 시간: {processing_time:.2f}초")
        print(f"보고서 길이: {len(report):,}자")
        
        # 결과 저장
        output_file = f"enhanced_fact_check_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("강화된 사실확인 시스템 적용 8단계 프로세스 결과\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"처리 시간: {processing_time:.2f}초\n")
            f.write(f"보고서 길이: {len(report):,}자\n\n")
            f.write("주요 개선사항:\n")
            f.write("- 네이버 뉴스: 관련성순 검색으로 변경\n")
            f.write("- 블로그 검색: 제거\n")
            f.write("- 공신력 있는 소스 추가: 포스코 공식, DART, 한국거래소\n")
            f.write("- 병렬 처리: 4개 소스 동시 검색\n")
            f.write("- 강화된 사실확인: 다중 소스 교차 검증\n\n")
            f.write("=" * 70 + "\n")
            f.write("생성된 보고서:\n")
            f.write("=" * 70 + "\n\n")
            f.write(report)
        
        print(f"결과 저장: {output_file}")
        
        # 보고서 미리보기
        print(f"\nPREVIEW: 보고서 미리보기:")
        print("-" * 60)
        preview = report[:800] + "\n\n... (이하 생략) ..." if len(report) > 800 else report
        print(preview)
        print("-" * 60)
        
        return True
        
    except Exception as e:
        print(f"강화된 사실확인 8단계 프로세스 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행"""
    print("START: 강화된 사실확인 시스템 종합 테스트 시작")
    print("=" * 70)
    
    # 1. 강화된 연구 서비스 단독 테스트
    research_success = test_enhanced_research()
    
    if research_success:
        print("\nSUCCESS: 강화된 연구 서비스 테스트 성공!")
        
        # 2. 통합 8단계 프로세스 테스트
        integrated_success = test_enhanced_fact_check()
        
        if integrated_success:
            print("\nCOMPLETE: 모든 테스트 성공!")
            print("강화된 사실확인 시스템이 성공적으로 적용되었습니다.")
            print("\n주요 개선사항:")
            print("- 다중 소스 병렬 검색 (네이버뉴스, 포스코공식, DART, 한국거래소)")
            print("- 네이버 뉴스 관련성순 검색")
            print("- 블로그 검색 제거")
            print("- 공신력 있는 소스 우선 활용")
            print("- 교차 검증 기반 사실확인")
        else:
            print("\nERROR: 통합 8단계 프로세스 테스트 실패")
    else:
        print("\nERROR: 강화된 연구 서비스 테스트 실패")
    
    print("\n테스트 완료.")

if __name__ == "__main__":
    main()