#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
가상 위기 사안 3차 테스트 - 시스템 일관성 검증
"""

import sys
import os
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_virtual_crisis_scenarios():
    """가상의 3단계 위기 사안들"""
    
    virtual_scenarios = [
        {
            "name": "러시아_제재_위반_의혹",
            "media": "한겨레",
            "reporter": "박한겨례",
            "issue": "포스코인터내셔널이 러시아 제재 대상 기업과 우회 거래를 통해 원자재를 수입했다는 의혹 제기. 관련 금융거래 내역과 제재 위반 가능성에 대한 명확한 해명 요구",
            "expected_level": 3,
            "risk_factors": ["정치적_민감성", "법적_위험", "국제적_파급"]
        },
        
        {
            "name": "인도네시아_환경파괴_논란",
            "media": "경향신문",
            "reporter": "이경향",
            "issue": "인도네시아 광산 개발 과정에서 열대우림 파괴와 원주민 거주지역 침해 논란. 환경단체의 국제소송 예고와 ESG 경영 실태에 대한 의혹 제기",
            "expected_level": 3,
            "risk_factors": ["ESG_리스크", "법적_위험", "국제적_파급"]
        },
        
        {
            "name": "북한_석탄_밀수_의혹",
            "media": "조선일보",
            "reporter": "김조선",
            "issue": "포스코인터내셔널 계열사가 북한산 석탄을 제3국을 통해 우회 수입했다는 첩보기관 정보 노출. UN 대북제재 위반 가능성과 정부 수사 착수 여부",
            "expected_level": 4,
            "risk_factors": ["정치적_민감성", "법적_위험", "국제적_파급", "높은_미디어관심"]
        }
    ]
    
    return virtual_scenarios

def run_virtual_crisis_tests():
    """가상 위기 사안 연속 테스트"""
    
    print("=== 가상 위기 사안 3차 테스트 - 시스템 일관성 검증 ===")
    print(f"테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        from data_based_llm import DataBasedLLM
        
        scenarios = create_virtual_crisis_scenarios()
        llm = DataBasedLLM()
        
        print("SUCCESS: 위기 대응 시스템 초기화 완료")
        print(f"테스트 시나리오: {len(scenarios)}개")
        print()
        
        test_results = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"=== 테스트 {i}/3: {scenario['name']} ===")
            print(f"언론사: {scenario['media']} {scenario['reporter']}")
            print(f"이슈: {scenario['issue'][:60]}...")
            print()
            
            # 처리 시간 측정
            start_time = time.time()
            
            report = llm.generate_comprehensive_issue_report(
                scenario["media"],
                scenario["reporter"],
                scenario["issue"]
            )
            
            processing_time = time.time() - start_time
            print(f"처리 완료: {processing_time:.2f}초")
            
            # 품질 분석
            quality_analysis = analyze_virtual_crisis_quality(report, scenario)
            
            # 결과 출력
            print("품질 분석 결과:")
            passed_count = 0
            for metric, result in quality_analysis.items():
                status = "통과" if result['passed'] else "미통과"
                print(f"  {status} {metric}: {result['score']}")
                if result['passed']:
                    passed_count += 1
            
            overall_score = (passed_count / len(quality_analysis)) * 100
            print(f"종합 점수: {overall_score:.1f}/100")
            
            if overall_score >= 85:
                grade = "A급"
            elif overall_score >= 75:
                grade = "B급"
            else:
                grade = "C급"
            
            print(f"등급: {grade}")
            print()
            
            test_results.append({
                "name": scenario["name"],
                "processing_time": processing_time,
                "quality_score": overall_score,
                "grade": grade,
                "analysis": quality_analysis,
                "report": report
            })
        
        # 전체 결과 분석
        avg_score = sum(result['quality_score'] for result in test_results) / len(test_results)
        avg_time = sum(result['processing_time'] for result in test_results) / len(test_results)
        
        print("=== 종합 결과 분석 ===")
        print(f"평균 품질 점수: {avg_score:.1f}/100")
        print(f"평균 처리 시간: {avg_time:.2f}초")
        
        # 일관성 분석
        score_variance = max(result['quality_score'] for result in test_results) - min(result['quality_score'] for result in test_results)
        print(f"점수 편차: {score_variance:.1f}점")
        
        if score_variance <= 10:
            consistency = "매우 높음"
        elif score_variance <= 20:
            consistency = "높음"
        else:
            consistency = "보통"
        
        print(f"품질 일관성: {consistency}")
        
        # 최종 평가
        if avg_score >= 85 and consistency in ["매우 높음", "높음"]:
            final_evaluation = "시스템 완성도 S급 - 실전 투입 가능"
        elif avg_score >= 75:
            final_evaluation = "시스템 완성도 A급 - 안정적 운영 가능"
        else:
            final_evaluation = "추가 개선 필요"
        
        print(f"최종 평가: {final_evaluation}")
        
        # 결과 저장
        save_virtual_test_results(test_results, avg_score, avg_time, consistency, final_evaluation)
        
        return True, test_results, final_evaluation
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, None, None

def analyze_virtual_crisis_quality(report, scenario):
    """가상 위기 사안 품질 분석"""
    
    analysis = {}
    
    # 1. 위기단계 적정성
    expected_level = scenario["expected_level"]
    has_proper_level = f"{expected_level}단계" in report
    
    analysis["위기단계_적정성"] = {
        "passed": has_proper_level,
        "score": f"{expected_level}단계 분류" if has_proper_level else "부적정",
        "improvement": f"{expected_level}단계 위기 분류 필요" if not has_proper_level else ""
    }
    
    # 2. 위험요소 대응
    risk_factors = scenario["risk_factors"]
    addressed_risks = 0
    
    if "정치적_민감성" in risk_factors:
        if any(term in report for term in ["제재", "정치", "국제"]):
            addressed_risks += 1
    
    if "법적_위험" in risk_factors:
        if any(term in report for term in ["법령", "준수", "컴플라이언스"]):
            addressed_risks += 1
    
    if "ESG_리스크" in risk_factors:
        if any(term in report for term in ["ESG", "환경", "인권", "지속가능"]):
            addressed_risks += 1
    
    risk_coverage = (addressed_risks / len(risk_factors)) * 100
    
    analysis["위험요소_대응"] = {
        "passed": risk_coverage >= 60,
        "score": f"{addressed_risks}/{len(risk_factors)} 요소 ({risk_coverage:.1f}%)",
        "improvement": "주요 위험요소별 맞춤 대응 필요" if risk_coverage < 60 else ""
    }
    
    # 3. 전문성
    professional_indicators = ["당사", "관련", "법령", "국제", "제재", "준수", "통제"]
    found_indicators = sum(1 for indicator in professional_indicators if indicator in report)
    prof_score = (found_indicators / len(professional_indicators)) * 100
    
    analysis["전문성"] = {
        "passed": prof_score >= 70,
        "score": f"{prof_score:.1f}%",
        "improvement": "전문용어 및 법무 표현 강화 필요" if prof_score < 70 else ""
    }
    
    # 4. 대응 체계
    has_systematic_response = any(term in report for term in ["법무", "ESG", "대외협력", "다부서", "협의"])
    
    analysis["대응_체계"] = {
        "passed": has_systematic_response,
        "score": "체계적" if has_systematic_response else "일반적",
        "improvement": "다부서 협업 대응 체계 구축 필요" if not has_systematic_response else ""
    }
    
    # 5. 메시지 품질
    has_quality_message = '"' in report and len(report) > 800
    
    analysis["메시지_품질"] = {
        "passed": has_quality_message,
        "score": "우수" if has_quality_message else "보통",
        "improvement": "체계적이고 완성도 높은 원보이스 필요" if not has_quality_message else ""
    }
    
    # 6. 보고서 완성도
    required_sections = ["발생 일시", "대응 단계", "발생 내용", "유관 의견", "대응 방안", "대응 결과"]
    found_sections = sum(1 for section in required_sections if section in report)
    completeness = (found_sections / len(required_sections)) * 100
    
    analysis["보고서_완성도"] = {
        "passed": completeness >= 85,
        "score": f"{completeness:.1f}%",
        "improvement": "필수 섹션 완성도 향상 필요" if completeness < 85 else ""
    }
    
    return analysis

def save_virtual_test_results(results, avg_score, avg_time, consistency, evaluation):
    """가상 테스트 결과 저장"""
    timestamp = datetime.now().strftime('%H%M%S')
    filename = f"virtual_crisis_test_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=== 가상 위기 사안 3차 테스트 결과 ===\n")
        f.write(f"테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"평균 품질 점수: {avg_score:.1f}/100\n")
        f.write(f"평균 처리 시간: {avg_time:.2f}초\n")
        f.write(f"품질 일관성: {consistency}\n")
        f.write(f"최종 평가: {evaluation}\n\n")
        
        for result in results:
            f.write(f"\n{'='*60}\n")
            f.write(f"{result['name'].upper()}\n")
            f.write(f"{'='*60}\n")
            f.write(f"처리 시간: {result['processing_time']:.2f}초\n")
            f.write(f"품질 점수: {result['quality_score']:.1f}/100\n")
            f.write(f"등급: {result['grade']}\n\n")
            
            f.write("세부 분석:\n")
            for metric, analysis in result['analysis'].items():
                status = "통과" if analysis['passed'] else "미통과"
                f.write(f"  {metric}: {status} - {analysis['score']}\n")
            
            f.write(f"\n생성된 보고서:\n")
            f.write("-" * 40 + "\n")
            f.write(result['report'])
            f.write("\n\n")
    
    print(f"SAVE: 가상 테스트 결과 저장 {filename}")

def main():
    """메인 테스트 실행"""
    success, results, evaluation = run_virtual_crisis_tests()
    
    if success and results:
        print(f"\n=== 시스템 검증 완료 ===")
        print("3개의 서로 다른 위기 시나리오 테스트 완료")
        print(f"최종 판정: {evaluation}")
        
        # 개별 결과 요약
        print(f"\n개별 테스트 결과:")
        for result in results:
            print(f"  {result['name']}: {result['quality_score']:.1f}점 ({result['grade']})")
        
        return True
    else:
        print("가상 위기 테스트 실패")
        return False

if __name__ == "__main__":
    main()