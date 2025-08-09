#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
현재 시스템 vs 이상적 사례 벤치마킹 테스트
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_benchmark_test():
    """벤치마킹 테스트 실행"""
    
    print("=== 현재 시스템 vs 이상적 사례 벤치마킹 테스트 ===")
    print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from data_based_llm import DataBasedLLM
        
        # 이상적 사례와 동일한 테스트 케이스
        benchmark_case = {
            "media": "조선일보",
            "reporter": "김조선",
            "issue": "포스코인터내셔널 식량사업 생산지, 주요 납품처, 올해 매출 계획 관련 문의"
        }
        
        llm = DataBasedLLM()
        print("SUCCESS: DataBasedLLM 초기화 완료")
        print(f"테스트 이슈: {benchmark_case['issue']}")
        print()
        
        # Enhanced 모드로 테스트
        print("START: 벤치마킹 테스트 (Enhanced 모드)...")
        start_time = time.time()
        
        current_report = llm.generate_comprehensive_issue_report(
            benchmark_case["media"],
            benchmark_case["reporter"],
            benchmark_case["issue"],
            mode="enhanced"
        )
        
        processing_time = time.time() - start_time
        print(f"SUCCESS: 처리 완료 ({processing_time:.2f}초)")
        print()
        
        # 이상적 사례와 비교 분석
        comparison_result = compare_with_ideal(current_report)
        
        print("=== 벤치마킹 결과 ===")
        for category, analysis in comparison_result.items():
            print(f"\n[{category}]")
            for metric, result in analysis.items():
                status = "O" if result['passed'] else "X"
                print(f"  {status} {metric}: {result['score']}")
                if not result['passed']:
                    print(f"    문제점: {result['issue']}")
                    print(f"    개선방향: {result['improvement']}")
        
        # 종합 점수 계산
        total_score = calculate_overall_score(comparison_result)
        print(f"\n=== 종합 평가 ===")
        print(f"전체 점수: {total_score:.1f}/100")
        
        if total_score >= 80:
            print("평가: 우수 - 이상적 사례와 유사한 수준")
        elif total_score >= 60:
            print("평가: 양호 - 일부 개선 필요")
        else:
            print("평가: 개선 필요 - 상당한 품질 향상 필요")
        
        # 결과 저장
        save_benchmark_result(current_report, comparison_result, total_score, processing_time)
        
        return True, comparison_result, current_report
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None, None

def compare_with_ideal(current_report):
    """현재 보고서와 이상적 사례 비교"""
    
    comparison_result = {
        "구조적_품질": {
            "템플릿_준수": analyze_template_compliance(current_report),
            "일시_형식": analyze_date_format(current_report),
            "위기단계_적정성": analyze_crisis_level(current_report)
        },
        
        "내용적_품질": {
            "구체성": analyze_specificity(current_report),
            "담당자_명시": analyze_contact_info(current_report),
            "사실확인_품질": analyze_fact_verification(current_report)
        },
        
        "커뮤니케이션_품질": {
            "원보이스_실용성": analyze_message_usability(current_report),
            "설명논리_구조": analyze_explanation_logic(current_report),
            "전문성": analyze_professionalism(current_report)
        }
    }
    
    return comparison_result

def analyze_template_compliance(report):
    """템플릿 준수도 분석"""
    required_sections = [
        "1. 발생 일시:",
        "2. 발생 단계:" if "2. 발생 단계:" in report else "2. 대응 단계:",
        "3. 발생 내용:",
        "4. 유관 의견:",
        "5. 대응 방안:",
        "6. 대응 결과:"
    ]
    
    found_count = sum(1 for section in required_sections if section in report)
    score = (found_count / len(required_sections)) * 100
    
    return {
        "passed": score >= 85,
        "score": f"{score:.1f}%",
        "issue": "일부 섹션 누락" if score < 85 else "",
        "improvement": "모든 필수 섹션 포함 필요" if score < 85 else ""
    }

def analyze_date_format(report):
    """일시 형식 분석"""
    # 이상적: "2025. 08. 09. 10:30"
    # 현재 시스템: "2025년 8월 9일 15시 8분"
    
    ideal_format = "." in report and "년" not in report and "시" not in report
    
    return {
        "passed": ideal_format,
        "score": "적합" if ideal_format else "부적합",
        "issue": "날짜 형식이 장황함" if not ideal_format else "",
        "improvement": "'2025. 08. 09. 10:30' 형식으로 간소화" if not ideal_format else ""
    }

def analyze_crisis_level(report):
    """위기단계 적정성 분석"""
    # 단순 문의사항은 1단계(관심)이 적정
    has_proper_level = "1단계" in report and "관심" in report
    
    return {
        "passed": has_proper_level,
        "score": "적정" if has_proper_level else "부적정",
        "issue": "단순 문의를 과도한 위기단계로 분류" if not has_proper_level else "",
        "improvement": "문의성 이슈는 1단계(관심)로 분류" if not has_proper_level else ""
    }

def analyze_specificity(report):
    """구체성 분석"""
    # 구체적 지역명, 수치, 업계 용어 포함 여부
    specific_terms = ["우크라이나", "호주", "미얀마", "수십만 톤", "곡물", "트레이더"]
    found_terms = [term for term in specific_terms if term in report]
    
    score = (len(found_terms) / len(specific_terms)) * 100
    
    return {
        "passed": score >= 30,  # 최소 30% 이상
        "score": f"{score:.1f}% ({len(found_terms)}/{len(specific_terms)} 용어)",
        "issue": "일반적 표현 위주, 구체적 정보 부족" if score < 30 else "",
        "improvement": "구체적 지역명, 수치, 업계 용어 포함 필요" if score < 30 else ""
    }

def analyze_contact_info(report):
    """담당자 정보 분석"""
    # 구체적 부서/담당자 표기 여부
    has_specific_contact = "/" in report and ("팀" in report or "섹션" in report or "리더" in report)
    
    return {
        "passed": has_specific_contact,
        "score": "구체적" if has_specific_contact else "일반적",
        "issue": "일반적 부서명만 언급, 담당자 정보 없음" if not has_specific_contact else "",
        "improvement": "'부서명/담당자명' 형식으로 구체화" if not has_specific_contact else ""
    }

def analyze_fact_verification(report):
    """사실확인 품질 분석"""
    fact_section = report[report.find("사실 확인:"):report.find("설명 논리:")] if "사실 확인:" in report else ""
    
    # 구체적 사업 정보 포함 여부
    has_business_details = len(fact_section) > 100 and ("사업" in fact_section or "운영" in fact_section)
    
    return {
        "passed": has_business_details,
        "score": "상세함" if has_business_details else "일반적",
        "issue": "사실확인이 피상적이고 일반적" if not has_business_details else "",
        "improvement": "구체적 사업 구조와 운영 방식 포함" if not has_business_details else ""
    }

def analyze_message_usability(report):
    """원보이스 실용성 분석"""
    # 인용 가능한 구체적 메시지 포함 여부
    has_quotable_message = '"' in report or "'" in report
    message_length = 0
    
    if has_quotable_message:
        # 인용문 길이 확인
        if '"' in report:
            quotes = report.split('"')
            if len(quotes) >= 3:
                message_length = len(quotes[1])
    
    is_usable = has_quotable_message and 20 <= message_length <= 100
    
    return {
        "passed": is_usable,
        "score": f"실용적({message_length}자)" if is_usable else "추상적",
        "issue": "인용하기 어려운 추상적 메시지" if not is_usable else "",
        "improvement": "20-100자 길이의 구체적 인용문 제공" if not is_usable else ""
    }

def analyze_explanation_logic(report):
    """설명논리 구조 분석"""
    has_positive_frame = "기여" in report or "안정" in report or "성장" in report
    has_limitation_explanation = "비공개" in report or "제한" in report or "한계" in report
    
    good_structure = has_positive_frame and has_limitation_explanation
    
    return {
        "passed": good_structure,
        "score": "균형적" if good_structure else "일반적",
        "issue": "긍정적 프레임과 제한사항 설명의 균형 부족" if not good_structure else "",
        "improvement": "긍정적 가치 제시 + 합리적 제한 설명" if not good_structure else ""
    }

def analyze_professionalism(report):
    """전문성 분석"""
    professional_terms = ["사업부", "운영", "공급망", "거점", "협력사", "트레이더", "매출"]
    found_terms = [term for term in professional_terms if term in report]
    
    score = (len(found_terms) / len(professional_terms)) * 100
    
    return {
        "passed": score >= 50,
        "score": f"{score:.1f}%",
        "issue": "업계 전문 용어 사용 부족" if score < 50 else "",
        "improvement": "해당 업계의 전문 용어 적극 활용" if score < 50 else ""
    }

def calculate_overall_score(comparison_result):
    """종합 점수 계산"""
    total_score = 0
    total_items = 0
    
    for category, metrics in comparison_result.items():
        for metric, result in metrics.items():
            total_items += 1
            if result['passed']:
                if metric == "구체성" or metric == "전문성":
                    # 백분율 점수는 직접 사용
                    score_text = result['score'].split('%')[0].split('(')[0]
                    total_score += float(score_text)
                else:
                    # 통과/실패는 100/0으로 계산
                    total_score += 100
            else:
                if metric == "구체성" or metric == "전문성":
                    score_text = result['score'].split('%')[0].split('(')[0]
                    total_score += float(score_text)
                # 실패는 0점
    
    return total_score / total_items if total_items > 0 else 0

def save_benchmark_result(report, comparison, score, processing_time):
    """벤치마킹 결과 저장"""
    timestamp = datetime.now().strftime('%H%M%S')
    filename = f"benchmark_result_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=== 벤치마킹 테스트 결과 ===\n")
        f.write(f"테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"처리 시간: {processing_time:.2f}초\n")
        f.write(f"종합 점수: {score:.1f}/100\n\n")
        
        f.write("상세 분석 결과:\n")
        f.write("="*50 + "\n")
        
        for category, metrics in comparison.items():
            f.write(f"\n[{category}]\n")
            for metric, result in metrics.items():
                status = "통과" if result['passed'] else "미통과"
                f.write(f"  {metric}: {status} - {result['score']}\n")
                if not result['passed']:
                    f.write(f"    문제점: {result['issue']}\n")
                    f.write(f"    개선방향: {result['improvement']}\n")
        
        f.write("\n" + "="*50 + "\n")
        f.write("생성된 보고서:\n")
        f.write("="*50 + "\n\n")
        f.write(report)
    
    print(f"SAVE: 벤치마킹 결과 저장 {filename}")

def main():
    """메인 테스트 실행"""
    success, comparison, report = run_benchmark_test()
    
    if success:
        print("\n=== 주요 개선 포인트 ===")
        improvement_points = []
        
        for category, metrics in comparison.items():
            for metric, result in metrics.items():
                if not result['passed'] and result['improvement']:
                    improvement_points.append(f"{metric}: {result['improvement']}")
        
        if improvement_points:
            print("우선 개선이 필요한 항목:")
            for point in improvement_points[:5]:  # 상위 5개만 표시
                print(f"  - {point}")
        else:
            print("모든 항목이 기준을 충족합니다.")
        
        return True
    else:
        print("벤치마킹 테스트 실패")
        return False

if __name__ == "__main__":
    main()