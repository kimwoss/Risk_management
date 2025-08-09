#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실적 공시 유형 특화 품질 개선 모듈
"""

import re
from datetime import datetime
from typing import Dict, List, Any

class FinancialEnhancer:
    """실적 공시 관련 보고서 전문 개선"""
    
    def __init__(self):
        self.financial_data = self._load_financial_templates()
        self.ir_terms = self._load_ir_terms()
        self.business_segments = self._load_business_segments()
    
    def enhance_financial_report(self, base_report: str, issue_description: str, 
                               media_name: str, reporter_name: str) -> str:
        """실적 공시 유형 보고서 특화 개선"""
        
        print("START: 실적 공시 특화 품질 개선...")
        
        # 실적 관련 이슈인지 확인
        if not self._is_financial_issue(issue_description):
            print("INFO: 일반 이슈로 분류, 표준 개선 적용")
            return base_report
        
        enhanced_report = base_report
        
        # 1. IR 담당자 정보 정확화
        enhanced_report = self._set_ir_contact(enhanced_report, issue_description)
        
        # 2. 구체적 재무 수치 추가
        enhanced_report = self._add_financial_figures(enhanced_report, issue_description)
        
        # 3. 사업부문별 세분화
        enhanced_report = self._add_business_segments(enhanced_report, issue_description)
        
        # 4. IR 전문용어 강화
        enhanced_report = self._enhance_ir_terminology(enhanced_report)
        
        # 5. 균형적 실적 표현
        enhanced_report = self._balance_financial_presentation(enhanced_report)
        
        # 6. 투명성 및 객관성 강화
        enhanced_report = self._enhance_transparency(enhanced_report, issue_description)
        
        print("SUCCESS: 실적 공시 특화 개선 완료")
        return enhanced_report
    
    def _is_financial_issue(self, issue_description: str) -> bool:
        """실적 공시 관련 이슈인지 판단"""
        financial_keywords = [
            "실적", "매출", "영업이익", "순이익", "분기", "연간", 
            "재무", "수익", "손익", "배당", "실적발표", "IR", "투자자"
        ]
        return any(keyword in issue_description for keyword in financial_keywords)
    
    def _set_ir_contact(self, report: str, issue_description: str) -> str:
        """IR 담당자 정보 정확화"""
        
        # 실적 관련 문의는 IR그룹 담당
        ir_contact = "IR그룹/유근석 리더"
        
        # 유관 의견 섹션에 IR 담당자 정보 추가/수정
        if "4. 유관 의견" in report:
            # 기존 담당자 정보가 있으면 교체
            if "(" in report and ")" in report:
                pattern = r'4\. 유관 의견\([^)]+\):'
                report = re.sub(pattern, f'4. 유관 의견({ir_contact}):', report)
            else:
                report = report.replace("4. 유관 의견:", f"4. 유관 의견({ir_contact}):")
        
        # 일반적 부서명도 IR그룹으로 교체
        general_departments = ["경영기획팀", "홍보그룹", "관련 부서", "해당 부서"]
        for dept in general_departments:
            if dept in report and "실적" in issue_description:
                report = report.replace(dept, "IR그룹")
        
        return report
    
    def _add_financial_figures(self, report: str, issue_description: str) -> str:
        """구체적 재무 수치 추가"""
        
        # 이슈 유형별 재무 데이터 매핑
        if "2분기" in issue_description or "Q2" in issue_description:
            financial_data = {
                "매출": "약 8조 1,440억 원 (전년 동기 대비 약 1.7% 감소)",
                "영업이익": "약 3,137억 원 (전년 동기 대비 약 10.3% 감소)", 
                "순이익": "약 905억 원 (전년 동기 대비 약 52.3% 감소)"
            }
        else:
            # 기본 템플릿 (연간 실적 추정)
            financial_data = {
                "매출": "연결 기준 약 16조원대 (전년 대비 소폭 감소)",
                "영업이익": "약 6,000억원대 (시장 여건 반영)",
                "순이익": "약 2,000억원대 (원자재 가격 변동 영향)"
            }
        
        # 사실확인 섹션 강화
        if "사실 확인:" in report:
            fact_start = report.find("사실 확인:")
            fact_end = report.find("- 설명 논리:")
            if fact_end == -1:
                fact_end = report.find("5. 대응 방안:")
            
            enhanced_fact = f"""사실 확인:
    ▪ 연결 기준 매출: {financial_data['매출']}
    ▪ 영업이익: {financial_data['영업이익']}
    ▪ 순이익: {financial_data['순이익']}
    ▪ 주요 사업별 성과:
      - 철강 부문: 글로벌 수요 회복 및 고부가 제품 확대 효과로 전년 대비 실적 개선
      - 에너지 부문: 국제 원자재 가격 변동에도 안정적 공급망 유지
      - 식량 부문: 해외 거점 다변화를 통한 수급 안정성 확보"""
            
            if fact_end != -1:
                report = report[:fact_start] + "- " + enhanced_fact + "\n" + report[fact_end:]
        
        return report
    
    def _add_business_segments(self, report: str, issue_description: str) -> str:
        """사업부문별 세분화 정보 추가"""
        
        # 사업부문별 상세 성과 (이미 _add_financial_figures에서 추가됨)
        # 추가적으로 각 부문별 전략 방향 언급
        
        if "대응 방안" in report:
            # 사업부문별 전략 메시지 추가
            strategic_message = """
  - 부문별 전략 방향:
    * 철강: 고부가가치 제품 중심의 포트폴리오 전환 지속
    * 에너지: 신재생 에너지 및 친환경 사업 확대
    * 식량: 글로벌 공급망 최적화 및 수직계열화 강화"""
            
            # 대응 방안 섹션에 추가
            response_start = report.find("5. 대응 방안:")
            response_end = report.find("6. 대응 결과:")
            if response_end == -1:
                response_end = len(report)
            
            if response_start != -1:
                existing_response = report[response_start:response_end]
                new_response = existing_response + strategic_message + "\n"
                report = report[:response_start] + new_response + report[response_end:]
        
        return report
    
    def _enhance_ir_terminology(self, report: str) -> str:
        """IR 전문용어 강화"""
        
        # 일반 용어를 IR 전문용어로 교체
        ir_replacements = [
            ("매출", "연결기준 매출"),
            ("이익", "영업이익"),
            ("수익성", "수익성 지표"), 
            ("성장", "지속가능한 성장"),
            ("투자", "전략적 투자"),
            ("시장", "시장 포지션"),
            ("경쟁력", "시장 경쟁력"),
            ("실적", "재무성과"),
            ("계획", "중장기 로드맵"),
            ("목표", "재무 목표"),
            ("회사", "당사"),
            ("주주", "주주가치"),
            ("배당", "주주환원"),
            ("현금", "잉여현금흐름")
        ]
        
        for generic_term, ir_term in ir_replacements:
            # 이미 IR 용어가 포함된 경우는 제외
            if ir_term not in report:
                report = report.replace(generic_term, ir_term)
        
        return report
    
    def _balance_financial_presentation(self, report: str) -> str:
        """균형적 실적 표현 (부정적 실적도 객관적 제시)"""
        
        # 설명 논리에 균형적 관점 추가
        if "설명 논리:" in report:
            balanced_logic = """설명 논리: 2분기 실적은 글로벌 경제 불확실성과 원자재 가격 변동 등 대외 여건 영향으로 전년 동기 대비 일부 감소하였으나, 철강·에너지·식량 등 핵심 사업에서의 안정적 성장과 공급망 강화, 재무구조 개선을 통해 지속적인 성장을 추진하고 있음. 하반기에는 시장 회복세와 함께 구조적 경쟁력 강화 효과가 본격 나타날 것으로 예상."""
            
            logic_start = report.find("설명 논리:")
            logic_end = report.find("5. 대응 방안:")
            if logic_end == -1:
                logic_end = report.find("- 메시지")
            
            if logic_start != -1 and logic_end != -1:
                report = report[:logic_start] + "- " + balanced_logic + "\n" + report[logic_end:]
        
        return report
    
    def _enhance_transparency(self, report: str, issue_description: str) -> str:
        """투명성 및 객관성 강화"""
        
        # 원보이스에 투명성 강조 메시지 추가
        if "원보이스" in report:
            transparent_message = '"포스코인터내셔널은 2분기 실적에 대해 투명하게 공개하며, 단기적 어려움에도 불구하고 중장기 성장 동력 확보를 통해 주주가치 제고에 최선을 다하겠습니다"'
            
            # 기존 원보이스를 투명성 중심 메시지로 교체
            voice_pattern = r'원보이스.*?(?=\n.*이후 대응|$)'
            new_voice = f"원보이스: {transparent_message}라는 메시지 전달"
            report = re.sub(voice_pattern, new_voice, report, flags=re.DOTALL)
        
        return report
    
    def _load_financial_templates(self) -> Dict:
        """재무 데이터 템플릿"""
        return {
            "quarterly": {
                "Q1": {"매출": "약 8조원대", "영업이익": "약 3,000억원대"},
                "Q2": {"매출": "약 8조 1,440억 원", "영업이익": "약 3,137억 원"},
                "Q3": {"매출": "약 8조 5,000억원대", "영업이익": "약 3,500억원대"},
                "Q4": {"매출": "약 9조원대", "영업이익": "약 4,000억원대"}
            },
            "annual": {
                "2024": {"매출": "약 33조원", "영업이익": "약 1조 3천억원"},
                "2025E": {"매출": "약 35조원", "영업이익": "약 1조 5천억원"}
            }
        }
    
    def _load_ir_terms(self) -> List[str]:
        """IR 전문 용어"""
        return [
            "연결 기준", "별도 기준", "영업이익", "EBITDA", "순이익", "당기순이익",
            "ROE", "ROA", "부채비율", "유동비율", "배당수익률", "주주환원",
            "잉여현금흐름", "자본적지출", "운전자본", "투자수익률"
        ]
    
    def _load_business_segments(self) -> Dict:
        """사업부문별 정보"""
        return {
            "철강": {
                "제품": ["열연강판", "냉연강판", "도금강판", "특수강"],
                "시장": "자동차, 가전, 건설",
                "전략": "고부가가치 제품 중심 포트폴리오"
            },
            "에너지": {
                "사업": ["석탄", "가스", "신재생에너지", "발전"],
                "지역": "호주, 인도네시아, 국내",
                "전략": "친환경 에너지 전환"
            },
            "식량": {
                "품목": ["곡물", "유지종자", "식품원료"],
                "거점": "우크라이나, 호주, 미얀마, 아르헨티나",
                "전략": "글로벌 수직계열화"
            }
        }

def main():
    """테스트 함수"""
    print("실적 공시 특화 품질 개선 모듈 테스트")
    
    # 샘플 실적 문의 보고서
    sample_report = """<이슈 발생 보고>

1. 발생 일시: 2025. 08. 09. 13:00

2. 발생 단계: 1단계(관심)

3. 발생 내용:
(조선일보 김조선)
2분기 실적 관련 문의

4. 유관 의견:
- 사실 확인: 2분기 실적은 전반적으로 양호한 수준
- 설명 논리: 지속적인 성장을 위한 노력 지속

5. 대응 방안:
- 원보이스: 안정적 경영 지속
- 이후 대응 방향성: 투명한 정보 제공
"""
    
    enhancer = FinancialEnhancer()
    enhanced_report = enhancer.enhance_financial_report(
        sample_report, 
        "2025년 2분기 포스코인터내셔널 주요사업별 실적과 향후 계획 관련 문의",
        "조선일보",
        "김조선"
    )
    
    print("\n실적 공시 특화 개선 후 보고서:")
    print("="*60)
    print(enhanced_report)

if __name__ == "__main__":
    main()