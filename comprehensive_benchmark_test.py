#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
종합 벤치마킹 테스트 - 두 가지 이상적 사례 모두 검증
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_comprehensive_benchmark():
    """두 가지 이상적 사례 종합 벤치마킹"""
    
    print("=== 종합 벤치마킹 테스트 ===")
    print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from data_based_llm import DataBasedLLM
        
        # 두 가지 테스트 케이스
        test_cases = [
            {
                "name": "식량사업_문의_사례",
                "media": "조선일보",
                "reporter": "김조선",
                "issue": "포스코인터내셔널 식량사업 생산지, 주요 납품처, 올해 매출 계획 관련 문의",
                "type": "business_inquiry"
            },
            {
                "name": "2분기_실적_문의_사례", 
                "media": "조선일보",
                "reporter": "김조선",
                "issue": "2025년 2분기 포스코인터내셔널 주요사업별 실적과 향후 계획 관련 문의",
                "type": "financial_results"
            }
        ]
        
        llm = DataBasedLLM()
        print("SUCCESS: DataBasedLLM (통합 특화 모듈) 초기화 완료")
        print()
        
        overall_results = {}
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"=== TEST {i}: {test_case['name']} ===")
            print(f"이슈: {test_case['issue']}")
            print()
            
            # Enhanced 모드로 테스트
            start_time = time.time()
            
            report = llm.generate_comprehensive_issue_report(
                test_case["media"],
                test_case["reporter"],
                test_case["issue"],
                mode="enhanced"
            )
            
            processing_time = time.time() - start_time
            print(f"처리 완료: {processing_time:.2f}초")
            print()
            
            # 각 사례별 특화된 품질 분석
            if test_case["type"] == "business_inquiry":
                analysis_result = analyze_business_inquiry_quality(report, test_case)
            else:  # financial_results
                analysis_result = analyze_financial_results_quality(report, test_case)
            
            print(f"{test_case['name']} 품질 분석:")
            for metric, result in analysis_result.items():
                status = "통과" if result['passed'] else "미통과"
                print(f"  {status} {metric}: {result['score']}")
                if not result['passed']:
                    print(f"    개선필요: {result['improvement']}")
            
            # 종합 점수
            passed_count = sum(1 for r in analysis_result.values() if r['passed'])
            total_count = len(analysis_result)
            overall_score = (passed_count / total_count) * 100
            
            print(f"  종합 점수: {overall_score:.1f}/100")
            print()
            
            overall_results[test_case['name']] = {
                "processing_time": processing_time,
                "quality_score": overall_score,
                "analysis": analysis_result,
                "report": report
            }
        
        # 전체 결과 요약
        print("=== 종합 평가 결과 ===")
        total_score = sum(result['quality_score'] for result in overall_results.values()) / len(overall_results)
        avg_processing_time = sum(result['processing_time'] for result in overall_results.values()) / len(overall_results)
        
        print(f"평균 품질 점수: {total_score:.1f}/100")
        print(f"평균 처리 시간: {avg_processing_time:.2f}초")
        
        if total_score >= 85:
            print("평가: 우수 - 이상적 사례 수준 달성")
        elif total_score >= 70:
            print("평가: 양호 - 실용 수준 달성")
        elif total_score >= 50:
            print("평가: 보통 - 추가 개선 필요")
        else:
            print("평가: 개선 필요 - 상당한 품질 향상 필요")
        
        # 결과 저장
        save_comprehensive_result(overall_results, total_score, avg_processing_time)
        
        return True, overall_results
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None

def analyze_business_inquiry_quality(report, test_case):
    """식량사업 문의 품질 분석"""
    
    analysis = {}
    
    # 1. 구체성 (지역명, 수치)
    specific_terms = ["우크라이나", "호주", "미얀마", "수십만 톤", "곡물", "트레이더"]
    found_count = sum(1 for term in specific_terms if term in report)
    score = (found_count / len(specific_terms)) * 100
    
    analysis["구체성"] = {
        "passed": score >= 50,
        "score": f"{score:.1f}% ({found_count}/{len(specific_terms)} 용어)",
        "improvement": "구체적 지역명과 규모 정보 추가 필요" if score < 50 else ""
    }
    
    # 2. 담당자 정보
    has_contact = "소재바이오사업운영섹션" in report and "김준표" in report
    
    analysis["담당자_정보"] = {
        "passed": has_contact,
        "score": "구체적" if has_contact else "일반적",
        "improvement": "소재바이오사업운영섹션/김준표 리더 명시 필요" if not has_contact else ""
    }
    
    # 3. 위기단계 적정성
    proper_level = "1단계" in report and "관심" in report
    
    analysis["위기단계"] = {
        "passed": proper_level,
        "score": "적정" if proper_level else "부적정",
        "improvement": "문의성 이슈는 1단계(관심)으로 분류" if not proper_level else ""
    }
    
    # 4. 원보이스 실용성
    has_quote = '"' in report and len([m for m in report.split('"') if len(m) > 10 and len(m) < 100]) > 0
    
    analysis["원보이스_실용성"] = {
        "passed": has_quote,
        "score": "실용적" if has_quote else "추상적",
        "improvement": "인용 가능한 구체적 메시지 필요" if not has_quote else ""
    }
    
    return analysis

def analyze_financial_results_quality(report, test_case):
    """실적 문의 품질 분석"""
    
    analysis = {}
    
    # 1. 재무 수치 구체성
    financial_terms = ["8조", "3,137억", "905억", "1.7%", "10.3%", "52.3%"]
    found_count = sum(1 for term in financial_terms if term in report)
    score = (found_count / len(financial_terms)) * 100
    
    analysis["재무수치_구체성"] = {
        "passed": score >= 70,
        "score": f"{score:.1f}% ({found_count}/{len(financial_terms)} 수치)",
        "improvement": "구체적 매출/이익 수치와 증감률 필요" if score < 70 else ""
    }
    
    # 2. IR 담당자
    has_ir_contact = "IR그룹" in report and "유근석" in report
    
    analysis["IR_담당자"] = {
        "passed": has_ir_contact,
        "score": "정확함" if has_ir_contact else "부정확",
        "improvement": "IR그룹/유근석 리더 명시 필요" if not has_ir_contact else ""
    }
    
    # 3. 사업부문별 세분화
    segments = ["철강", "에너지", "식량"]
    found_segments = sum(1 for seg in segments if seg in report)
    
    analysis["사업부문_세분화"] = {
        "passed": found_segments >= 2,
        "score": f"{found_segments}/{len(segments)} 부문",
        "improvement": "주요 사업부문별 성과 구분 필요" if found_segments < 2 else ""
    }
    
    # 4. IR 전문용어
    ir_terms = ["연결기준", "영업이익", "전년동기대비", "재무성과", "주주가치"]
    found_ir_terms = sum(1 for term in ir_terms if term in report)
    
    analysis["IR_전문용어"] = {
        "passed": found_ir_terms >= 3,
        "score": f"{found_ir_terms}/{len(ir_terms)} 용어",
        "improvement": "IR 전문 용어 적극 활용 필요" if found_ir_terms < 3 else ""
    }
    
    # 5. 투명성 (부정적 실적 객관적 제시)
    has_transparency = "감소" in report or "하락" in report or "부진" in report
    
    analysis["투명성"] = {
        "passed": has_transparency,
        "score": "객관적" if has_transparency else "편향적",
        "improvement": "부정적 실적도 객관적으로 제시" if not has_transparency else ""
    }
    
    return analysis

def save_comprehensive_result(results, total_score, avg_time):
    """종합 벤치마킹 결과 저장"""
    timestamp = datetime.now().strftime('%H%M%S')
    filename = f"comprehensive_benchmark_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=== 종합 벤치마킹 테스트 결과 ===\n")
        f.write(f"테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"평균 품질 점수: {total_score:.1f}/100\n")
        f.write(f"평균 처리 시간: {avg_time:.2f}초\n\n")
        
        for case_name, result in results.items():
            f.write(f"\n{'='*50}\n")
            f.write(f"{case_name.upper()}\n")
            f.write(f"{'='*50}\n")
            f.write(f"처리 시간: {result['processing_time']:.2f}초\n")
            f.write(f"품질 점수: {result['quality_score']:.1f}/100\n\n")
            
            f.write("세부 분석:\n")
            for metric, analysis in result['analysis'].items():
                status = "통과" if analysis['passed'] else "미통과"
                f.write(f"  {metric}: {status} - {analysis['score']}\n")
                if not analysis['passed']:
                    f.write(f"    개선필요: {analysis['improvement']}\n")
            
            f.write(f"\n생성된 보고서:\n")
            f.write("-" * 30 + "\n")
            f.write(result['report'])
            f.write("\n\n")
    
    print(f"SAVE: 종합 벤치마킹 결과 저장 {filename}")

def main():
    """메인 테스트 실행"""
    success, results = run_comprehensive_benchmark()
    
    if success and results:
        print("\n=== 최종 개선 권장사항 ===")
        
        all_improvements = []
        for case_name, result in results.items():
            for metric, analysis in result['analysis'].items():
                if not analysis['passed'] and analysis['improvement']:
                    all_improvements.append(f"{case_name} - {metric}: {analysis['improvement']}")
        
        if all_improvements:
            print("우선 개선 항목:")
            for improvement in all_improvements[:5]:
                print(f"  - {improvement}")
        else:
            print("모든 테스트 케이스가 기준을 충족합니다!")
            print("시스템이 이상적 사례 수준에 도달했습니다.")
        
        return True
    else:
        print("종합 벤치마킹 테스트 실패")
        return False

if __name__ == "__main__":
    main()