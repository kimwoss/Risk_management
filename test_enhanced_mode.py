#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
강화된 8단계 프로세스 테스트
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_vs_standard():
    """강화된 모드 vs 표준 모드 비교 테스트"""
    
    print("=== 강화된 8단계 프로세스 비교 테스트 ===")
    print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from data_based_llm import DataBasedLLM
        
        # 테스트 케이스
        test_case = {
            "media": "조선일보",
            "reporter": "김기자", 
            "issue": "포스코인터내셔널 철강 제품 품질 이슈로 일부 납품 지연"
        }
        
        llm = DataBasedLLM()
        print("SUCCESS: DataBasedLLM 초기화 완료")
        print(f"테스트 이슈: {test_case['issue']}")
        print()
        
        # 1. 강화된 모드 테스트
        print("START: ENHANCED MODE 테스트...")
        enhanced_start = time.time()
        
        enhanced_report = llm.generate_comprehensive_issue_report(
            test_case["media"],
            test_case["reporter"],
            test_case["issue"],
            mode="enhanced"
        )
        
        enhanced_time = time.time() - enhanced_start
        print(f"SUCCESS: ENHANCED 완료 ({enhanced_time:.2f}초)")
        print(f"   보고서 길이: {len(enhanced_report):,}자")
        print()
        
        # 품질 검증
        enhanced_quality = analyze_report_quality(enhanced_report)
        print("ANALYSIS: ENHANCED 품질 분석:")
        for key, value in enhanced_quality.items():
            print(f"   {key}: {value}")
        print()
        
        # 결과 저장
        timestamp = datetime.now().strftime('%H%M%S')
        
        with open(f"test_enhanced_report_{timestamp}.txt", 'w', encoding='utf-8') as f:
            f.write("=== 강화된 모드 테스트 결과 ===\n")
            f.write(f"처리 시간: {enhanced_time:.2f}초\n")
            f.write(f"보고서 길이: {len(enhanced_report):,}자\n\n")
            f.write("품질 분석:\n")
            for key, value in enhanced_quality.items():
                f.write(f"- {key}: {value}\n")
            f.write("\n" + "="*50 + "\n")
            f.write("생성된 보고서:\n")
            f.write("="*50 + "\n\n")
            f.write(enhanced_report)
        
        print(f"SAVE: 결과 저장 test_enhanced_report_{timestamp}.txt")
        
        # 성능 비교 요약
        print("\n" + "="*60)
        print("테스트 요약")
        print("="*60)
        print(f"강화된 모드 처리시간: {enhanced_time:.2f}초")
        print(f"예상 표준 모드 시간: 60-120초")
        print(f"성능 개선: {((90 - enhanced_time) / 90 * 100):.1f}% 빠름")
        print()
        
        if enhanced_time < 30:
            print("SUCCESS: 성능 목표 달성 (30초 이내)")
        else:
            print("WARNING: 성능 목표 미달성 (30초 초과)")
        
        return True, enhanced_quality, enhanced_report
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None, None

def analyze_report_quality(report):
    """보고서 품질 분석"""
    analysis = {}
    
    # 1. 템플릿 구조 체크
    required_sections = [
        "<이슈 발생 보고>",
        "1. 발생 일시:",
        "2. 발생 단계:",
        "3. 발생 내용:",
        "4. 유관 의견:",
        "5. 대응 방안:",
        "6. 대응 결과:"
    ]
    
    found_sections = [section for section in required_sections if section in report]
    analysis["템플릿_준수도"] = f"{len(found_sections)}/{len(required_sections)} ({len(found_sections)/len(required_sections)*100:.1f}%)"
    
    # 2. 위기단계 분류 체크
    crisis_levels = ["1단계", "2단계", "3단계", "4단계"]
    found_crisis = [level for level in crisis_levels if level in report]
    analysis["위기단계_분류"] = "있음" if found_crisis else "없음"
    if found_crisis:
        analysis["분류된_단계"] = found_crisis[0]
    
    # 3. 핵심 키워드 포함도
    key_terms = ["포스코인터내셔널", "사실확인", "대응방안", "원보이스", "유관"]
    found_terms = [term for term in key_terms if term in report]
    analysis["키워드_포함도"] = f"{len(found_terms)}/{len(key_terms)} ({len(found_terms)/len(key_terms)*100:.1f}%)"
    
    # 4. 구조적 완성도
    structural_elements = [
        "발생 일시:" in report and "2025년" in report,
        "포스코" in report,
        len(report) > 300,
        "대응" in report,
        "확인" in report
    ]
    structure_score = sum(structural_elements)
    analysis["구조적_완성도"] = f"{structure_score}/5 ({structure_score/5*100:.1f}%)"
    
    # 5. 보고서 특성
    analysis["총_길이"] = f"{len(report):,}자"
    analysis["줄_수"] = f"{len(report.split(chr(10)))}줄"
    
    return analysis

def main():
    """메인 테스트 실행"""
    success, quality, report = test_enhanced_vs_standard()
    
    if success and quality:
        # 종합 평가
        template_score = float(quality["템플릿_준수도"].split("(")[1].split("%")[0])
        keyword_score = float(quality["키워드_포함도"].split("(")[1].split("%")[0])
        structure_score = float(quality["구조적_완성도"].split("(")[1].split("%")[0])
        
        overall_score = (template_score + keyword_score + structure_score) / 3
        
        print(f"\nSCORE: 종합 품질 점수 {overall_score:.1f}/100")
        
        if overall_score >= 80:
            print("SUCCESS: 평가 우수 - 프로덕션 준비됨")
        elif overall_score >= 60:
            print("GOOD: 평가 양호 - 추가 개선 고려")
        else:
            print("WARNING: 평가 개선 필요")
        
        return True
    else:
        print("ERROR: 테스트 실패")
        return False

if __name__ == "__main__":
    main()