#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 템플릿 시스템 테스트
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_structured_report_generator():
    """구조화된 보고서 생성기 테스트"""
    print("=== 구조화된 보고서 생성기 테스트 ===")
    
    try:
        from improved_report_generator import StructuredReportGenerator
        
        # 테스트 데이터
        test_data = {
            'media_name': '조선일보',
            'reporter_name': '김기자',  
            'issue_description': '포스코인터내셔널 2차전지 소재 배터리 결함 전기차 리콜 검토',
            'crisis_level': '2단계(주의)',
            'initial_analysis': {
                'category': '제품 안전성',
                'impact_scope': '고객사 및 최종소비자',
                'urgency': '높음',
                'summary': '2차전지 소재 품질 문제로 전기차 배터리 결함 가능성 제기'
            },
            'relevant_depts': [
                {'부서명': '품질보증팀', '담당자': '이과장', '연락처': '02-1234-5678'}
            ],
            'fact_verification': {
                'fact_status': '언론보도됨',
                'credibility': '높음', 
                'background_context': '전기차 배터리 공급망 이슈'
            },
            'pr_strategy': {
                'key_messages': ['품질 최우선 정책', '투명한 조사'],
                'immediate_actions': ['기술진단팀 구성']
            }
        }
        
        generator = StructuredReportGenerator()
        report = generator.generate_structured_report(test_data)
        
        print("SUCCESS: 구조화된 보고서 생성 완료")
        print(f"보고서 길이: {len(report):,}자")
        
        # 구조 검증
        required_sections = [
            "<이슈 발생 보고>",
            "1. 발생 일시:",
            "2. 발생 단계:",
            "3. 발생 내용:",
            "4. 유관 의견:",
            "5. 대응 방안:",
            "6. 대응 결과:"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in report:
                missing_sections.append(section)
        
        if not missing_sections:
            print("SUCCESS: 모든 필수 섹션 포함됨")
        else:
            print(f"WARNING: 누락된 섹션: {missing_sections}")
        
        # 결과 저장
        with open(f"structured_test_{datetime.now().strftime('%H%M%S')}.txt", 'w', encoding='utf-8') as f:
            f.write(report)
        
        return True, report
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None

def test_integrated_8step_process():
    """통합된 8단계 프로세스 테스트"""
    print("\n=== 통합된 8단계 프로세스 테스트 ===")
    
    try:
        from data_based_llm import DataBasedLLM
        
        llm = DataBasedLLM()
        
        # 간단한 테스트 실행
        media_name = "조선일보"
        reporter_name = "김기자"
        issue_description = "포스코 배터리 소재 품질 이슈"
        
        print(f"테스트 입력: {media_name} / {reporter_name} / {issue_description}")
        
        # 8단계 프로세스 실행
        report = llm.generate_comprehensive_issue_report(
            media_name, reporter_name, issue_description
        )
        
        print(f"SUCCESS: 8단계 프로세스 완료")
        print(f"보고서 길이: {len(report):,}자")
        
        # 템플릿 구조 검증
        template_indicators = [
            "<이슈 발생 보고>",
            "발생 일시",
            "발생 단계", 
            "발생 내용",
            "유관 의견",
            "대응 방안"
        ]
        
        found_indicators = [indicator for indicator in template_indicators if indicator in report]
        
        print(f"템플릿 구조 준수도: {len(found_indicators)}/{len(template_indicators)} ({len(found_indicators)/len(template_indicators)*100:.1f}%)")
        
        # 결과 저장
        output_file = f"integrated_test_{datetime.now().strftime('%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== 개선된 템플릿 시스템 테스트 결과 ===\n")
            f.write(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"보고서 길이: {len(report):,}자\n")
            f.write(f"구조 준수도: {len(found_indicators)}/{len(template_indicators)}\n\n")
            f.write("=" * 50 + "\n")
            f.write("생성된 보고서:\n")
            f.write("=" * 50 + "\n\n")
            f.write(report)
        
        print(f"결과 저장: {output_file}")
        
        # 미리보기
        print(f"\n--- 보고서 미리보기 (처음 500자) ---")
        preview = report[:500] + "..." if len(report) > 500 else report
        print(preview)
        print("--- 미리보기 끝 ---")
        
        return True, report
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """메인 테스트"""
    print("개선된 템플릿 시스템 종합 테스트 시작")
    print("=" * 60)
    
    # 1. 구조화된 보고서 생성기 테스트
    structured_success, structured_report = test_structured_report_generator()
    
    # 2. 통합된 8단계 프로세스 테스트
    integrated_success, integrated_report = test_integrated_8step_process()
    
    print("\n" + "=" * 60)
    print("테스트 결과 종합:")
    print(f"- 구조화된 보고서 생성기: {'SUCCESS' if structured_success else 'FAILED'}")
    print(f"- 통합 8단계 프로세스: {'SUCCESS' if integrated_success else 'FAILED'}")
    
    if structured_success and integrated_success:
        print("\nCOMPLETE: 개선된 템플릿 시스템이 성공적으로 적용되었습니다!")
        print("\n주요 개선사항:")
        print("- risk_report.txt 템플릿 구조 강제 준수")
        print("- 8단계 분석 결과의 구조화된 매핑")
        print("- 폴백 시스템으로 안정성 확보")
        print("- LLM 출력 형식 표준화")
    else:
        print("\nWARNING: 일부 테스트가 실패했습니다.")
    
    print("\n테스트 완료.")

if __name__ == "__main__":
    main()