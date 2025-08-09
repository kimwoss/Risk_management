#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빠른 답변 퀄리티 테스트
"""

import sys
import os
from datetime import datetime
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def quick_quality_test():
    """빠른 퀄리티 테스트"""
    print("=== 답변 퀄리티 빠른 테스트 ===")
    
    try:
        from data_based_llm import DataBasedLLM
        
        llm = DataBasedLLM()
        print("SUCCESS: DataBasedLLM 초기화")
        
        # 간단한 테스트 케이스
        test_case = {
            "media": "조선일보",
            "reporter": "김기자", 
            "issue": "포스코인터내셔널 철강 제품 품질 이슈 발생"
        }
        
        print(f"테스트 실행: {test_case['issue']}")
        
        start_time = time.time()
        report = llm.generate_comprehensive_issue_report(
            test_case["media"],
            test_case["reporter"],
            test_case["issue"]
        )
        processing_time = time.time() - start_time
        
        print(f"\nSUCCESS: 처리 완료 ({processing_time:.2f}초)")
        print(f"보고서 길이: {len(report):,}자")
        
        # 품질 분석
        analysis = analyze_quality(report)
        
        print("\n=== 품질 분석 결과 ===")
        for key, value in analysis.items():
            print(f"{key}: {value}")
        
        # 결과 저장
        output_file = f"quick_quality_test_{datetime.now().strftime('%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== 답변 퀄리티 빠른 테스트 결과 ===\n")
            f.write(f"처리 시간: {processing_time:.2f}초\n")
            f.write(f"보고서 길이: {len(report):,}자\n\n")
            f.write("품질 분석:\n")
            for key, value in analysis.items():
                f.write(f"- {key}: {value}\n")
            f.write("\n" + "="*50 + "\n")
            f.write("생성된 보고서:\n")
            f.write("="*50 + "\n\n")
            f.write(report)
        
        print(f"결과 저장: {output_file}")
        
        return True, analysis, report
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False, None, None

def analyze_quality(report):
    """품질 분석"""
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
    """메인 테스트"""
    success, analysis, report = quick_quality_test()
    
    if success:
        print("\n=== 종합 평가 ===")
        
        # 점수 계산
        template_score = int(analysis["템플릿_준수도"].split("(")[1].split("%")[0])
        keyword_score = int(analysis["키워드_포함도"].split("(")[1].split("%")[0])
        structure_score = int(analysis["구조적_완성도"].split("(")[1].split("%")[0])
        
        overall_score = (template_score + keyword_score + structure_score) / 3
        
        print(f"전체 점수: {overall_score:.1f}/100")
        
        if overall_score >= 80:
            print("평가: 우수")
        elif overall_score >= 60:
            print("평가: 양호")
        else:
            print("평가: 개선 필요")
        
        # 개선 포인트 제시
        improvement_points = []
        if template_score < 80:
            improvement_points.append("템플릿 구조 준수도 향상")
        if keyword_score < 70:
            improvement_points.append("핵심 키워드 포함률 개선")
        if structure_score < 60:
            improvement_points.append("구조적 완성도 강화")
        
        if improvement_points:
            print("\n개선 포인트:")
            for point in improvement_points:
                print(f"- {point}")
    else:
        print("테스트 실패")

if __name__ == "__main__":
    main()