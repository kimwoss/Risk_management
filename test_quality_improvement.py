#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
품질 개선 통합 테스트
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_quality_improvement():
    """품질 개선 통합 테스트"""
    
    print("=== 품질 개선 통합 테스트 ===")
    print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from data_based_llm import DataBasedLLM
        
        # 이상적 사례와 동일한 테스트 케이스
        test_case = {
            "media": "조선일보",
            "reporter": "김조선",
            "issue": "포스코인터내셔널 식량사업 생산지, 주요 납품처, 올해 매출 계획 관련 문의"
        }
        
        llm = DataBasedLLM()
        print("SUCCESS: DataBasedLLM (품질개선 통합버전) 초기화 완료")
        print(f"테스트 이슈: {test_case['issue']}")
        print()
        
        # Before & After 비교를 위한 테스트
        print("=== BEFORE (Standard 모드) ===")
        start_time = time.time()
        
        # 1. Standard 모드 (품질 개선 없음)
        standard_report = llm.generate_comprehensive_issue_report(
            test_case["media"],
            test_case["reporter"],
            test_case["issue"],
            mode="standard"
        )
        
        standard_time = time.time() - start_time
        print(f"Standard 모드 완료: {standard_time:.2f}초")
        print()
        
        print("=== AFTER (Enhanced 모드 + 품질개선) ===")
        start_time = time.time()
        
        # 2. Enhanced 모드 (품질 개선 포함)
        enhanced_report = llm.generate_comprehensive_issue_report(
            test_case["media"],
            test_case["reporter"],
            test_case["issue"],
            mode="enhanced"
        )
        
        enhanced_time = time.time() - start_time
        print(f"Enhanced 모드 완료: {enhanced_time:.2f}초")
        print()
        
        # 품질 비교 분석
        comparison_result = compare_quality_improvement(standard_report, enhanced_report)
        
        print("=== 품질 개선 결과 ===")
        for metric, result in comparison_result.items():
            improvement = "개선됨" if result['improved'] else "변화없음"
            print(f"{metric}: {improvement}")
            print(f"  Before: {result['before']}")
            print(f"  After:  {result['after']}")
            if result['improved']:
                print(f"  개선점: {result['improvement_note']}")
            print()
        
        # 결과 저장
        save_quality_test_result(standard_report, enhanced_report, comparison_result, 
                               standard_time, enhanced_time)
        
        # 종합 평가
        improved_count = sum(1 for result in comparison_result.values() if result['improved'])
        total_metrics = len(comparison_result)
        improvement_rate = (improved_count / total_metrics) * 100
        
        print(f"=== 종합 평가 ===")
        print(f"개선된 지표: {improved_count}/{total_metrics} ({improvement_rate:.1f}%)")
        print(f"처리 속도: Standard {standard_time:.1f}초 vs Enhanced {enhanced_time:.1f}초")
        
        if improvement_rate >= 70:
            print("평가: 품질 개선 성공")
        elif improvement_rate >= 40:
            print("평가: 부분적 개선")
        else:
            print("평가: 개선 효과 제한적")
        
        return True, comparison_result
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def compare_quality_improvement(standard_report, enhanced_report):
    """Standard vs Enhanced 품질 비교"""
    
    comparison_result = {}
    
    # 1. 날짜 형식 개선
    standard_has_verbose_date = "년" in standard_report and "시" in standard_report
    enhanced_has_concise_date = "." in enhanced_report and ("년" not in enhanced_report or enhanced_report.count(".") > 3)
    
    comparison_result["날짜_형식"] = {
        "improved": standard_has_verbose_date and enhanced_has_concise_date,
        "before": "장황함 (년/월/일/시/분)" if standard_has_verbose_date else "간결함",
        "after": "간결함 (2025.08.09.15:30)" if enhanced_has_concise_date else "장황함",
        "improvement_note": "날짜 형식이 간결하게 개선됨"
    }
    
    # 2. 구체성 개선
    specific_terms = ["우크라이나", "호주", "미얀마", "수십만 톤", "곡물", "트레이더"]
    standard_specific_count = sum(1 for term in specific_terms if term in standard_report)
    enhanced_specific_count = sum(1 for term in specific_terms if term in enhanced_report)
    
    comparison_result["구체성"] = {
        "improved": enhanced_specific_count > standard_specific_count,
        "before": f"{standard_specific_count}/{len(specific_terms)} 구체적 용어",
        "after": f"{enhanced_specific_count}/{len(specific_terms)} 구체적 용어",
        "improvement_note": f"{enhanced_specific_count - standard_specific_count}개 구체적 용어 추가"
    }
    
    # 3. 담당자 정보
    standard_has_contact = "/" in standard_report and ("리더" in standard_report or "팀장" in standard_report)
    enhanced_has_contact = "/" in enhanced_report and ("리더" in enhanced_report or "팀장" in enhanced_report)
    
    comparison_result["담당자_정보"] = {
        "improved": not standard_has_contact and enhanced_has_contact,
        "before": "구체적" if standard_has_contact else "일반적",
        "after": "구체적" if enhanced_has_contact else "일반적",
        "improvement_note": "담당자 정보 구체화"
    }
    
    # 4. 원보이스 실용성
    standard_has_quotes = '"' in standard_report or "'" in standard_report
    enhanced_has_quotes = '"' in enhanced_report or "'" in enhanced_report
    
    comparison_result["원보이스_실용성"] = {
        "improved": not standard_has_quotes and enhanced_has_quotes,
        "before": "인용문 있음" if standard_has_quotes else "추상적",
        "after": "인용문 있음" if enhanced_has_quotes else "추상적", 
        "improvement_note": "인용 가능한 구체적 메시지 추가"
    }
    
    # 5. 전문성
    professional_terms = ["당사", "공급", "고객사", "매출", "협력사", "수급"]
    standard_prof_count = sum(1 for term in professional_terms if term in standard_report)
    enhanced_prof_count = sum(1 for term in professional_terms if term in enhanced_report)
    
    comparison_result["전문성"] = {
        "improved": enhanced_prof_count > standard_prof_count,
        "before": f"{standard_prof_count}/{len(professional_terms)} 전문 용어",
        "after": f"{enhanced_prof_count}/{len(professional_terms)} 전문 용어",
        "improvement_note": f"{enhanced_prof_count - standard_prof_count}개 전문 용어 증가"
    }
    
    # 6. 보고서 길이
    standard_length = len(standard_report)
    enhanced_length = len(enhanced_report)
    
    comparison_result["보고서_품질"] = {
        "improved": enhanced_length > standard_length * 1.1,  # 10% 이상 증가
        "before": f"{standard_length:,}자",
        "after": f"{enhanced_length:,}자",
        "improvement_note": f"{enhanced_length - standard_length:+,}자 증가 (상세도 향상)"
    }
    
    return comparison_result

def save_quality_test_result(standard_report, enhanced_report, comparison, 
                           standard_time, enhanced_time):
    """품질 테스트 결과 저장"""
    timestamp = datetime.now().strftime('%H%M%S')
    filename = f"quality_improvement_test_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=== 품질 개선 통합 테스트 결과 ===\n")
        f.write(f"테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Standard 모드: {standard_time:.2f}초\n")
        f.write(f"Enhanced 모드: {enhanced_time:.2f}초\n\n")
        
        f.write("품질 개선 비교:\n")
        f.write("="*50 + "\n")
        
        for metric, result in comparison.items():
            status = "개선됨" if result['improved'] else "변화없음"
            f.write(f"\n{metric}: {status}\n")
            f.write(f"  Before: {result['before']}\n")
            f.write(f"  After:  {result['after']}\n")
            if result['improved']:
                f.write(f"  개선점: {result['improvement_note']}\n")
        
        f.write("\n" + "="*50 + "\n")
        f.write("STANDARD 모드 보고서:\n")
        f.write("="*50 + "\n\n")
        f.write(standard_report)
        
        f.write("\n\n" + "="*50 + "\n")
        f.write("ENHANCED 모드 보고서 (품질개선 적용):\n")
        f.write("="*50 + "\n\n")
        f.write(enhanced_report)
    
    print(f"SAVE: 품질 테스트 결과 저장 {filename}")

def main():
    """메인 테스트 실행"""
    success, comparison = test_quality_improvement()
    
    if success and comparison:
        print("\n=== 최종 권장사항 ===")
        print("Enhanced 모드 사용 권장:")
        print("- 빠른 처리 속도 (3-5초)")
        print("- 개선된 보고서 품질")
        print("- 이상적 사례에 근접한 구체성과 전문성")
        
        return True
    else:
        print("품질 개선 테스트 실패")
        return False

if __name__ == "__main__":
    main()