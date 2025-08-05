#!/usr/bin/env python3
"""
포스코인터내셔널 위기 커뮤니케이션 보고서 자동 생성 스크립트
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.openai_service import OpenAIService
from src.services.search_service import SearchService
from src.utils.logger import Logger

class ReportGenerator:
    """포스코인터내셔널 이슈 보고서 자동 생성기"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.openai_service = OpenAIService()
        self.search_service = SearchService()
        self.prompt_template = self._load_prompt_template()
        
        # 부서 매핑 테이블
        self.department_mapping = {
            "경영전략": {"부서": "경영전략그룹", "담당자": "서유리", "키워드": ["비전", "전략", "조직개편"]},
            "지속가능경영": {"부서": "지속가능경영그룹", "담당자": "이승진", "키워드": ["ESG", "지속가능성", "환경"]},
            "IR": {"부서": "IR그룹", "담당자": "유근석", "키워드": ["공시", "실적", "투자자", "주가"]},
            "HR": {"부서": "HR그룹", "담당자": "권택현", "키워드": ["인사", "채용", "조직문화"]},
            "대외협력": {"부서": "대외협력그룹", "담당자": "고영택", "키워드": ["정부", "유관기관", "협력"]},
            "철강": {"부서": "철강사업", "담당자": "김요섭", "키워드": ["철강", "생산", "공급망"]},
            "소재바이오": {"부서": "소재바이오", "담당자": "김준표", "키워드": ["2차전지", "바이오"]},
            "에너지": {"부서": "에너지정책", "담당자": "왕희훈", "키워드": ["정책", "에너지", "전환"]},
            "가스": {"부서": "가스사업", "담당자": "김승모", "키워드": ["LNG", "해외광구"]},
            "포모솔": {"부서": "포스코모빌리티솔루션", "담당자": "엄유나", "키워드": ["매각", "미래차", "부품"]},
            "삼척": {"부서": "삼척블루파워", "담당자": "장재영", "키워드": ["석탄화력", "지역사회"]},
            "홍보": {"부서": "홍보그룹", "담당자": "허성형", "키워드": ["그룹", "언론", "총괄"]}
        }
    
    def _load_prompt_template(self) -> str:
        """프롬프트 템플릿 로드"""
        try:
            prompt_file = project_root / "prompts" / "issue_report_prompt.txt"
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"프롬프트 템플릿 로드 실패: {e}")
            return self._get_fallback_template()
    
    def _get_fallback_template(self) -> str:
        """기본 프롬프트 템플릿"""
        return """포스코인터내셔널의 위기 대응 커뮤니케이션 보고서를 작성해주세요.
        
기사/이슈: {{ input_article }}
유사 사례: {{ similar_cases }}
위기 단계: {{ crisis_level }}
담당 부서: {{ department_suggestion }}
분석 일시: {{ today }}

위의 정보를 바탕으로 전문적인 이슈 발생 보고서를 작성해주세요."""
    
    def suggest_department(self, content: str) -> Dict[str, str]:
        """이슈 내용을 기반으로 담당 부서 추천"""
        content_lower = content.lower()
        scores = {}
        
        for dept_key, dept_info in self.department_mapping.items():
            score = 0
            for keyword in dept_info["키워드"]:
                if keyword.lower() in content_lower:
                    score += 1
            scores[dept_key] = score
        
        # 가장 높은 점수의 부서 선택
        best_dept = max(scores, key=scores.get) if scores else "홍보"
        dept_info = self.department_mapping[best_dept]
        
        return {
            "부서명": dept_info["부서"],
            "담당자": dept_info["담당자"],
            "추천이유": f"키워드 매칭 점수: {scores[best_dept]}"
        }
    
    def assess_crisis_level(self, content: str) -> str:
        """이슈 내용을 기반으로 위기 단계 평가"""
        content_lower = content.lower()
        
        # 위기 키워드 분석
        critical_keywords = ["사고", "피해", "소송", "조사", "규제위반", "시정명령"]
        major_keywords = ["논란", "의혹", "비판", "반발", "우려"]
        minor_keywords = ["문의", "질의", "확인", "설명"]
        
        critical_score = sum(1 for kw in critical_keywords if kw in content_lower)
        major_score = sum(1 for kw in major_keywords if kw in content_lower)
        minor_score = sum(1 for kw in minor_keywords if kw in content_lower)
        
        if critical_score >= 2:
            return "4단계 (비상)"
        elif critical_score >= 1 or major_score >= 2:
            return "3단계 (위기)"
        elif major_score >= 1:
            return "2단계 (주의)"
        else:
            return "1단계 (관심)"
    
    def search_similar_cases(self, content: str, top_k: int = 3) -> list:
        """유사 사례 검색"""
        try:
            similar_cases = self.search_service.search_similar_issues(content, top_k=top_k)
            return similar_cases
        except Exception as e:
            self.logger.error(f"유사 사례 검색 실패: {e}")
            return []
    
    def generate_report(self, user_input: Dict[str, str]) -> Dict[str, any]:
        """보고서 생성 메인 함수"""
        self.logger.info("보고서 생성 시작")
        
        try:
            # 입력 데이터 검증
            required_fields = ["발생_일시", "매체", "기자", "주요내용"]
            for field in required_fields:
                if field not in user_input:
                    raise ValueError(f"필수 입력 항목이 누락되었습니다: {field}")
            
            # 이슈 내용 구성
            input_article = f"""
발생 일시: {user_input['발생_일시']}
매체/기자: {user_input['매체']} / {user_input['기자']}
주요 내용: {user_input['주요내용']}
"""
            
            # 1. 위기 단계 자동 평가
            crisis_level = user_input.get('단계') or self.assess_crisis_level(user_input['주요내용'])
            
            # 2. 담당 부서 추천
            dept_info = self.suggest_department(user_input['주요내용'])
            department_suggestion = f"{dept_info['부서명']} / {dept_info['담당자']}"
            
            # 3. 유사 사례 검색
            similar_cases = self.search_similar_cases(user_input['주요내용'])
            similar_cases_text = "\n".join([
                f"- {case.get('이슈발생보고', str(case))[:100]}..." 
                for case in similar_cases[:3]
            ]) if similar_cases else "유사 사례가 없습니다."
            
            # 4. 프롬프트 구성
            filled_prompt = self.prompt_template.replace("{{ input_article }}", input_article)\
                                               .replace("{{ similar_cases }}", similar_cases_text)\
                                               .replace("{{ crisis_level }}", crisis_level)\
                                               .replace("{{ department_suggestion }}", department_suggestion)\
                                               .replace("{{ today }}", datetime.now().strftime('%Y-%m-%d %H:%M'))
            
            # 5. GPT 보고서 생성
            self.logger.info("GPT 보고서 생성 중...")
            report_content = self.openai_service.generate_issue_report(filled_prompt)
            
            # 결과 구성
            result = {
                "success": True,
                "input_data": user_input,
                "analysis": {
                    "crisis_level": crisis_level,
                    "suggested_department": dept_info,
                    "similar_cases_count": len(similar_cases)
                },
                "report_content": report_content,
                "generated_at": datetime.now().isoformat(),
                "similar_cases": similar_cases
            }
            
            self.logger.info("보고서 생성 완료")
            return result
            
        except Exception as e:
            error_msg = f"보고서 생성 실패: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    def save_report(self, result: Dict, output_file: Optional[str] = None) -> str:
        """보고서를 파일로 저장"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"reports/crisis_report_{timestamp}.txt"
        
        output_path = project_root / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 보고서 내용 구성
        report_text = f"""
=== 포스코인터내셔널 위기 커뮤니케이션 보고서 ===
생성 일시: {result['generated_at']}

📋 입력 정보:
- 발생 일시: {result['input_data']['발생_일시']}
- 매체/기자: {result['input_data']['매체']} / {result['input_data']['기자']}
- 주요 내용: {result['input_data']['주요내용']}

📊 자동 분석:
- 위기 단계: {result['analysis']['crisis_level']}
- 추천 부서: {result['analysis']['suggested_department']['부서명']} / {result['analysis']['suggested_department']['담당자']}
- 유사 사례: {result['analysis']['similar_cases_count']}건

📝 생성된 보고서:
{result['report_content']}

=== 보고서 끝 ===
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return str(output_path)

def interactive_mode():
    """대화형 보고서 생성 모드"""
    print("=" * 60)
    print("🏢 포스코인터내셔널 위기 커뮤니케이션 보고서 생성기")
    print("=" * 60)
    
    generator = ReportGenerator()
    
    while True:
        try:
            print("\n📝 이슈 정보를 입력해주세요:")
            
            # 사용자 입력 받기
            user_input = {}
            user_input['발생_일시'] = input("1. 발생 일시 (예: 2025.08.05 10:00): ").strip()
            user_input['매체'] = input("2. 매체명 (예: 이데일리): ").strip()
            user_input['기자'] = input("3. 기자명 (예: 김은경): ").strip()
            user_input['주요내용'] = input("4. 주요 내용: ").strip()
            
            # 선택적 입력
            manual_stage = input("5. 위기 단계 (선택사항, 자동분석 시 Enter): ").strip()
            if manual_stage:
                user_input['단계'] = manual_stage
            
            # 입력 검증
            if not all([user_input['발생_일시'], user_input['매체'], user_input['기자'], user_input['주요내용']]):
                print("❌ 필수 정보가 누락되었습니다. 다시 입력해주세요.")
                continue
            
            # 보고서 생성
            print("\n🔄 보고서 생성 중... (시간이 조금 걸릴 수 있습니다)")
            result = generator.generate_report(user_input)
            
            if result['success']:
                print("\n" + "=" * 60)
                print("📊 자동 분석 결과:")
                print(f"   위기 단계: {result['analysis']['crisis_level']}")
                print(f"   추천 부서: {result['analysis']['suggested_department']['부서명']} / {result['analysis']['suggested_department']['담당자']}")
                print(f"   유사 사례: {result['analysis']['similar_cases_count']}건")
                
                print("\n📋 생성된 보고서:")
                print("=" * 60)
                print(result['report_content'])
                print("=" * 60)
                
                # 파일 저장 옵션
                save_option = input("\n💾 보고서를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
                if save_option in ['y', 'yes', '예']:
                    saved_path = generator.save_report(result)
                    print(f"✅ 보고서가 저장되었습니다: {saved_path}")
            
            else:
                print(f"❌ 보고서 생성 실패: {result['error']}")
            
            # 계속 진행 여부
            continue_option = input("\n다른 보고서를 생성하시겠습니까? (y/n): ").strip().lower()
            if continue_option not in ['y', 'yes', '예']:
                break
                
        except KeyboardInterrupt:
            print("\n👋 프로그램을 종료합니다.")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

def example_usage():
    """사용 예시"""
    print("📖 사용 예시 실행 중...")
    
    generator = ReportGenerator()
    
    # 예시 입력 데이터 (알래스카 협업 문의)
    sample_input = {
        "발생_일시": "2025.08.05 13:00",
        "매체": "조선일보",
        "기자": "김지수",
        "주요내용": "포스코인터내셔널의 알래스카 미국 LNG 프로젝트 협업 관련하여 당사의 구체적인 협업 포인트와 투자 규모에 대한 문의"
    }
    
    print(f"📝 샘플 입력:")
    print(json.dumps(sample_input, ensure_ascii=False, indent=2))
    
    result = generator.generate_report(sample_input)
    
    if result['success']:
        print(f"\n✅ 보고서 생성 성공!")
        print(f"📊 분석 결과: {result['analysis']}")
        print(f"\n📋 생성된 보고서:")
        print("-" * 40)
        print(result['report_content'])
    else:
        print(f"❌ 예시 실행 실패: {result['error']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        example_usage()
    else:
        interactive_mode()
