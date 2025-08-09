"""
최적화된 보고서 생성기 - LLM 호출 통합 방식
기존 5-6회 API 호출을 1-2회로 단축
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

class OptimizedReportGenerator:
    """최적화된 보고서 생성기"""
    
    def __init__(self, llm_manager, data_folder="data"):
        self.llm = llm_manager
        self.data_folder = data_folder
        self.master_data = self._load_master_data()
    
    def generate_fast_report(self, media_name: str, reporter_name: str, issue_description: str) -> str:
        """고속 보고서 생성 (15-30초 목표)"""
        
        print(f"START: 최적화된 고속 보고서 생성 - {media_name}")
        
        start_time = datetime.now()
        
        # 1. 기본 데이터 수집 (로컬 처리 - 1초 이내)
        basic_data = self._collect_basic_data(media_name, issue_description)
        
        # 2. 통합 LLM 분석 (1회 API 호출 - 10-15초)
        integrated_analysis = self._integrated_llm_analysis(
            media_name, reporter_name, issue_description, basic_data
        )
        
        # 3. 구조화된 보고서 생성 (로컬 처리 - 1초 이내)
        final_report = self._format_structured_report(
            media_name, reporter_name, issue_description, 
            basic_data, integrated_analysis
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        print(f"COMPLETE: 최적화된 처리 완료 ({processing_time:.2f}초)")
        
        return final_report
    
    def _collect_basic_data(self, media_name: str, issue_description: str) -> Dict:
        """기본 데이터 수집 (로컬 처리)"""
        
        basic_data = {
            "timestamp": datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분"),
            "relevant_departments": [],
            "suggested_crisis_level": "2단계(주의)",  # 기본값
            "media_info": {}
        }
        
        # 부서 매핑 (키워드 기반 빠른 매칭)
        if self.master_data and "departments" in self.master_data:
            issue_keywords = issue_description.lower()
            
            dept_mapping = {
                "철강": ["철강사업부", "품질보증팀"],
                "자원": ["자원개발사업부", "자원탐사팀"],
                "환경": ["ESG경영실", "환경안전팀"],
                "품질": ["품질보증팀", "기술연구소"],
                "재무": ["재무팀", "경영기획팀", "IR팀"],
                "광산": ["자원개발사업부", "해외사업팀"],
                "배터리": ["이차전지소재사업부", "기술연구소"]
            }
            
            for keyword, depts in dept_mapping.items():
                if keyword in issue_keywords:
                    basic_data["relevant_departments"].extend(depts)
                    break
            
            # 기본 부서 (매핑 안된 경우)
            if not basic_data["relevant_departments"]:
                basic_data["relevant_departments"] = ["홍보그룹", "경영기획팀"]
        
        # 위기단계 추정 (키워드 기반)
        high_risk_keywords = ["사고", "중단", "폐쇄", "소송", "환경오염", "대규모"]
        medium_risk_keywords = ["지연", "불량", "문제", "우려", "논란"]
        
        if any(keyword in issue_description for keyword in high_risk_keywords):
            basic_data["suggested_crisis_level"] = "3단계(위기)"
        elif any(keyword in issue_description for keyword in medium_risk_keywords):
            basic_data["suggested_crisis_level"] = "2단계(주의)"
        else:
            basic_data["suggested_crisis_level"] = "1단계(관심)"
        
        return basic_data
    
    def _integrated_llm_analysis(self, media_name: str, reporter_name: str, 
                               issue_description: str, basic_data: Dict) -> Dict:
        """통합 LLM 분석 (1회 API 호출로 모든 분석 수행)"""
        
        integrated_prompt = f"""
당신은 포스코인터내셔널의 언론 최고 책임자(CCO) 전략적 의사결정 지원 AI입니다.

다음 이슈에 대해 종합적인 분석을 수행하고 JSON 형식으로 결과를 제공하세요:

**입력 정보:**
- 언론사: {media_name}
- 기자명: {reporter_name}  
- 이슈 내용: {issue_description}
- 추정 위기단계: {basic_data['suggested_crisis_level']}
- 관련 부서: {', '.join(basic_data['relevant_departments'])}

**출력 형식 (JSON):**
{{
  "issue_analysis": {{
    "category": "이슈 분류 (제품품질/환경안전/재무성과/사업운영 중 선택)",
    "severity": "심각도 (높음/중간/낮음)",
    "urgency": "시급성 (높음/중간/낮음)",
    "summary": "이슈 핵심 요약 (50자 이내)"
  }},
  "crisis_assessment": {{
    "level": "위기단계 (1단계(관심)/2단계(주의)/3단계(위기)/4단계(비상))",
    "rationale": "단계 선정 근거 (100자 이내)"
  }},
  "fact_verification": {{
    "status": "사실확인상태 (확인됨/추정단계/확인불가)",
    "credibility": "신뢰도 (높음/중간/낮음)",
    "background": "배경 상황 (150자 이내)",
    "cautions": ["주의사항1", "주의사항2"]
  }},
  "department_opinions": {{
    "fact_check": "현재까지 파악된 객관적 정보 (200자 이내)",
    "explanation_logic": "이슈 해소를 위한 합리적 설명 구조 (200자 이내)",
    "message_direction": "대외 발표 시 일관된 표현 방향 (100자 이내)"
  }},
  "response_strategy": {{
    "key_messages": ["핵심 메시지1", "핵심 메시지2", "핵심 메시지3"],
    "immediate_actions": ["즉시 대응1", "즉시 대응2"],
    "communication_tone": "커뮤니케이션 기조 (신중함/투명성/적극성 등)"
  }},
  "similar_cases": {{
    "reference": "유사 사례 참조 (100자 이내)",
    "lessons": "교훈 및 시사점 (100자 이내)"
  }},
  "concept_definition": {{
    "issue_concept": "이슈 개념적 정의 (100자 이내)", 
    "business_impact": "경영/사회/법률적 함의 (150자 이내)"
  }}
}}

위 형식을 정확히 준수하여 JSON으로만 응답하세요. 추가 설명은 하지 마세요.
        """
        
        try:
            response = self.llm.chat(integrated_prompt)
            return json.loads(response)
        except json.JSONDecodeError:
            print("WARNING: JSON 파싱 실패, 기본값 사용")
            return self._get_fallback_analysis()
        except Exception as e:
            print(f"WARNING: 통합 분석 실패: {str(e)}")
            return self._get_fallback_analysis()
    
    def _format_structured_report(self, media_name: str, reporter_name: str, 
                                issue_description: str, basic_data: Dict, 
                                analysis: Dict) -> str:
        """구조화된 보고서 포맷팅"""
        
        sections = []
        
        # 헤더
        sections.append("<이슈 발생 보고>")
        sections.append("")
        
        # 1. 발생 일시
        sections.append(f"1. 발생 일시: {basic_data['timestamp']}")
        sections.append("")
        
        # 2. 발생 단계
        crisis_level = analysis.get('crisis_assessment', {}).get('level', basic_data['suggested_crisis_level'])
        sections.append(f"2. 발생 단계: {crisis_level}")
        sections.append("")
        
        # 3. 발생 내용
        sections.append("3. 발생 내용:")
        sections.append(f"({media_name} {reporter_name})")
        sections.append("")
        
        issue_summary = analysis.get('issue_analysis', {}).get('summary', issue_description[:100])
        sections.append(f"- {issue_summary}")
        
        issue_category = analysis.get('issue_analysis', {}).get('category', 'N/A')
        sections.append(f"- 분류: {issue_category}")
        sections.append("")
        
        # 4. 유관 의견
        sections.append("4. 유관 의견:")
        
        dept_opinions = analysis.get('department_opinions', {})
        fact_check = dept_opinions.get('fact_check', '현재 사실 관계 확인 중')
        sections.append(f"- 사실 확인: {fact_check}")
        
        explanation = dept_opinions.get('explanation_logic', '관련 부서 의견 수렴 중')
        sections.append(f"- 설명 논리: {explanation}")
        
        message_dir = dept_opinions.get('message_direction', '신중한 접근')
        sections.append(f"- 메시지 방향성: {message_dir}")
        sections.append("")
        
        # 5. 대응 방안
        sections.append("5. 대응 방안:")
        
        response_strategy = analysis.get('response_strategy', {})
        key_messages = response_strategy.get('key_messages', ['정확한 사실 확인 후 대응'])
        sections.append("- 원보이스:")
        for msg in key_messages[:3]:
            sections.append(f"  '{msg}'")
        
        immediate_actions = response_strategy.get('immediate_actions', ['관련 부서 협의'])
        sections.append("- 이후 대응 방향성:")
        for action in immediate_actions[:2]:
            sections.append(f"  - {action}")
        sections.append("")
        
        # 6. 대응 결과
        sections.append("6. 대응 결과: (추후 업데이트)")
        sections.append("")
        
        # 참조 섹션
        sections.append("=" * 50)
        sections.append("참조. 최근 유사 사례 (1년 이내):")
        similar_ref = analysis.get('similar_cases', {}).get('reference', '관련 사례 조사 중')
        sections.append(f"- {similar_ref}")
        lessons = analysis.get('similar_cases', {}).get('lessons', '지속적 모니터링 필요')
        sections.append(f"- 교훈: {lessons}")
        sections.append("")
        
        sections.append("참조. 이슈 정의 및 개념 정립:")
        concept_def = analysis.get('concept_definition', {})
        issue_concept = concept_def.get('issue_concept', issue_description)
        sections.append(f"- 개념: {issue_concept}")
        
        business_impact = concept_def.get('business_impact', '영향 분석 중')
        sections.append(f"- 경영/사회/법률적 함의: {business_impact}")
        
        return "\n".join(sections)
    
    def _get_fallback_analysis(self) -> Dict:
        """기본 분석 결과 (LLM 실패 시)"""
        return {
            "issue_analysis": {
                "category": "사업운영",
                "severity": "중간", 
                "urgency": "중간",
                "summary": "관련 이슈 발생으로 대응 검토 중"
            },
            "crisis_assessment": {
                "level": "2단계(주의)",
                "rationale": "언론 보도로 인한 주의 단계 적용"
            },
            "fact_verification": {
                "status": "확인불가",
                "credibility": "중간",
                "background": "추가 사실 확인 진행 중",
                "cautions": ["정확한 정보 확인 필요", "신중한 대응 요구"]
            },
            "department_opinions": {
                "fact_check": "현재 관련 부서에서 사실 관계 확인 중",
                "explanation_logic": "투명하고 신속한 정보 공개를 통한 신뢰 회복",
                "message_direction": "사실에 기반한 정확한 정보 제공"
            },
            "response_strategy": {
                "key_messages": ["사실 확인 후 투명한 소통", "고객 신뢰 최우선", "지속적 품질 개선"],
                "immediate_actions": ["관련 부서 긴급 회의", "사실 관계 정확한 파악"],
                "communication_tone": "신중하고 투명한 접근"
            },
            "similar_cases": {
                "reference": "유사 이슈 대응 사례 검토 중",
                "lessons": "투명한 소통과 신속한 대응의 중요성"
            },
            "concept_definition": {
                "issue_concept": "기업 운영 과정에서 발생한 이슈 상황",
                "business_impact": "기업 신뢰도 및 브랜드 가치에 미치는 영향 분석 필요"
            }
        }
    
    def _load_master_data(self) -> Dict:
        """마스터 데이터 로드"""
        try:
            with open(os.path.join(self.data_folder, "master_data.json"), 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"WARNING: 마스터 데이터 로드 실패: {str(e)}")
            return {}

def main():
    """테스트 함수"""
    print("최적화된 보고서 생성기 테스트")
    
    # Mock LLM (테스트용)
    class MockLLM:
        def chat(self, prompt):
            return '''{
                "issue_analysis": {
                    "category": "제품품질",
                    "severity": "중간",
                    "urgency": "높음",
                    "summary": "철강제품 품질 불량으로 납품 지연 우려"
                },
                "crisis_assessment": {
                    "level": "2단계(주의)",
                    "rationale": "제품 품질 이슈로 고객 신뢰 영향 가능"
                },
                "fact_verification": {
                    "status": "확인됨",
                    "credibility": "높음",
                    "background": "정기 품질 검사에서 일부 제품 기준 미달 확인",
                    "cautions": ["추가 제품 검사 필요", "고객사 신속 통보 요구"]
                },
                "department_opinions": {
                    "fact_check": "품질보증팀에서 해당 제품 로트 전수 검사 진행 중",
                    "explanation_logic": "엄격한 품질 관리 시스템 하에 발견된 이슈로 즉시 대응 조치",
                    "message_direction": "품질 최우선 정책과 투명한 정보 공개"
                },
                "response_strategy": {
                    "key_messages": ["품질 최우선 경영 방침 재확인", "투명한 조사 결과 공유", "재발 방지 시스템 강화"],
                    "immediate_actions": ["해당 제품 출하 중단", "고객사 긴급 통보"],
                    "communication_tone": "신중하고 전문적인 대응"
                },
                "similar_cases": {
                    "reference": "2023년 타 철강사 품질 이슈 대응 사례 참조",
                    "lessons": "신속한 초기 대응과 투명한 소통의 중요성"
                },
                "concept_definition": {
                    "issue_concept": "제품 품질 관리 프로세스의 일시적 공백으로 인한 이슈",
                    "business_impact": "단기적 매출 영향보다 장기적 신뢰 관계 유지가 중요"
                }
            }'''
    
    generator = OptimizedReportGenerator(MockLLM())
    
    result = generator.generate_fast_report(
        "조선일보", 
        "김기자",
        "포스코인터내셔널 철강제품 품질 불량 발견"
    )
    
    print(f"\n생성 결과 길이: {len(result)}자")
    print("\n" + "="*50)
    print("생성된 보고서:")
    print("="*50)
    print(result)

if __name__ == "__main__":
    main()