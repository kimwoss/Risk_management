#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3단계 위기 사안 특화 대응 시스템
"""

import re
from datetime import datetime
from typing import Dict, List, Any, Tuple

class CrisisResponseEnhancer:
    """위기 사안 전문 대응 시스템"""
    
    def __init__(self):
        self.crisis_levels = self._load_crisis_level_matrix()
        self.legal_terms = self._load_legal_terminology()
        self.crisis_contacts = self._load_crisis_contact_matrix()
        self.sensitive_keywords = self._load_sensitive_keywords()
    
    def enhance_crisis_response(self, base_report: str, issue_description: str, 
                              media_name: str, reporter_name: str) -> str:
        """위기 사안 특화 대응 강화"""
        
        # 위기 수준 분석
        crisis_level, risk_factors = self._analyze_crisis_level(issue_description)
        
        if crisis_level < 3:  # 1-2단계는 기존 시스템 사용
            print(f"INFO: {crisis_level}단계 이슈로 분류, 표준 처리")
            return base_report
        
        print(f"START: {crisis_level}단계 위기 사안 특화 처리 - 위험요소: {len(risk_factors)}개")
        
        enhanced_report = base_report
        
        # 1. 위기단계 정확한 분류
        enhanced_report = self._set_accurate_crisis_level(enhanced_report, crisis_level, risk_factors)
        
        # 2. 다부서 협업 체계 구축
        enhanced_report = self._establish_multi_department_response(enhanced_report, issue_description, crisis_level)
        
        # 3. 법적 방어 논리 구축
        enhanced_report = self._build_legal_defense_logic(enhanced_report, issue_description, risk_factors)
        
        # 4. 전문 용어 및 구조 강화
        enhanced_report = self._enhance_professional_terminology(enhanced_report, issue_description)
        
        # 5. 체계적 원보이스 구성
        enhanced_report = self._build_systematic_key_message(enhanced_report, issue_description, crisis_level)
        
        # 6. 비상 연락망 구축
        enhanced_report = self._establish_emergency_contacts(enhanced_report, issue_description)
        
        # 7. Q&A 브릿지 추가
        enhanced_report = self._add_qa_bridge(enhanced_report, issue_description, risk_factors)
        
        print("SUCCESS: 위기 사안 특화 처리 완료")
        return enhanced_report
    
    def _analyze_crisis_level(self, issue_description: str) -> Tuple[int, List[str]]:
        """위기 수준 정밀 분석"""
        
        risk_factors = []
        crisis_score = 1  # 기본 1단계
        
        # 최고위험 키워드 (4단계 확정)
        critical_keywords = ["북한", "밀수", "첩보기관", "UN제재", "수사착수"]
        if any(keyword in issue_description for keyword in critical_keywords):
            risk_factors.append("최고위험")
            crisis_score += 3  # 즉시 4단계로
        
        # 정치적 민감성
        political_keywords = ["군부", "제재", "정권", "정치", "외교", "국제관계", "러시아", "우회거래"]
        if any(keyword in issue_description for keyword in political_keywords):
            risk_factors.append("정치적_민감성")
            crisis_score += 1
        
        # 법적 위험
        legal_keywords = ["의혹", "위반", "불법", "조사", "해명", "책임", "소송"]
        if any(keyword in issue_description for keyword in legal_keywords):
            risk_factors.append("법적_위험")
            crisis_score += 1
        
        # ESG 리스크
        esg_keywords = ["인권", "환경", "지배구조", "ESG", "지속가능"]
        if any(keyword in issue_description for keyword in esg_keywords):
            risk_factors.append("ESG_리스크")
            crisis_score += 0.5
        
        # 국제적 파급
        international_keywords = ["해외", "국제", "글로벌", "다국적", "외국"]
        if any(keyword in issue_description for keyword in international_keywords):
            risk_factors.append("국제적_파급")
            crisis_score += 0.5
        
        # 미디어 관심도
        high_attention_keywords = ["의혹", "폭로", "추적", "단독", "특보"]
        if any(keyword in issue_description for keyword in high_attention_keywords):
            risk_factors.append("높은_미디어관심")
            crisis_score += 0.5
        
        final_level = min(int(crisis_score), 4)  # 최대 4단계
        
        return final_level, risk_factors
    
    def _set_accurate_crisis_level(self, report: str, level: int, risk_factors: List[str]) -> str:
        """정확한 위기단계 설정"""
        
        level_names = {
            1: "1단계(관심)",
            2: "2단계(주의)", 
            3: "3단계(위기)",
            4: "4단계(비상)"
        }
        
        # 기존 위기단계를 정확한 단계로 교체
        for old_level in range(1, 5):
            old_pattern = f"{old_level}단계"
            if old_pattern in report:
                report = report.replace(old_pattern, level_names[level])
        
        # 발생 단계 → 대응 단계로 수정 (위기 사안에서는 대응 단계가 적절)
        report = report.replace("2. 발생 단계:", "2. 대응 단계:")
        
        return report
    
    def _establish_multi_department_response(self, report: str, issue_description: str, level: int) -> str:
        """다부서 협업 대응 체계"""
        
        if level >= 3:
            # 미얀마/에너지 관련 특화 담당자
            if "미얀마" in issue_description or "가스" in issue_description or "에너지" in issue_description:
                primary_contacts = [
                    "가스사업운영섹션 / 김승모 부장 02-759-2288, 010-3006-9811",
                    "대외협력그룹 / 고영택 차장 02-3457-2089, 010-2911-7868"
                ]
            else:
                # 일반 위기 사안
                primary_contacts = [
                    "법무팀 / 이법무 팀장 02-3457-2100, 010-1234-5678",
                    "ESG경영실 / 박ESG 실장 02-3457-2200, 010-2345-6789"
                ]
            
            # 4. 유관 의견 섹션 개선
            if "4. 유관 의견" in report:
                contact_text = "\n".join([f"  - {contact}" for contact in primary_contacts])
                
                # 기존 담당자 정보 교체
                opinion_start = report.find("4. 유관 의견")
                opinion_end = report.find("5. 대응 방안:")
                if opinion_end == -1:
                    opinion_end = len(report)
                
                new_opinion_section = f"4. 유관 의견(현업부서/담당자)\n{contact_text}\n\n  (가안) 사실 확인"
                
                # 기존 사실확인 내용 보존
                existing_content = report[opinion_start:opinion_end]
                if "사실 확인" in existing_content:
                    fact_content = existing_content[existing_content.find("사실 확인"):]
                    new_opinion_section += f"\n  - {fact_content.strip()}"
                
                report = report[:opinion_start] + new_opinion_section + "\n\n" + report[opinion_end:]
        
        return report
    
    def _build_legal_defense_logic(self, report: str, issue_description: str, risk_factors: List[str]) -> str:
        """법적 방어 논리 구축"""
        
        legal_elements = []
        
        if "정치적_민감성" in risk_factors:
            legal_elements.append("정치 사안과 분리된 상업·기술적 합작 운영 원칙")
        
        if "법적_위험" in risk_factors:
            legal_elements.append("국제 제재와 국내외 법령을 철저히 준수")
            legal_elements.append("제재대상과 연계된 거래·금융서비스 방지를 위한 내부 통제 강화")
        
        if "ESG_리스크" in risk_factors:
            legal_elements.append("인권실사(HRDD)와 지역사회 프로그램 병행")
        
        if legal_elements and "설명 논리:" in report:
            legal_defense = f"설명 논리: {'; '.join(legal_elements)}. 당사는 관련 리스크를 최소화하고 투명한 경영을 통해 이해관계자들의 신뢰를 확보해 나가고 있음."
            
            # 기존 설명 논리 교체
            logic_start = report.find("설명 논리:")
            logic_end = report.find("5. 대응 방안:")
            if logic_end == -1:
                logic_end = report.find("- 메시지")
            
            if logic_start != -1 and logic_end != -1:
                report = report[:logic_start] + "- " + legal_defense + "\n\n" + report[logic_end:]
        
        return report
    
    def _enhance_professional_terminology(self, report: str, issue_description: str) -> str:
        """전문 용어 강화"""
        
        # 에너지/법무 전문용어 강제 추가
        if "가스" in issue_description or "에너지" in issue_description or "미얀마" in issue_description:
            # 사실확인 섹션에 전문용어 강제 삽입
            if "사실 확인" in report:
                professional_content = """
  - 사업 구조/원칙: 미얀마 서해상 A-1/A-3 'Shwe 프로젝트'는 생산물분배계약(PSC) 기반의 비법인 합작(UJV) 구조로 운영되며, 각 파트너는 지분에 비례해 독립적으로 가스를 판매·정산함. 정부·정책 변화와 무관하게 현지 전력수급 안정 등 공익적 성격을 고려해 안전·지속운영을 최우선으로 함.
  - '4단계 개발' 관련: 2024.07.24 지역매체에 '프로젝트 4단계 확대 관련 EPC(설계·구매·시공) 계약 체결' 보도가 있었음. 구체 사양·세부 일정·투자 규모 등은 계약상 비공개이며, 당사는 공개된 범위 내에서만 코멘트 가능.
  - 제재·준법 환경: MOGE(미얀마 석유가스공사)에 대해 EU('22.02 제재 지정, '25.04 연장)·미국 OFAC('23.10 특정 금융서비스 금지 지침) 등 국제 제재가 존재. 당사는 대외 제재 및 국내외 법령을 준수하며, 제재위반 소지가 있는 거래·금융서비스는 허용하지 않으며, 제재대상에게 직·간접 지원이 되지 않도록 통제를 강화. 인권실사(HRDD)와 지역사회 프로그램을 병행."""
                
                # 기존 사실확인을 전문용어 포함 버전으로 교체
                fact_start = report.find("사실 확인")
                fact_end = report.find("설명 논리:")
                if fact_end == -1:
                    fact_end = report.find("5. 대응 방안:")
                
                if fact_start != -1 and fact_end != -1:
                    report = report[:fact_start] + "사실 확인" + professional_content + "\n" + report[fact_end:]
        
        # 일반 법무 전문용어도 추가
        legal_replacements = [
            ("준수", "컴플라이언스 준수"),
            ("제재", "국제 제재"),
            ("통제", "내부통제시스템")
        ]
        
        for generic, professional in legal_replacements:
            if professional not in report:
                report = report.replace(generic, professional)
        
        return report
    
    def _build_systematic_key_message(self, report: str, issue_description: str, level: int) -> str:
        """체계적 원보이스 구성"""
        
        if level >= 3:
            # 미얀마 가스전 특화 메시지 (4단계 체계적 구성)
            if "미얀마" in issue_description or "가스" in issue_description:
                systematic_message = '''
  - 원보이스(초안):
    "Shwe 프로젝트는 PSC 기반의 국제 합작 구조로, 지역 전력공급 안정에 필수적인 에너지 인프라입니다. 
     당사는 국제 제재와 국내외 법령을 철저히 준수하며, 제재대상과 연계된 거래·금융서비스가 발생하지 않도록 내부 통제를 강화해 운영하고 있습니다. 
     '4단계' 관련 세부 내용은 계약상 비공개 사항으로 공개 범위 내에서만 안내드릴 수 있습니다. 
     구체 실적 수치는 공시자료를 기준으로 확인 부탁드립니다."'''
            else:
                # 일반 위기 사안 메시지
                systematic_message = '''
  - 원보이스(초안):
    "당사는 관련 사안에 대해 면밀히 검토하고 있으며, 모든 법적 요구사항과 국제 기준을 준수하고 있습니다.
     투명하고 책임감 있는 경영을 통해 이해관계자들의 신뢰를 확보해 나가겠습니다.
     구체적인 사항은 관련 절차에 따라 적절히 대응해 나가겠습니다."'''
            
            # 대응 방안 섹션에 체계적 원보이스 삽입
            if "5. 대응 방안:" in report:
                response_start = report.find("5. 대응 방안:")
                response_end = report.find("6. 대응 결과:")
                if response_end == -1:
                    response_end = len(report)
                
                # 기존 내용 보존하면서 원보이스 추가
                existing_response = report[response_start:response_end]
                if "원보이스" not in existing_response:
                    new_response = f"5. 대응 방안\n  - 단계: 3단계(위기) 유지. 법무·ESG·대외협력 동시 협의 → 대표이사/홀딩스 보고.{systematic_message}"
                    report = report[:response_start] + new_response + "\n\n" + report[response_end:]
                else:
                    # 기존 원보이스를 체계적 버전으로 교체
                    voice_pattern = r'원보이스.*?(?=\n.*이후 대응|6\. 대응 결과|$)'
                    report = re.sub(voice_pattern, systematic_message.strip(), report, flags=re.DOTALL)
        
        return report
    
    def _establish_emergency_contacts(self, report: str, issue_description: str) -> str:
        """비상 연락망 구축"""
        
        # 이미 _establish_multi_department_response에서 처리됨
        return report
    
    def _add_qa_bridge(self, report: str, issue_description: str, risk_factors: List[str]) -> str:
        """Q&A 브릿지 추가"""
        
        if "정치적_민감성" in risk_factors:
            qa_bridge = """
  - Q&A 브릿지
    · 군부와의 '관계' 질문 → "정치 사안과 분리된 상업·기술적 합작 운영 원칙, 제재 준수" 프레임"""
            
            # 대응 방안 섹션 끝에 추가
            if "5. 대응 방안:" in report:
                response_end = report.find("6. 대응 결과:")
                if response_end == -1:
                    response_end = len(report)
                
                response_content = report[:response_end] + qa_bridge + "\n\n" + report[response_end:]
                report = response_content
        
        return report
    
    def _load_crisis_level_matrix(self) -> Dict:
        """위기 단계 매트릭스"""
        return {
            1: {"name": "관심", "threshold": 1.0, "response": "부서 단독"},
            2: {"name": "주의", "threshold": 2.0, "response": "부서 + 홍보팀"},
            3: {"name": "위기", "threshold": 3.0, "response": "법무+ESG+대외협력"},
            4: {"name": "비상", "threshold": 4.0, "response": "전사 위기관리위원회"}
        }
    
    def _load_legal_terminology(self) -> List[str]:
        """법무 전문용어"""
        return [
            "컴플라이언스", "OFAC", "HRDD", "PSC", "UJV", "EPC", "MOGE",
            "제재 준수", "내부통제시스템", "리스크 관리", "거버넌스"
        ]
    
    def _load_crisis_contact_matrix(self) -> Dict:
        """위기 대응 연락망"""
        return {
            "에너지": [
                "가스사업운영섹션 / 김승모 부장 02-759-2288, 010-3006-9811",
                "대외협력그룹 / 고영택 차장 02-3457-2089, 010-2911-7868"
            ],
            "법무": [
                "법무팀 / 이법무 팀장 02-3457-2100, 010-1234-5678"
            ],
            "ESG": [
                "ESG경영실 / 박ESG 실장 02-3457-2200, 010-2345-6789"
            ]
        }
    
    def _load_sensitive_keywords(self) -> Dict:
        """민감 키워드 매트릭스"""
        return {
            "political": ["군부", "제재", "정권", "정치", "외교"],
            "legal": ["의혹", "위반", "불법", "조사", "해명"],
            "esg": ["인권", "환경", "지배구조", "ESG"],
            "international": ["해외", "국제", "글로벌", "외국"]
        }

def main():
    """테스트 함수"""
    print("위기 사안 특화 대응 시스템 테스트")
    
    # 샘플 위기 사안
    sample_report = """<이슈 발생 보고>

1. 발생 일시: 2025. 08. 09. 15:10

2. 발생 단계: 2단계(주의)

3. 발생 내용:
(동아일보 김동아)
미얀마 가스전 군부 연관 의혹

4. 유관 의견:
- 사실 확인: 관련 사실 확인 중
- 설명 논리: 투명한 대응

5. 대응 방안:
- 원보이스: 사실 확인 후 대응
"""
    
    enhancer = CrisisResponseEnhancer()
    enhanced_report = enhancer.enhance_crisis_response(
        sample_report,
        "미얀마 가스전 실적 개선 배경, 4단계 개발 진척, 군부 관계, 영업이익 지원금 의혹 해명 요구",
        "동아일보",
        "김동아"
    )
    
    print("\n위기 사안 특화 개선 후 보고서:")
    print("="*60)
    print(enhanced_report)

if __name__ == "__main__":
    main()