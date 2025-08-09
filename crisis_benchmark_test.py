#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3단계 위기 사안 벤치마킹 테스트
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_crisis_benchmark_test():
    """위기 사안 벤치마킹 테스트"""
    
    print("=== 3단계 위기 사안 벤치마킹 테스트 ===")
    print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from data_based_llm import DataBasedLLM
        
        # 세 번째 이상적 사례 테스트
        crisis_case = {
            "media": "동아일보",
            "reporter": "김동아",
            "issue": "미얀마 가스전 실적 개선 배경, 4단계 개발 진척, 군부 관계, 영업이익 지원금 의혹 해명 요구"
        }
        
        llm = DataBasedLLM()
        print("SUCCESS: 통합 위기 대응 시스템 초기화 완료")
        print(f"테스트 이슈: {crisis_case['issue']}")
        print()
        
        # Enhanced 모드로 테스트 (위기 대응 특화 포함)
        print("START: 3단계 위기 사안 처리...")
        start_time = time.time()
        
        report = llm.generate_comprehensive_issue_report(
            crisis_case["media"],
            crisis_case["reporter"],
            crisis_case["issue"]
        )
        
        processing_time = time.time() - start_time
        print(f"처리 완료: {processing_time:.2f}초")
        print()
        
        # 위기 사안 특화 품질 분석
        analysis_result = analyze_crisis_report_quality(report, crisis_case)
        
        print("=== 위기 사안 품질 분석 결과 ===")
        for metric, result in analysis_result.items():
            status = "통과" if result['passed'] else "미통과"
            print(f"{status} {metric}: {result['score']}")
            if not result['passed']:
                print(f"    개선필요: {result['improvement']}")
        
        # 종합 점수 계산
        passed_count = sum(1 for result in analysis_result.values() if result['passed'])
        total_metrics = len(analysis_result)
        overall_score = (passed_count / total_metrics) * 100
        
        print(f"\n종합 점수: {overall_score:.1f}/100")
        
        if overall_score >= 90:
            evaluation = "S급 - 이상적 사례 수준"
        elif overall_score >= 80:
            evaluation = "A급 - 우수"
        elif overall_score >= 70:
            evaluation = "B급 - 양호"
        else:
            evaluation = "C급 - 개선 필요"
        
        print(f"평가: {evaluation}")
        
        # 결과 저장
        save_crisis_benchmark_result(report, analysis_result, overall_score, processing_time, evaluation)
        
        return True, analysis_result, overall_score, report
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None, 0, None

def analyze_crisis_report_quality(report, test_case):
    """위기 사안 보고서 품질 분석"""
    
    analysis = {}
    
    # 1. 위기단계 정확성
    proper_crisis_level = "3단계" in report and ("위기" in report or "대응" in report)
    
    analysis["위기단계_정확성"] = {
        "passed": proper_crisis_level,
        "score": "정확함" if proper_crisis_level else "부정확",
        "improvement": "3단계(위기) 분류 필요" if not proper_crisis_level else ""
    }
    
    # 2. 다부서 협업 체계
    has_multi_department = ("가스사업운영섹션" in report and "대외협력그룹" in report) or \
                          ("법무" in report and "ESG" in report)
    
    analysis["다부서_협업"] = {
        "passed": has_multi_department,
        "score": "구축됨" if has_multi_department else "미흡",
        "improvement": "법무+ESG+대외협력 다부서 협업 체계 구축" if not has_multi_department else ""
    }
    
    # 3. 전문용어 활용
    professional_terms = ["PSC", "UJV", "EPC", "MOGE", "OFAC", "HRDD"]
    found_terms = sum(1 for term in professional_terms if term in report)
    prof_score = (found_terms / len(professional_terms)) * 100
    
    analysis["전문용어_활용"] = {
        "passed": found_terms >= 3,
        "score": f"{found_terms}/{len(professional_terms)} 용어 ({prof_score:.1f}%)",
        "improvement": "PSC, UJV, EPC 등 에너지 전문용어 활용 필요" if found_terms < 3 else ""
    }
    
    # 4. 법적 방어 논리
    has_legal_defense = any(term in report for term in ["제재 준수", "내부 통제", "컴플라이언스", "법령"])
    
    analysis["법적_방어논리"] = {
        "passed": has_legal_defense,
        "score": "구축됨" if has_legal_defense else "미흡",
        "improvement": "제재 준수, 내부 통제 강화 등 법적 방어논리 필요" if not has_legal_defense else ""
    }
    
    # 5. 연락처 구체성
    has_specific_contacts = "02-" in report and "010-" in report
    
    analysis["연락처_구체성"] = {
        "passed": has_specific_contacts,
        "score": "완전함" if has_specific_contacts else "일반적",
        "improvement": "직통 전화번호 포함된 완전한 연락처 필요" if not has_specific_contacts else ""
    }
    
    # 6. 원보이스 체계성
    has_systematic_message = report.count('"') >= 2 and len(report.split('"')[1]) > 100
    
    analysis["원보이스_체계성"] = {
        "passed": has_systematic_message,
        "score": "체계적" if has_systematic_message else "단순함",
        "improvement": "4단계 논리 구성의 체계적 원보이스 필요" if not has_systematic_message else ""
    }
    
    # 7. Q&A 브릿지
    has_qa_bridge = "Q&A" in report or "브릿지" in report
    
    analysis["QA_브릿지"] = {
        "passed": has_qa_bridge,
        "score": "있음" if has_qa_bridge else "없음",
        "improvement": "예상 추가 질문에 대한 Q&A 브릿지 필요" if not has_qa_bridge else ""
    }
    
    # 8. 보고라인 명시
    has_reporting_line = "대표이사" in report or "홀딩스" in report or "보고" in report
    
    analysis["보고라인_명시"] = {
        "passed": has_reporting_line,
        "score": "명시됨" if has_reporting_line else "미명시",
        "improvement": "대표이사/홀딩스 보고라인 명시 필요" if not has_reporting_line else ""
    }
    
    return analysis

def save_crisis_benchmark_result(report, analysis, score, time, evaluation):
    """위기 벤치마킹 결과 저장"""
    timestamp = datetime.now().strftime('%H%M%S')
    filename = f"crisis_benchmark_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=== 3단계 위기 사안 벤치마킹 결과 ===\n")
        f.write(f"테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"처리 시간: {time:.2f}초\n")
        f.write(f"종합 점수: {score:.1f}/100\n")
        f.write(f"평가 등급: {evaluation}\n\n")
        
        f.write("세부 분석 결과:\n")
        f.write("="*50 + "\n")
        
        for metric, result in analysis.items():
            status = "통과" if result['passed'] else "미통과"
            f.write(f"{metric}: {status} - {result['score']}\n")
            if not result['passed']:
                f.write(f"  개선필요: {result['improvement']}\n")
        
        f.write("\n" + "="*50 + "\n")
        f.write("생성된 위기 대응 보고서:\n")
        f.write("="*50 + "\n\n")
        f.write(report)
    
    print(f"SAVE: 위기 벤치마킹 결과 저장 {filename}")

def main():
    """메인 테스트 실행"""
    success, analysis, score, report = run_crisis_benchmark_test()
    
    if success and analysis:
        print("\n=== 위기 대응 시스템 평가 ===")
        
        # 개선이 필요한 항목들
        improvement_needed = []
        for metric, result in analysis.items():
            if not result['passed'] and result['improvement']:
                improvement_needed.append(f"{metric}: {result['improvement']}")
        
        if improvement_needed:
            print("우선 개선 필요 항목:")
            for improvement in improvement_needed:
                print(f"  - {improvement}")
        else:
            print("모든 위기 대응 기준을 충족합니다!")
            print("3단계 위기 사안 대응 시스템이 완성되었습니다.")
        
        print(f"\n최종 평가: 3단계 위기 사안 대응 역량 {score:.1f}점")
        
        return True
    else:
        print("위기 벤치마킹 테스트 실패")
        return False

if __name__ == "__main__":
    main()