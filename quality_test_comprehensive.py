#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
답변 퀄리티 종합 테스트 및 평가 시스템
"""

import sys
import os
from datetime import datetime
import time
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class QualityAssessment:
    """답변 퀄리티 평가 시스템"""
    
    def __init__(self):
        self.test_cases = [
            {
                "id": "case_1_routine",
                "name": "일반적인 제품 이슈",
                "media": "조선일보",
                "reporter": "김기자",
                "issue": "포스코인터내셔널 철강제품에서 품질 불량이 발견되어 납품 지연이 우려된다는 보도",
                "expected_crisis_level": "2단계(주의)",
                "expected_departments": ["품질보증팀", "철강사업부"],
                "complexity": "중간"
            },
            {
                "id": "case_2_crisis",
                "name": "위기 상황",
                "media": "매일경제",
                "reporter": "이기자",
                "issue": "포스코인터내셔널 해외 광산에서 대규모 환경오염 사고 발생, 현지 정부가 사업 중단 명령 검토",
                "expected_crisis_level": "3단계(위기)",
                "expected_departments": ["자원개발사업부", "ESG경영실", "법무팀"],
                "complexity": "높음"
            },
            {
                "id": "case_3_financial",
                "name": "재무/투자 관련",
                "media": "한국경제",
                "reporter": "박기자",
                "issue": "포스코인터내셔널 3분기 실적 급락, 주가 10% 하락에 투자자들 우려 확산",
                "expected_crisis_level": "2단계(주의)",
                "expected_departments": ["경영기획팀", "재무팀", "IR팀"],
                "complexity": "중간"
            },
            {
                "id": "case_4_complex",
                "name": "복합 이슈",
                "media": "연합뉴스",
                "reporter": "최기자",
                "issue": "포스코인터내셔널 인도네시아 니켈 광산 개발 프로젝트에서 환경문제와 현지 주민 갈등이 동시 발생, ESG 경영 논란 확산",
                "expected_crisis_level": "3단계(위기)",
                "expected_departments": ["자원개발사업부", "ESG경영실", "대외협력팀"],
                "complexity": "매우 높음"
            }
        ]
        
        self.evaluation_criteria = {
            "completeness": {  # 완성도
                "template_compliance": 0,      # 템플릿 준수도
                "required_sections": 0,        # 필수 섹션 포함
                "factual_accuracy": 0          # 사실 정확성
            },
            "quality": {  # 품질
                "crisis_level_accuracy": 0,    # 위기단계 정확성
                "department_relevance": 0,     # 부서 연관성
                "response_appropriateness": 0  # 대응방안 적절성
            },
            "process": {  # 프로세스
                "processing_time": 0,          # 처리 시간
                "error_handling": 0,           # 오류 처리
                "consistency": 0               # 일관성
            }
        }

    def run_comprehensive_test(self):
        """종합 테스트 실행"""
        print("=" * 80)
        print("포스코인터내셔널 언론대응 AI 시스템 - 답변 퀄리티 종합 평가")
        print("=" * 80)
        
        try:
            from data_based_llm import DataBasedLLM
            llm = DataBasedLLM()
            print("SUCCESS: DataBasedLLM 초기화 완료")
            
            test_results = []
            
            for i, test_case in enumerate(self.test_cases, 1):
                print(f"\n{'='*60}")
                print(f"테스트 케이스 {i}: {test_case['name']} (복잡도: {test_case['complexity']})")
                print(f"{'='*60}")
                
                result = self._execute_single_test(llm, test_case)
                test_results.append(result)
                
                # 중간 결과 출력
                print(f"처리 시간: {result['processing_time']:.2f}초")
                print(f"템플릿 준수도: {result['template_compliance']:.1f}%")
                print(f"위기단계 정확도: {result['crisis_accuracy']:.1f}%")
                
            # 종합 평가
            overall_assessment = self._comprehensive_analysis(test_results)
            
            # 결과 저장
            self._save_results(test_results, overall_assessment)
            
            return test_results, overall_assessment
            
        except Exception as e:
            print(f"ERROR: 테스트 실행 실패 - {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None

    def _execute_single_test(self, llm, test_case):
        """단일 테스트 케이스 실행"""
        start_time = time.time()
        
        try:
            # 8단계 프로세스 실행
            report = llm.generate_comprehensive_issue_report(
                test_case["media"],
                test_case["reporter"],
                test_case["issue"]
            )
            
            processing_time = time.time() - start_time
            
            # 결과 분석
            analysis = self._analyze_report_quality(report, test_case)
            analysis.update({
                "test_case": test_case,
                "processing_time": processing_time,
                "report_content": report,
                "success": True
            })
            
            return analysis
            
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "test_case": test_case,
                "processing_time": processing_time,
                "success": False,
                "error": str(e),
                "template_compliance": 0,
                "crisis_accuracy": 0,
                "department_relevance": 0
            }

    def _analyze_report_quality(self, report, test_case):
        """보고서 품질 분석"""
        analysis = {}
        
        # 1. 템플릿 준수도 검사
        required_sections = [
            "<이슈 발생 보고>",
            "1. 발생 일시:",
            "2. 발생 단계:",
            "3. 발생 내용:",
            "4. 유관 의견:",
            "5. 대응 방안:",
            "6. 대응 결과:"
        ]
        
        found_sections = sum(1 for section in required_sections if section in report)
        analysis["template_compliance"] = (found_sections / len(required_sections)) * 100
        
        # 2. 위기단계 정확도
        expected_level = test_case["expected_crisis_level"]
        if expected_level in report:
            analysis["crisis_accuracy"] = 100
        elif any(level in report for level in ["1단계", "2단계", "3단계", "4단계"]):
            analysis["crisis_accuracy"] = 50  # 다른 단계지만 분류는 함
        else:
            analysis["crisis_accuracy"] = 0
        
        # 3. 부서 연관성
        expected_depts = test_case["expected_departments"]
        found_depts = sum(1 for dept in expected_depts if dept in report)
        analysis["department_relevance"] = (found_depts / len(expected_depts)) * 100 if expected_depts else 100
        
        # 4. 보고서 길이 및 구조적 완성도
        analysis["report_length"] = len(report)
        analysis["structural_completeness"] = self._assess_structural_quality(report)
        
        # 5. 핵심 키워드 포함 여부
        key_terms = ["포스코인터내셔널", "대응방안", "사실확인", "원보이스"]
        found_terms = sum(1 for term in key_terms if term in report)
        analysis["keyword_coverage"] = (found_terms / len(key_terms)) * 100
        
        return analysis

    def _assess_structural_quality(self, report):
        """구조적 품질 평가"""
        quality_indicators = [
            "발생 일시:" in report and "2025년" in report,  # 시간 정보
            "단계:" in report,  # 위기단계 정보
            "사실 확인:" in report,  # 사실확인 섹션
            "원보이스:" in report,  # 대응 메시지
            len(report) > 500,  # 최소 길이
            "참조." in report   # 참조 섹션
        ]
        
        return (sum(quality_indicators) / len(quality_indicators)) * 100

    def _comprehensive_analysis(self, test_results):
        """종합 분석"""
        if not test_results:
            return {"error": "테스트 결과 없음"}
        
        successful_tests = [r for r in test_results if r.get("success", False)]
        
        if not successful_tests:
            return {"error": "성공한 테스트 없음"}
        
        analysis = {
            "summary": {
                "total_tests": len(test_results),
                "successful_tests": len(successful_tests),
                "success_rate": (len(successful_tests) / len(test_results)) * 100,
                "avg_processing_time": sum(r["processing_time"] for r in successful_tests) / len(successful_tests)
            },
            "quality_metrics": {
                "avg_template_compliance": sum(r.get("template_compliance", 0) for r in successful_tests) / len(successful_tests),
                "avg_crisis_accuracy": sum(r.get("crisis_accuracy", 0) for r in successful_tests) / len(successful_tests),
                "avg_department_relevance": sum(r.get("department_relevance", 0) for r in successful_tests) / len(successful_tests),
                "avg_structural_completeness": sum(r.get("structural_completeness", 0) for r in successful_tests) / len(successful_tests),
                "avg_keyword_coverage": sum(r.get("keyword_coverage", 0) for r in successful_tests) / len(successful_tests)
            },
            "performance_issues": [],
            "improvement_points": []
        }
        
        # 성능 이슈 식별
        if analysis["summary"]["avg_processing_time"] > 30:
            analysis["performance_issues"].append("처리 시간이 30초를 초과함")
        
        if analysis["quality_metrics"]["avg_template_compliance"] < 80:
            analysis["improvement_points"].append("템플릿 준수도 개선 필요")
        
        if analysis["quality_metrics"]["avg_crisis_accuracy"] < 70:
            analysis["improvement_points"].append("위기단계 분류 정확도 향상 필요")
        
        if analysis["quality_metrics"]["avg_department_relevance"] < 60:
            analysis["improvement_points"].append("유관부서 매핑 로직 개선 필요")
        
        return analysis

    def _save_results(self, test_results, overall_assessment):
        """결과 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 상세 결과 저장
        detailed_file = f"quality_test_detailed_{timestamp}.json"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_results": test_results,
                "overall_assessment": overall_assessment,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        # 요약 보고서 저장
        summary_file = f"quality_assessment_report_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("포스코인터내셔널 언론대응 AI 시스템 - 답변 퀄리티 평가 보고서\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"평가 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if overall_assessment and "summary" in overall_assessment:
                f.write("## 전체 성능 요약\n")
                f.write(f"- 총 테스트: {overall_assessment['summary']['total_tests']}건\n")
                f.write(f"- 성공률: {overall_assessment['summary']['success_rate']:.1f}%\n")
                f.write(f"- 평균 처리시간: {overall_assessment['summary']['avg_processing_time']:.2f}초\n\n")
                
                f.write("## 품질 지표\n")
                metrics = overall_assessment['quality_metrics']
                f.write(f"- 템플릿 준수도: {metrics['avg_template_compliance']:.1f}%\n")
                f.write(f"- 위기단계 정확도: {metrics['avg_crisis_accuracy']:.1f}%\n")
                f.write(f"- 부서 연관성: {metrics['avg_department_relevance']:.1f}%\n")
                f.write(f"- 구조적 완성도: {metrics['avg_structural_completeness']:.1f}%\n")
                f.write(f"- 키워드 포함도: {metrics['avg_keyword_coverage']:.1f}%\n\n")
                
                if overall_assessment['improvement_points']:
                    f.write("## 개선 포인트\n")
                    for point in overall_assessment['improvement_points']:
                        f.write(f"- {point}\n")
        
        print(f"\n결과 저장 완료:")
        print(f"- 상세 결과: {detailed_file}")
        print(f"- 요약 보고서: {summary_file}")

def main():
    """메인 실행"""
    assessor = QualityAssessment()
    test_results, overall_assessment = assessor.run_comprehensive_test()
    
    if overall_assessment:
        print(f"\n{'='*60}")
        print("종합 평가 결과")
        print(f"{'='*60}")
        
        if "summary" in overall_assessment:
            print(f"성공률: {overall_assessment['summary']['success_rate']:.1f}%")
            print(f"평균 처리시간: {overall_assessment['summary']['avg_processing_time']:.2f}초")
        
        if "quality_metrics" in overall_assessment:
            metrics = overall_assessment['quality_metrics']
            print(f"템플릿 준수도: {metrics['avg_template_compliance']:.1f}%")
            print(f"위기단계 정확도: {metrics['avg_crisis_accuracy']:.1f}%")
            print(f"부서 연관성: {metrics['avg_department_relevance']:.1f}%")
        
        if overall_assessment.get('improvement_points'):
            print(f"\n주요 개선 포인트:")
            for point in overall_assessment['improvement_points']:
                print(f"- {point}")

if __name__ == "__main__":
    main()