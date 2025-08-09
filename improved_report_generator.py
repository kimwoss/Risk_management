"""
개선된 보고서 생성 시스템
템플릿 구조를 강제로 준수하는 구조화된 접근법
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

class StructuredReportGenerator:
    """구조화된 보고서 생성기"""
    
    def __init__(self, data_folder: str = "data"):
        self.data_folder = data_folder
        self.template_sections = {
            "header": "이슈 발생 보고",
            "occurrence_time": "1. 발생 일시",
            "crisis_level": "2. 발생 단계", 
            "content": "3. 발생 내용",
            "department_opinions": "4. 유관 의견",
            "response_plan": "5. 대응 방안",
            "response_result": "6. 대응 결과",
            "reference_cases": "참조. 최근 유사 사례",
            "issue_definition": "참조. 이슈 정의 및 개념 정립"
        }
    
    def generate_structured_report(self, analysis_results: Dict[str, Any]) -> str:
        """구조화된 방식으로 보고서 생성"""
        
        sections = []
        
        # 헤더
        sections.append(f"<{self.template_sections['header']}>")
        sections.append("")
        
        # 1. 발생 일시
        sections.append(f"{self.template_sections['occurrence_time']}: {self._get_current_time()}")
        sections.append("")
        
        # 2. 발생 단계
        crisis_level = analysis_results.get('crisis_level', '확인 중')
        sections.append(f"{self.template_sections['crisis_level']}: {crisis_level}")
        sections.append("")
        
        # 3. 발생 내용
        sections.append(f"{self.template_sections['content']}:")
        content = self._generate_content_section(analysis_results)
        sections.append(content)
        sections.append("")
        
        # 4. 유관 의견
        sections.append(f"{self.template_sections['department_opinions']}:")
        opinions = self._generate_department_opinions_section(analysis_results)
        sections.append(opinions)
        sections.append("")
        
        # 5. 대응 방안
        sections.append(f"{self.template_sections['response_plan']}:")
        response_plan = self._generate_response_plan_section(analysis_results)
        sections.append(response_plan)
        sections.append("")
        
        # 6. 대응 결과 (공란)
        sections.append(f"{self.template_sections['response_result']}: (추후 업데이트 예정)")
        sections.append("")
        
        # 참조 섹션들
        sections.append("=" * 50)
        sections.append("REFERENCE: 추가 분석 정보")
        sections.append("=" * 50)
        sections.append("")
        
        # 참조. 최근 유사 사례
        sections.append(f"{self.template_sections['reference_cases']} (1년 이내):")
        similar_cases = self._generate_similar_cases_section(analysis_results)
        sections.append(similar_cases)
        sections.append("")
        
        # 참조. 이슈 정의 및 개념 정립
        sections.append(f"{self.template_sections['issue_definition']}:")
        issue_definition = self._generate_issue_definition_section(analysis_results)
        sections.append(issue_definition)
        
        return "\n".join(sections)
    
    def _get_current_time(self) -> str:
        """현재 시간 반환"""
        return datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
    
    def _generate_content_section(self, analysis_results: Dict[str, Any]) -> str:
        """3. 발생 내용 섹션 생성"""
        media_name = analysis_results.get('media_name', '언론사명 확인 중')
        reporter_name = analysis_results.get('reporter_name', '기자명 확인 중')
        issue_description = analysis_results.get('issue_description', '이슈 내용 확인 중')
        
        content_lines = []
        content_lines.append(f"({media_name} {reporter_name})")
        content_lines.append("")
        
        # 이슈 요약
        if analysis_results.get('initial_analysis', {}).get('summary'):
            content_lines.append("이슈 요약:")
            content_lines.append(f"- {analysis_results['initial_analysis']['summary']}")
        else:
            content_lines.append(f"- {issue_description}")
        
        # 카테고리 및 영향범위
        initial_analysis = analysis_results.get('initial_analysis', {})
        if initial_analysis.get('category'):
            content_lines.append(f"- 카테고리: {initial_analysis['category']}")
        if initial_analysis.get('impact_scope'):
            content_lines.append(f"- 영향범위: {initial_analysis['impact_scope']}")
        if initial_analysis.get('urgency'):
            content_lines.append(f"- 시급성: {initial_analysis['urgency']}")
        
        return "\n".join(content_lines)
    
    def _generate_department_opinions_section(self, analysis_results: Dict[str, Any]) -> str:
        """4. 유관 의견 섹션 생성"""
        opinions_lines = []
        
        # 관련 부서 정보
        relevant_depts = analysis_results.get('relevant_depts', [])
        if relevant_depts:
            opinions_lines.append("관련 부서:")
            for dept in relevant_depts[:3]:
                dept_name = dept.get('부서명', 'N/A')
                담당자 = dept.get('담당자', 'N/A')
                연락처 = dept.get('연락처', 'N/A')
                opinions_lines.append(f"- {dept_name} ({담당자}, {연락처})")
        
        opinions_lines.append("")
        
        # 사실 확인
        fact_verification = analysis_results.get('fact_verification', {})
        opinions_lines.append("- 사실 확인:")
        
        if fact_verification.get('fact_status'):
            opinions_lines.append(f"  상태: {fact_verification['fact_status']}")
        
        if fact_verification.get('credibility'):
            opinions_lines.append(f"  신뢰도: {fact_verification['credibility']}")
            
        if fact_verification.get('background_context'):
            background = fact_verification['background_context']
            if len(background) > 150:
                background = background[:150] + "..."
            opinions_lines.append(f"  배경: {background}")
        
        # 부서별 의견 (있는 경우)
        department_opinions = analysis_results.get('department_opinions', {})
        if department_opinions:
            opinions_lines.append("")
            opinions_lines.append("- 설명 논리:")
            for dept_name, opinion_data in department_opinions.items():
                if opinion_data.get('opinion'):
                    opinion_text = opinion_data['opinion'][:200] + "..." if len(opinion_data['opinion']) > 200 else opinion_data['opinion']
                    opinions_lines.append(f"  {dept_name}: {opinion_text}")
        
        return "\n".join(opinions_lines)
    
    def _generate_response_plan_section(self, analysis_results: Dict[str, Any]) -> str:
        """5. 대응 방안 섹션 생성"""
        response_lines = []
        
        pr_strategy = analysis_results.get('pr_strategy', {})
        
        # 원보이스 메시지
        response_lines.append("- 원보이스:")
        if pr_strategy.get('key_messages'):
            for message in pr_strategy['key_messages'][:3]:
                response_lines.append(f"  '{message}'")
        else:
            response_lines.append("  메시지 검토 중")
        
        response_lines.append("")
        
        # 대응 방향성
        response_lines.append("- 이후 대응 방향성:")
        if pr_strategy.get('immediate_actions'):
            for action in pr_strategy['immediate_actions'][:3]:
                response_lines.append(f"  - {action}")
        
        if pr_strategy.get('communication_tone'):
            response_lines.append(f"  - 커뮤니케이션 기조: {pr_strategy['communication_tone']}")
        
        # 주의사항
        fact_verification = analysis_results.get('fact_verification', {})
        if fact_verification.get('cautions'):
            response_lines.append("")
            response_lines.append("- 주의사항:")
            cautions = fact_verification['cautions']
            if isinstance(cautions, list):
                for caution in cautions[:2]:
                    response_lines.append(f"  - {caution}")
            else:
                response_lines.append(f"  - {cautions}")
        
        return "\n".join(response_lines)
    
    def _generate_similar_cases_section(self, analysis_results: Dict[str, Any]) -> str:
        """참조. 최근 유사 사례 섹션 생성"""
        similar_lines = []
        
        # 웹 검색 결과에서 유사 사례 추출
        web_search_results = analysis_results.get('web_search_results', {})
        
        if web_search_results.get('sources', {}).get('naver_news'):
            news_items = web_search_results['sources']['naver_news'][:2]
            for i, news in enumerate(news_items, 1):
                title = news.get('title', 'N/A')
                desc = news.get('description', '')[:100] + "..." if news.get('description') else ''
                similar_lines.append(f"{i}. {title}")
                if desc:
                    similar_lines.append(f"   요약: {desc}")
        else:
            similar_lines.append("1. 관련 보도사례 조사 중")
        
        similar_lines.append("")
        similar_lines.append("교훈 및 참고사항:")
        
        fact_verification = analysis_results.get('fact_verification', {})
        if fact_verification.get('similar_cases'):
            similar_lines.append(f"- {fact_verification['similar_cases']}")
        else:
            similar_lines.append("- 유사 사례 분석을 통한 대응 방향 수립 필요")
        
        return "\n".join(similar_lines)
    
    def _generate_issue_definition_section(self, analysis_results: Dict[str, Any]) -> str:
        """참조. 이슈 정의 및 개념 정립 섹션 생성"""
        definition_lines = []
        
        issue_description = analysis_results.get('issue_description', '')
        initial_analysis = analysis_results.get('initial_analysis', {})
        
        definition_lines.append(f"이슈 개념:")
        definition_lines.append(f"- {issue_description}")
        
        if initial_analysis.get('category'):
            definition_lines.append(f"- 분류: {initial_analysis['category']}")
        
        definition_lines.append("")
        definition_lines.append("경영/사회/법률적 함의:")
        
        fact_verification = analysis_results.get('fact_verification', {})
        if fact_verification.get('potential_impact'):
            impact = fact_verification['potential_impact']
            if len(impact) > 200:
                impact = impact[:200] + "..."
            definition_lines.append(f"- {impact}")
        else:
            definition_lines.append("- 잠재적 파급효과 분석 중")
        
        # 추가 확인 필요사항
        if fact_verification.get('additional_verification_needed'):
            definition_lines.append("")
            definition_lines.append("추가 확인 필요사항:")
            additional_items = fact_verification['additional_verification_needed']
            if isinstance(additional_items, list):
                for item in additional_items[:3]:
                    definition_lines.append(f"- {item}")
            else:
                definition_lines.append(f"- {additional_items}")
        
        return "\n".join(definition_lines)

def main():
    """테스트 함수"""
    # 테스트 데이터
    test_analysis_results = {
        'media_name': '조선일보',
        'reporter_name': '김기자',
        'issue_description': '포스코인터내셔널 2차전지 소재 배터리 결함 이슈',
        'crisis_level': '2단계(주의)',
        'initial_analysis': {
            'category': '제품 안전성',
            'impact_scope': '고객사 및 최종소비자',
            'urgency': '높음',
            'summary': '2차전지 소재 품질 문제로 인한 전기차 배터리 결함 가능성 제기'
        },
        'relevant_depts': [
            {'부서명': '품질보증팀', '담당자': '이과장', '연락처': '02-1234-5678'},
            {'부서명': '기술연구소', '담당자': '박박사', '연락처': '02-1234-5679'}
        ],
        'fact_verification': {
            'fact_status': '언론보도됨',
            'credibility': '높음',
            'background_context': '전기차 배터리 공급망 품질관리 이슈',
            'cautions': ['정확한 기술적 사실 확인 필수', '고객사와의 협의 필요']
        },
        'pr_strategy': {
            'key_messages': ['품질 최우선 정책 강조', '투명한 조사 진행'],
            'immediate_actions': ['기술진단팀 구성', '고객사 대응'], 
            'communication_tone': '신중하고 전문적인 접근'
        }
    }
    
    generator = StructuredReportGenerator()
    structured_report = generator.generate_structured_report(test_analysis_results)
    
    print("=== 구조화된 보고서 생성 테스트 ===")
    print(structured_report)
    
    # 파일로 저장
    output_file = f"structured_report_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(structured_report)
    
    print(f"\n테스트 결과 저장: {output_file}")

if __name__ == "__main__":
    main()