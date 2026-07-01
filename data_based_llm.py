"""
데이터 기반 답변 생성 시스템
"""
import json
import pandas as pd
import os
from typing import Dict, List, Any, Optional
from llm_manager import LLMManager
from naver_search import IssueResearchService
try:
    from enhanced_research_service import EnhancedResearchService
    ENHANCED_RESEARCH_AVAILABLE = True
except ImportError:
    ENHANCED_RESEARCH_AVAILABLE = False

try:
    from optimized_web_research import OptimizedWebResearchService
    OPTIMIZED_RESEARCH_AVAILABLE = True
except ImportError:
    OPTIMIZED_RESEARCH_AVAILABLE = False

try:
    from quality_enhancer import QualityEnhancer
    QUALITY_ENHANCER_AVAILABLE = True
except ImportError:
    QUALITY_ENHANCER_AVAILABLE = False

class DataBasedLLM:
    """데이터 파일을 기반으로 답변을 생성하는 LLM 클래스"""
    
    def __init__(self, data_folder: str = "data", model: str = "gpt-4o"):
        """
        데이터 기반 LLM 초기화
        
        Args:
            data_folder (str): 데이터 파일들이 위치한 폴더 경로
            model (str): 사용할 OpenAI 모델
        """
        self.data_folder = data_folder
        self.llm = LLMManager(model, data_folder)  # data_folder 전달
        self.master_data = None
        self.media_response_data = None
        self.research_service = None
        
        # 웹 검색 서비스 초기화
        try:
            self.research_service = IssueResearchService()
            print("INIT: 웹 검색 서비스 초기화 완료")
        except Exception as e:
            print(f"WARNING: 웹 검색 서비스 초기화 실패: {str(e)}")
        
        # 강화된 웹 검색 서비스 초기화
        self.enhanced_research = None
        if ENHANCED_RESEARCH_AVAILABLE:
            try:
                self.enhanced_research = EnhancedResearchService()
                print("INIT: 강화된 웹 검색 서비스 초기화 완료")
            except Exception as e:
                print(f"WARNING: 강화된 웹 검색 서비스 초기화 실패: {str(e)}")
        
        # 최적화된 웹 검색 서비스 초기화
        self.optimized_research = None
        if OPTIMIZED_RESEARCH_AVAILABLE:
            try:
                self.optimized_research = OptimizedWebResearchService()
                print("INIT: 최적화된 웹 검색 서비스 초기화 완료")
            except Exception as e:
                print(f"WARNING: 최적화된 웹 검색 서비스 초기화 실패: {str(e)}")
        
        # 품질 개선 모듈 초기화
        self.quality_enhancer = None
        if QUALITY_ENHANCER_AVAILABLE:
            try:
                self.quality_enhancer = QualityEnhancer()
                print("INIT: 품질 개선 모듈 초기화 완료")
            except Exception as e:
                print(f"WARNING: 품질 개선 모듈 초기화 실패: {str(e)}")
        
        # 데이터 로드
        self._load_data()
    
    def _load_data(self):
        """데이터 파일들을 로드"""
        try:
            # master_data.json 로드
            master_path = os.path.join(self.data_folder, "master_data.json")
            if os.path.exists(master_path):
                with open(master_path, 'r', encoding='utf-8') as f:
                    self.master_data = json.load(f)
                print(f"LOAD: master_data.json 로드 완료")
            else:
                print(f"✗ master_data.json 파일을 찾을 수 없습니다: {master_path}")
            
            # 언론대응내역.csv 로드
            csv_path = os.path.join(self.data_folder, "언론대응내역.csv")
            if os.path.exists(csv_path):
                self.media_response_data = pd.read_csv(csv_path, encoding='utf-8')
                print(f"LOAD: 언론대응내역.csv 로드 완료 ({len(self.media_response_data)}건)")
            else:
                print(f"✗ 언론대응내역.csv 파일을 찾을 수 없습니다: {csv_path}")
                
        except Exception as e:
            print(f"✗ 데이터 로드 중 오류 발생: {str(e)}")
    
    def get_relevant_departments(self, query: str, use_ai_enhancement: bool = True) -> List[Dict]:
        """개선된 AI 기반 부서-이슈 매핑 시스템"""
        if not self.master_data or 'departments' not in self.master_data:
            return []
        
        # 1단계: 기본 키워드 매칭
        relevant_depts = self._basic_department_matching(query)
        
        # 2단계: AI 기반 시맨틱 매칭 (선택적)
        if use_ai_enhancement and len(relevant_depts) <= 1:
            ai_enhanced_depts = self._ai_enhanced_department_matching(query)
            # AI 결과와 기본 결과 통합
            relevant_depts = self._merge_department_results(relevant_depts, ai_enhanced_depts)
        
        # 3단계: 최종 정렬 및 필터링
        final_depts = self._finalize_department_selection(relevant_depts, query)
        
        return final_depts[:3]  # 상위 3개 부서 반환
    
    def _basic_department_matching(self, query: str) -> List[Dict]:
        """1단계: 기본 키워드 기반 부서 매칭 (개선된 알고리즘)"""
        relevant_depts = []
        query_lower = query.lower()
        
        # 쿼리 전처리 - 중요 키워드 추출
        key_terms = self._extract_key_terms(query_lower)
        
        for dept_name, dept_info in self.master_data['departments'].items():
            if not dept_info.get('활성상태', True):
                continue
                
            relevance_score = 0
            matched_items = []
            
            # 1) 부서명 직접 매칭 (가중치 8)
            if dept_name.lower() in query_lower:
                relevance_score += 8
                matched_items.append(f"부서명:{dept_name}")
            
            # 2) 담당이슈 정밀 매칭 (가중치 6)
            issues = dept_info.get('담당이슈', [])
            for issue in issues:
                issue_lower = issue.lower()
                # 완전 매칭
                if issue_lower in query_lower:
                    relevance_score += 6
                    matched_items.append(f"이슈:{issue}")
                # 부분 매칭 (키워드 포함)
                elif any(term in issue_lower for term in key_terms):
                    relevance_score += 3
                    matched_items.append(f"이슈(부분):{issue}")
            
            # 3) 키워드 가중치 매칭 (가중치 4)
            keywords = dept_info.get('키워드', '').split(', ')
            for keyword in keywords:
                if keyword.strip():
                    keyword_lower = keyword.strip().lower()
                    if keyword_lower in query_lower:
                        relevance_score += 4
                        matched_items.append(f"키워드:{keyword}")
                    elif any(term in keyword_lower for term in key_terms):
                        relevance_score += 2
                        matched_items.append(f"키워드(부분):{keyword}")
            
            # 4) 시맨틱 관련성 보너스
            semantic_bonus = self._calculate_semantic_bonus(query_lower, dept_info)
            relevance_score += semantic_bonus
            
            if relevance_score > 0:
                dept_info_copy = dept_info.copy()
                dept_info_copy['부서명'] = dept_name
                dept_info_copy['관련성점수'] = relevance_score
                dept_info_copy['매칭항목'] = matched_items
                relevant_depts.append(dept_info_copy)
        
        # 점수 기준 정렬
        relevant_depts.sort(key=lambda x: (-x['관련성점수'], x.get('우선순위', 999)))
        return relevant_depts
    
    def _extract_key_terms(self, query_lower: str) -> List[str]:
        """쿼리에서 핵심 키워드 추출"""
        # 불용어 제거
        stop_words = ['의', '에', '을', '를', '이', '가', '은', '는', '과', '와', '에서', '로', '으로', '관련', '대한', '에게', '한테']
        
        # 중요 키워드 패턴 정의
        important_patterns = [
            '2차전지', '배터리', '리튬', '전기차', 'esg', '환경', '미얀마', '가스전', 'lng', '터미널',
            '투자', '실적', '주가', '배당', '홍보', 'ir', '인사', '채용', '노사', '전략', 'ceo', '경영진',
            '소재', '바이오', '곡물', '팜유', '정책', '규제', '정부', '에너지', '신재생', '석탄', '발전',
            '모터코어', '자동차', '미래차', '솔루션', '모빌리티', '법인', '지사', '해외', '터키'
        ]
        
        # 쿼리에서 중요 패턴 추출
        key_terms = []
        for pattern in important_patterns:
            if pattern in query_lower:
                key_terms.append(pattern)
        
        # 일반적인 명사 추출 (간단한 휴리스틱)
        words = query_lower.split()
        for word in words:
            if len(word) >= 2 and word not in stop_words:
                if word not in key_terms:  # 중복 제거
                    key_terms.append(word)
        
        return key_terms[:5]  # 상위 5개만 사용
    
    def _calculate_semantic_bonus(self, query_lower: str, dept_info: Dict) -> float:
        """부서와 쿼리 간 시맨틱 관련성 보너스 계산"""
        bonus = 0
        
        # 부서별 특화 도메인 정의
        dept_domains = {
            'IR그룹': ['주식', '투자자', '재무', '공시', '배당', '수익', '주주', '펀더멘털'],
            '에너지정책그룹': ['전력', '가스', '석유', '재생에너지', '정책', '규제'],
            '가스사업운영섹션': ['탐사', '생산', '광구', 'e&p', '석유가스'],
            '소재바이오사업운영섹션': ['신소재', '첨단소재', '바이오매스', '식품', '농업'],
            '지속가능경영그룹': ['지속가능성', '탄소중립', '친환경', '사회책임'],
            '포스코모빌리티솔루션': ['자동차산업', '부품', '완성차', 'oem']
        }
        
        dept_name = dept_info.get('부서명', '')
        if dept_name in dept_domains:
            domain_keywords = dept_domains[dept_name]
            for keyword in domain_keywords:
                if keyword in query_lower:
                    bonus += 1.5
        
        return bonus
    
    def _ai_enhanced_department_matching(self, query: str) -> List[Dict]:
        """2단계: AI 기반 시맨틱 부서 매핑"""
        
        # 부서 정보를 AI가 이해할 수 있는 형태로 구성
        dept_descriptions = []
        for dept_name, dept_info in self.master_data['departments'].items():
            if not dept_info.get('활성상태', True):
                continue
                
            description = f"""
부서: {dept_name}
담당자: {dept_info.get('담당자', 'N/A')}
담당이슈: {', '.join(dept_info.get('담당이슈', []))}
키워드: {dept_info.get('키워드', 'N/A')}
우선순위: {dept_info.get('우선순위', 'N/A')}
            """.strip()
            dept_descriptions.append(description)
        
        # AI 기반 부서 추천 프롬프트
        ai_prompt = f"""
        다음 이슈에 대해 가장 적합한 담당 부서 2-3개를 추천해주세요:
        
        이슈: {query}
        
        === 부서 정보 ===
        {chr(10).join(dept_descriptions)}
        
        추천 기준:
        1. 담당 이슈와의 직접적 연관성
        2. 부서의 전문성과 책임 범위  
        3. 과거 유사 사례 처리 경험
        
        응답 형식: 부서명1, 부서명2, 부서명3 (추천 순서대로)
        추가 설명은 하지 말고 부서명만 콤마로 구분하여 답변하세요.
        """
        
        try:
            ai_response = self.llm.chat(
                ai_prompt,
                system_prompt="당신은 포스코인터내셔널의 조직 전문가입니다. 이슈의 성격을 파악하여 가장 적합한 담당 부서를 추천해주세요.",
                temperature=0.2
            )
            
            # AI 응답에서 부서명 추출
            recommended_depts = self._extract_departments_from_ai_response(ai_response)
            return recommended_depts
            
        except Exception as e:
            print(f"AI 기반 부서 매핑 중 오류: {str(e)}")
            return []
    
    def _extract_departments_from_ai_response(self, response: str) -> List[Dict]:
        """AI 응답에서 부서명 추출하여 부서 정보 반환"""
        recommended_depts = []
        
        if not response:
            return recommended_depts
        
        # 응답에서 부서명 추출
        dept_names = [name.strip() for name in response.split(',')]
        
        for i, dept_name in enumerate(dept_names[:3]):  # 최대 3개
            if dept_name in self.master_data['departments']:
                dept_info = self.master_data['departments'][dept_name].copy()
                dept_info['부서명'] = dept_name
                dept_info['관련성점수'] = 10 - i * 2  # AI 추천 순서에 따른 점수
                dept_info['매칭항목'] = ['AI추천']
                recommended_depts.append(dept_info)
        
        return recommended_depts
    
    def _merge_department_results(self, basic_results: List[Dict], ai_results: List[Dict]) -> List[Dict]:
        """기본 매칭과 AI 매칭 결과 통합"""
        merged = {}
        
        # 기본 결과 추가
        for dept in basic_results:
            dept_name = dept['부서명']
            merged[dept_name] = dept
        
        # AI 결과 통합 (기존 부서는 점수 보정, 새 부서는 추가)
        for dept in ai_results:
            dept_name = dept['부서명']
            if dept_name in merged:
                # 기존 부서의 점수 보정 (AI 추천 보너스)
                merged[dept_name]['관련성점수'] += 3
                merged[dept_name]['매칭항목'].append('AI추천')
            else:
                # 새 부서 추가
                merged[dept_name] = dept
        
        return list(merged.values())
    
    def _finalize_department_selection(self, departments: List[Dict], query: str) -> List[Dict]:
        """최종 부서 선정 및 정렬"""
        
        if not departments:
            # 기본 부서 제공
            default_depts = ['IR그룹', '홍보그룹', '경영전략그룹']
            for dept_name in default_depts:
                if dept_name in self.master_data['departments']:
                    dept_info = self.master_data['departments'][dept_name].copy()
                    dept_info['부서명'] = dept_name
                    dept_info['관련성점수'] = 1
                    dept_info['매칭항목'] = ['기본부서']
                    departments.append(dept_info)
                    break
        
        # 최종 정렬: 관련성점수 > 우선순위 > 부서명
        departments.sort(key=lambda x: (
            -x['관련성점수'], 
            x.get('우선순위', 999),
            x['부서명']
        ))
        
        return departments
    
    def search_media_responses(self, query: str, limit: int = 10) -> pd.DataFrame:
        """언론대응내역에서 관련 케이스 검색"""
        if self.media_response_data is None:
            return pd.DataFrame()
        
        query_lower = query.lower()
        
        # 이슈 발생 보고 컬럼에서 검색
        mask = self.media_response_data['이슈 발생 보고'].str.lower().str.contains(
            query_lower, na=False, regex=False
        )
        
        relevant_cases = self.media_response_data[mask].head(limit)
        
        return relevant_cases
    
    def get_recent_cases_by_type(self, case_type: str = None, limit: int = 5) -> pd.DataFrame:
        """최근 사례들을 유형별로 검색"""
        if self.media_response_data is None:
            return pd.DataFrame()
        
        df = self.media_response_data.copy()
        
        if case_type:
            df = df[df['발생 유형'] == case_type]
        
        # 최근 데이터부터 정렬 (발생 일시 기준)
        df = df.sort_values('발생 일시', ascending=False)
        
        return df.head(limit)
    
    def generate_data_based_response(self, query: str) -> str:
        """데이터를 기반으로 답변 생성"""
        
        # 1. 관련 부서 정보 수집
        relevant_depts = self.get_relevant_departments(query)
        
        # 2. 관련 언론대응 사례 수집
        relevant_cases = self.search_media_responses(query)
        
        # 3. 최근 사례들 수집
        recent_cases = self.get_recent_cases_by_type(limit=3)
        
        # 4. 컨텍스트 구성
        context = self._build_context(query, relevant_depts, relevant_cases, recent_cases)
        
        # 5. LLM에 전달할 프롬프트 구성 (총괄 프롬프트 자동 사용)
        prompt = f"""
        질문: {query}
        
        관련 데이터:
        {context}
        
        위 데이터를 참고하여 질문에 대한 종합적이고 구체적인 답변을 제공해주세요.
        
        다음 사항을 포함하여 상세히 답변해주세요:
        1. 관련 부서 정보와 각 부서의 구체적 역할 및 책임
        2. 과거 유사 사례의 대응 방법과 결과 분석
        3. 단계별 구체적인 조치사항과 실행 계획
        4. 예상되는 리스크와 구체적인 완화 방안
        5. 중립적이고 객관적인 커뮤니케이션 방향성
        6. 실행 가능한 타임라인과 성과 측정 방법
        
        답변은 구체적인 사례와 근거를 바탕으로 작성하되, 전문적이고 실용적인 조언을 제공해주세요.
        """
        
        return self.llm.chat(prompt)  # 시스템 프롬프트 제거
    
    def generate_enhanced_response_with_fact_check(self, query: str) -> str:
        """강화된 웹 검색 기반 사실검증과 대응방안 포함 답변 생성"""
        
        if not self.enhanced_research:
            print("WARNING: 강화된 웹 검색 기능을 사용할 수 없습니다. 기본 답변을 생성합니다.")
            return self.generate_data_based_response(query)
        
        print("START: 강화된 웹 검색 기반 종합 분석을 시작합니다...")
        
        try:
            # 1. 종합 이슈 분석 수행
            comprehensive_analysis = self.enhanced_research.comprehensive_issue_analysis(query)
            
            # 2. 기존 데이터 기반 정보도 함께 수집
            relevant_depts = self.get_relevant_departments(query)
            relevant_cases = self.search_media_responses(query)
            
            # 3. 강화된 답변 생성 프롬프트 구성
            enhanced_prompt = self._build_enhanced_response_prompt(
                query, comprehensive_analysis, relevant_depts, relevant_cases
            )
            
            # 4. LLM을 통한 최종 답변 생성
            final_response = self.llm.chat(enhanced_prompt)
            
            return final_response
            
        except Exception as e:
            print(f"강화된 분석 중 오류 발생: {str(e)}")
            return self.generate_data_based_response(query)
    
    def _build_enhanced_response_prompt(self, query: str, analysis: Dict, 
                                      relevant_depts: List[Dict], relevant_cases) -> str:
        """강화된 답변 생성을 위한 프롬프트 구성"""
        
        fact_verification = analysis.get('fact_verification')
        response_strategy = analysis.get('response_strategy')
        research_data = analysis.get('research_data', {})
        
        # 사실검증 정보 요약
        fact_summary = f"""
=== 사실검증 결과 ===
확인 상태: {fact_verification.fact_status}
신뢰도: {fact_verification.confidence_score:.2f}
검증 근거: {len(fact_verification.evidence_sources)}개 소스
모순사항: {', '.join(fact_verification.contradictions) if fact_verification.contradictions else '없음'}
추가 검증사항: {fact_verification.verification_notes}
        """.strip()
        
        # 대응전략 요약
        strategy_summary = f"""
=== 권고 대응전략 ===
위기수준: {response_strategy.crisis_level}
커뮤니케이션 톤: {response_strategy.communication_tone}

즉시 조치사항 (24시간 내):
{chr(10).join([f"• {action}" for action in response_strategy.immediate_actions[:5]])}

단기 전략 (1주일 내):
{chr(10).join([f"• {action}" for action in response_strategy.short_term_strategy[:5]])}

장기 전략 (1개월 내):
{chr(10).join([f"• {action}" for action in response_strategy.long_term_strategy[:3]])}

핵심 이해관계자: {', '.join(response_strategy.stakeholders)}
성과 측정지표: {', '.join(response_strategy.success_metrics)}
        """.strip()
        
        # 관련 부서 정보
        dept_info = ""
        if relevant_depts:
            dept_info = "=== 관련 부서 정보 ===\n"
            for dept in relevant_depts[:3]:
                dept_info += f"""
부서: {dept.get('부서명', 'N/A')}
담당자: {dept.get('담당자', 'N/A')}
연락처: {dept.get('연락처', 'N/A')}
이메일: {dept.get('이메일', 'N/A')}
담당영역: {', '.join(dept.get('담당이슈', []))}
                """.strip() + "\n"
        
        # 웹 검색 결과 요약
        web_research_summary = f"""
=== 웹 검색 결과 요약 ===
뉴스 기사: {len(research_data.get('news_results', []))}건
블로그 게시물: {len(research_data.get('blog_results', []))}건
보도 수준: {research_data.get('analysis_summary', {}).get('coverage_level', 'N/A')}
        """.strip()
        
        # 최종 프롬프트 구성
        enhanced_prompt = f"""
        다음 이슈에 대해 사실검증 결과와 전략적 대응방안을 포함한 종합적인 답변을 작성해주세요:
        
        질문: {query}
        
        {fact_summary}
        
        {strategy_summary}
        
        {dept_info}
        
        {web_research_summary}
        
        다음 구조로 전문적이고 실행 가능한 답변을 작성해주세요:
        
        1. **이슈 개요 및 현황**
           - 이슈의 정확한 정의와 현재 상황
           - 사실관계 확인 결과 및 신뢰도
        
        2. **사실 검증 및 분석**
           - 확인된 사실과 미확인 정보 구분
           - 상충되는 정보나 주의사항
           - 추가 확인이 필요한 사항
        
        3. **관련 부서 및 담당자**
           - 주 담당 부서와 연락처
           - 각 부서의 역할과 책임
           - 협업이 필요한 부서들
        
        4. **유관 의견 (전문가 관점)**
           - 업계 전문가 시각
           - 유사 사례 벤치마킹
           - 리스크와 기회 요인 분석
        
        5. **단계별 대응 방안**
           - 즉시 조치사항 (24시간 내)
           - 단기 대응전략 (1주일 내)  
           - 장기 대응전략 (1개월 내)
           - 각 단계별 구체적 실행계획
        
        6. **커뮤니케이션 전략**
           - 권고 커뮤니케이션 톤앤매너
           - 핵심 메시지 포인트
           - 이해관계자별 소통 방안
        
        7. **모니터링 및 성과 측정**
           - 주요 모니터링 지표
           - 성과 측정 방법
           - 예상 타임라인
        
        답변은 구체적이고 실행 가능하며, 경영진이 즉시 의사결정할 수 있도록 명확하게 작성해주세요.
        전문 용어는 적절히 사용하되, 이해하기 쉽게 설명을 포함해주세요.
        """
        
        return enhanced_prompt
    
    def generate_optimized_response_with_fact_check(self, query: str, show_progress: bool = True) -> str:
        """최적화된 웹 검색 기반 고속 사실검증과 대응방안 포함 답변 생성"""
        
        if not self.optimized_research:
            print("WARNING: 최적화된 웹 검색 기능을 사용할 수 없습니다. 강화된 버전을 시도합니다.")
            return self.generate_enhanced_response_with_fact_check(query)
        
        # 진행률 콜백 설정
        if show_progress:
            def progress_callback(step: str, progress: int):
                print(f"⏩ {step} ({progress}%)")
            self.optimized_research.set_progress_callback(progress_callback)
        
        print("START: 최적화된 고속 분석을 시작합니다...")
        
        try:
            import time
            start_time = time.time()
            
            # 1. 최적화된 종합 이슈 분석 수행
            comprehensive_analysis = self.optimized_research.optimized_comprehensive_analysis(query)
            
            # 2. 기존 데이터 기반 정보도 함께 수집 (캐시된 버전)
            relevant_depts = self.get_relevant_departments(query)
            
            # 3. 최적화된 답변 생성 프롬프트 구성
            optimized_prompt = self._build_optimized_response_prompt(
                query, comprehensive_analysis, relevant_depts
            )
            
            # 4. LLM을 통한 최종 답변 생성 (캐시된 버전)
            final_response = self.llm.chat(optimized_prompt)
            
            processing_time = time.time() - start_time
            cache_status = comprehensive_analysis.get('cache_status', {})
            
            # 성능 정보 추가
            performance_info = f"""
            
📊 **성능 정보**
- 총 처리시간: {processing_time:.2f}초
- 메모리 캐시 항목: {cache_status.get('memory_cache_size', 0)}개
- 분석 처리시간: {comprehensive_analysis.get('processing_time', 0)}초
            """
            
            return final_response + performance_info
            
        except Exception as e:
            print(f"최적화된 분석 중 오류 발생: {str(e)}")
            return self.generate_enhanced_response_with_fact_check(query)
    
    def _build_optimized_response_prompt(self, query: str, analysis: Dict, 
                                       relevant_depts: List[Dict]) -> str:
        """최적화된 답변 생성을 위한 프롬프트 구성"""
        
        fact_verification = analysis.get('fact_verification', {})
        crisis_assessment = analysis.get('crisis_assessment', {})
        response_strategy = analysis.get('response_strategy', {})
        research_data = analysis.get('research_data', {})
        
        # 사실검증 정보 요약 (간소화)
        fact_summary = f"""
=== 사실검증 결과 ===
확인 상태: {fact_verification.get('fact_status', '미확인')}
신뢰도: {fact_verification.get('confidence_score', 0.5):.2f}
핵심 발견: {', '.join(fact_verification.get('key_findings', ['분석 중']))}
        """.strip()
        
        # 위기평가 요약
        crisis_summary = f"""
=== 위기수준 평가 ===
위기수준: {crisis_assessment.get('crisis_level', '주의')}
긴급도: {crisis_assessment.get('urgency_score', 5)}/10
영향평가: {crisis_assessment.get('impact_assessment', '검토 중')}
        """.strip()
        
        # 대응전략 요약 (최적화)
        strategy_summary = f"""
=== 권고 대응전략 ===
즉시 조치: {', '.join(response_strategy.get('immediate_actions', ['상황 모니터링'])[:3])}
단기 전략: {', '.join(response_strategy.get('short_term_strategy', ['대응 검토'])[:3])}
장기 전략: {', '.join(response_strategy.get('long_term_strategy', ['지속 관찰'])[:2])}
핵심 이해관계자: {', '.join(response_strategy.get('key_stakeholders', ['내부 관계자']))}
커뮤니케이션 톤: {response_strategy.get('communication_tone', '신중한 대응')}
        """.strip()
        
        # 관련 부서 정보 (간소화)
        dept_info = ""
        if relevant_depts:
            dept_info = "=== 관련 부서 정보 ===\n"
            for dept in relevant_depts[:2]:  # 최대 2개 부서만
                dept_info += f"{dept.get('부서명', 'N/A')}: {dept.get('담당자', 'N/A')} ({dept.get('연락처', 'N/A')})\n"
        
        # 웹 검색 결과 요약 (간소화)
        web_summary = f"""
=== 검색 결과 요약 ===
수집 정보: 뉴스 {len(research_data.get('news_results', []))}건, 블로그 {len(research_data.get('blog_results', []))}건
보도 수준: {research_data.get('analysis_summary', {}).get('coverage_level', 'N/A')}
        """.strip()
        
        # 최적화된 프롬프트 (간결하고 명확한 구조)
        optimized_prompt = f"""
        다음 이슈에 대해 신속하고 정확한 대응방안을 제시해주세요:
        
        질문: {query}
        
        {fact_summary}
        
        {crisis_summary}
        
        {strategy_summary}
        
        {dept_info}
        
        {web_summary}
        
        다음 구조로 간결하고 실행 가능한 답변을 작성해주세요:
        
        ## 1. 📋 이슈 요약
        - 현재 상황 및 사실관계
        - 위기수준과 긴급도
        
        ## 2. 🔍 사실 검증
        - 확인된 정보와 미확인 정보
        - 추가 확인 필요사항
        
        ## 3. 👥 담당 부서
        - 주 담당부서와 연락처
        - 협업 부서
        
        ## 4. 💭 전문가 의견
        - 업계 관점 및 유사사례
        - 리스크와 기회 요인
        
        ## 5. ⚡ 즉시 대응방안
        - 24시간 내 조치사항
        - 담당자 및 실행계획
        
        ## 6. 📈 단기/장기 전략
        - 1주일 내 단기전략
        - 1개월 내 장기전략
        
        ## 7. 📢 커뮤니케이션 가이드
        - 권고 메시지 톤
        - 이해관계자별 소통방안
        
        답변은 구체적이고 실행 가능하도록 작성하며, 핵심만 간결하게 포함해주세요.
        """
        
        return optimized_prompt
    
    def clear_all_caches(self):
        """모든 캐시 초기화"""
        if self.optimized_research:
            self.optimized_research.clear_cache()
            print("🧹 최적화 캐시가 초기화되었습니다.")
        else:
            print("WARNING: 캐시 시스템을 사용할 수 없습니다.")
    
    def _build_context(self, query: str, relevant_depts: List[Dict], 
                      relevant_cases: pd.DataFrame, recent_cases: pd.DataFrame) -> str:
        """답변 생성을 위한 컨텍스트 구성"""
        context_parts = []
        
        # 관련 부서 정보
        if relevant_depts:
            context_parts.append("=== 관련 부서 정보 ===")
            for dept in relevant_depts:
                dept_info = f"""
부서: {dept.get('부서명', 'N/A')}
담당자: {dept.get('담당자', 'N/A')}
연락처: {dept.get('연락처', 'N/A')}
이메일: {dept.get('이메일', 'N/A')}
담당이슈: {', '.join(dept.get('담당이슈', []))}
우선순위: {dept.get('우선순위', 'N/A')}
                """.strip()
                context_parts.append(dept_info)
        
        # 관련 언론대응 사례
        if not relevant_cases.empty:
            context_parts.append("\n=== 관련 언론대응 사례 ===")
            for _, case in relevant_cases.iterrows():
                case_info = f"""
일시: {case.get('발생 일시', 'N/A')}
유형: {case.get('발생 유형', 'N/A')}
단계: {case.get('단계', 'N/A')}
이슈: {case.get('이슈 발생 보고', 'N/A')}
결과: {case.get('대응 결과', 'N/A')}
                """.strip()
                context_parts.append(case_info)
        
        # 최근 사례들
        if not recent_cases.empty:
            context_parts.append("\n=== 최근 대응 사례 ===")
            for _, case in recent_cases.head(3).iterrows():
                case_info = f"""
일시: {case.get('발생 일시', 'N/A')}
유형: {case.get('발생 유형', 'N/A')}
이슈: {case.get('이슈 발생 보고', 'N/A')}
                """.strip()
                context_parts.append(case_info)
        
        return "\n\n".join(context_parts)
    
    def analyze_issue_trends(self, days: int = 30) -> str:
        """이슈 트렌드 분석"""
        if self.media_response_data is None:
            return "데이터가 없어 트렌드 분석을 할 수 없습니다."
        
        # 최근 데이터 필터링 (간단하게 최근 N개 레코드로 대체)
        recent_data = self.media_response_data.tail(days)
        
        # 유형별 집계
        type_counts = recent_data['발생 유형'].value_counts()
        stage_counts = recent_data['단계'].value_counts()
        
        trend_context = f"""
=== 최근 {days}건 이슈 트렌드 분석 ===

발생 유형별 분포:
{type_counts.to_string()}

단계별 분포:
{stage_counts.to_string()}

총 건수: {len(recent_data)}건
        """
        
        prompt = f"""
        다음 데이터를 바탕으로 최근 이슈 트렌드를 분석하고 시사점을 제시해주세요:
        
        {trend_context}
        """
        
        return self.llm.chat(prompt, "당신은 리스크 관리 및 이슈 분석 전문가입니다.")
    
    def recommend_response_strategy(self, issue_description: str) -> str:
        """이슈 설명을 바탕으로 대응 전략 추천"""
        
        # 유사 사례 검색
        similar_cases = self.search_media_responses(issue_description, limit=5)
        
        # 관련 부서 찾기
        relevant_depts = self.get_relevant_departments(issue_description)
        
        context = self._build_context(issue_description, relevant_depts, similar_cases, pd.DataFrame())
        
        prompt = f"""
        다음 이슈에 대한 대응 전략을 추천해주세요:
        
        이슈 설명: {issue_description}
        
        참고 데이터:
        {context}
        
        다음 항목들을 포함하여 답변해주세요:
        1. 이슈의 심각도 평가 (1-5점)
        2. 주관 부서 및 담당자 연락처
        3. 즉시 조치사항
        4. 단계별 대응 계획
        5. 유사 사례 대응 결과 참조
        6. 예상 리스크 및 완화 방안
        """
        
        return self.llm.chat(prompt)  # 총괄 프롬프트 자동 사용
    
    
    
    
    
    
    
    
    
    
    def _generate_fallback_report(self, media_name: str, reporter_name: str, 
                                issue_description: str, error_msg: str) -> str:
        """에러 시 폴백 보고서"""
        
        current_time = self._get_current_time()
        
        return f"""<이슈 발생 보고>

1. 발생 일시: {current_time}

2. 발생 단계: 2단계(주의)

3. 발생 내용:
({media_name} {reporter_name})
{issue_description}

4. 유관 의견:
- 사실 확인: 관련 부서에서 사실 관계 확인 진행 중
- 설명 논리: 정확한 정보 파악 후 투명하고 성실한 소통 예정
- 메시지 방향성: 신중하고 책임감 있는 대응

5. 대응 방안:
- 원보이스: '정확한 사실 확인을 통해 성실하게 대응하겠습니다'
- 이후 대응 방향성: 
  - 관련 부서 긴급 회의 소집
  - 추가 정보 수집 및 분석

6. 대응 결과: (추후 업데이트)

참조. 최근 유사 사례 (1년 이내):
- 관련 사례 조사 중

참조. 이슈 정의 및 개념 정립:
- 개념: 기업 운영 과정에서 발생한 이슈 상황
- 경영/사회/법률적 함의: 기업 신뢰도 및 운영에 미치는 영향 분석 필요

※ 주의: 시스템 처리 중 일시적 문제로 간소화된 보고서가 생성되었습니다.
상세 분석이 필요한 경우 재실행하시거나 표준 모드를 사용하시기 바랍니다.
"""
    
    def generate_issue_report(self, media_name: str, reporter_name: str, issue_description: str) -> str:
        """이슈 발생 보고서 생성 — 단일 합성(single-synthesis) 파이프라인.

        실제 데이터(유관부서/위기단계 기준/유사사례/언론사정보/실시간 웹검색)를 모두 수집해
        하나의 강력한 프롬프트로 LLM에 위임한다. 가짜 부서·고정문구·'분석 금지' 폴백을 제거.
        """
        # 1) 입력 검증
        if not self._validate_inputs(media_name, reporter_name, issue_description):
            return "입력값이 부족합니다. 언론사·기자명은 2자 이상, 이슈 내용은 10자 이상 입력해주세요."

        try:
            # 2) 실제 컨텍스트 수집
            relevant_depts = self.get_relevant_departments_from_master_data(issue_description)
            crisis_hint = self._assess_crisis_level_from_master_data(issue_description)
            media_info = self._get_media_info_from_master_data(media_name)
            similar_cases = self._collect_similar_cases(issue_description, media_name, limit=5)

            # 3) 실시간 웹 검색 (항상 수행) — 실패 시 graceful degrade
            try:
                web_results = self._conduct_web_research(issue_description, {})
            except Exception as e:
                print(f"WARNING: 웹 검색 실패, 내부 데이터로 진행: {str(e)}")
                web_results = {"sources": {}, "search_summary": "웹 검색 미수행"}

            # 4) 단일 합성 프롬프트 구성 후 보고서 생성
            prompt = self._build_issue_report_prompt(
                media_name=media_name,
                reporter_name=reporter_name,
                issue_description=issue_description,
                relevant_depts=relevant_depts,
                crisis_hint=crisis_hint,
                media_info=media_info,
                similar_cases=similar_cases,
                web_results=web_results,
            )

            # 시스템 프롬프트는 risk_report.txt(총괄 프롬프트) 자동 사용.
            # 보고서는 일관성이 중요하므로 temperature를 낮추고 충분한 토큰을 확보한다.
            return self.llm.chat(prompt, temperature=0.3, max_tokens=3000)

        except Exception as e:
            print(f"ERROR: 이슈 보고서 생성 실패: {str(e)}")
            return self._generate_fallback_report(media_name, reporter_name, issue_description, str(e))

    def _collect_similar_cases(self, issue_description: str, media_name: str, limit: int = 5) -> list:
        """언론대응내역.csv에서 유사 과거 사례 수집 (키워드 + 언론사 기반)."""
        if self.media_response_data is None or self.media_response_data.empty:
            return []

        df = self.media_response_data
        issue_col = "이슈 발생 보고" if "이슈 발생 보고" in df.columns else None
        if not issue_col:
            return []

        collected = []
        seen = set()

        def _add(row):
            key = str(row.get("순번", row.name))
            if key in seen:
                return
            seen.add(key)
            collected.append({
                "일시": str(row.get("발생 일시", "")).strip(),
                "유형": str(row.get("발생 유형", "")).strip(),
                "단계": str(row.get("단계", "")).strip(),
                "부서": str(row.get("현업 부서", "")).strip(),
                "이슈": str(row.get(issue_col, "")).strip(),
                "결과": str(row.get("대응 결과", "")).strip(),
            })

        # 1) 키워드 기반 매칭
        key_terms = self._extract_key_terms(issue_description.lower())
        for term in key_terms:
            if len(term) < 2:
                continue
            try:
                mask = df[issue_col].astype(str).str.lower().str.contains(term, na=False, regex=False)
                for _, row in df[mask].iterrows():
                    _add(row)
            except Exception:
                continue

        # 2) 언론사 기반 매칭 (정규화 검색)
        try:
            media_cases = self._search_by_media(media_name, limit=limit)
            for _, row in media_cases.iterrows():
                _add(row)
        except Exception:
            pass

        # 최근순 정렬 후 상위 N건
        def _date_key(c):
            return c.get("일시", "")
        collected.sort(key=_date_key, reverse=True)
        return collected[:limit]

    def _format_departments_block(self, relevant_depts: list) -> str:
        """프롬프트용 유관부서 블록 (master_data 실제 정보만)."""
        if not relevant_depts:
            return "=== 유관 부서 ===\n(매칭된 부서 없음 — 기본 대응부서: 홍보그룹)"
        lines = ["=== 유관 부서 (master_data.json 자동 매핑 / 실제 정보) ==="]
        for i, d in enumerate(relevant_depts[:3], 1):
            issues = ", ".join(d.get("담당이슈", [])[:5])
            lines.append(
                f"{i}. {d.get('부서명', 'N/A')} | 담당자: {d.get('담당자', 'N/A')} "
                f"| 연락처: {d.get('연락처', 'N/A')} | 이메일: {d.get('이메일', 'N/A')} "
                f"| 담당영역: {issues}"
            )
        return "\n".join(lines)

    def _format_crisis_block(self, crisis_hint: str) -> str:
        """프롬프트용 위기단계 분류 기준 블록 (정의+예시)."""
        levels = (self.master_data or {}).get("crisis_levels", {})
        if not levels:
            return ""
        lines = ["=== 위기 단계 분류 기준 (master_data.json) ==="]
        for name, info in levels.items():
            examples = ", ".join(info.get("예시", [])[:4])
            lines.append(f"- {name}: {info.get('정의', '')} (예: {examples})")
        lines.append(f"(참고) 키워드 기반 1차 추정: {crisis_hint}. 단 이는 참고용이며, 작성 요구사항 2번의 원칙"
                     f"(부정·리스크 요소 없는 단순 문의=1단계)을 우선 적용해 최종 확정하십시오.")
        return "\n".join(lines)

    def _format_similar_cases_block(self, similar_cases: list) -> str:
        """프롬프트용 유사사례 블록."""
        if not similar_cases:
            return "=== 과거 유사 대응 사례 (언론대응내역) ===\n(매칭되는 과거 사례 없음)"
        lines = ["=== 과거 유사 대응 사례 (언론대응내역.csv / 실제 이력) ==="]
        for c in similar_cases:
            issue_txt = c["이슈"][:120] + ("…" if len(c["이슈"]) > 120 else "")
            result_txt = c["결과"][:120] + ("…" if len(c["결과"]) > 120 else "")
            lines.append(f"- [{c['일시']} | {c['유형']} | {c['단계']} | {c['부서']}] {issue_txt}")
            if result_txt:
                lines.append(f"    └ 대응결과: {result_txt}")
        return "\n".join(lines)

    def _format_media_block(self, media_name: str, media_info: dict) -> str:
        """프롬프트용 언론사 정보 블록."""
        if not media_info:
            return f"=== 언론사 정보 ===\n{media_name}: 내부 DB에 등록 정보 없음"
        reporters = media_info.get("출입기자", [])
        reporter_names = ", ".join([r.get("이름", "") for r in reporters[:5] if isinstance(r, dict)])
        return (
            "=== 언론사 정보 (master_data.json) ===\n"
            f"{media_name} | 구분: {media_info.get('구분', 'N/A')} "
            f"| 당사 담당자: {media_info.get('담당자', 'N/A')} "
            f"| 출입기자({len(reporters)}명): {reporter_names}"
        )

    def _collect_gold_examples(self, issue_description: str, limit: int = 2) -> list:
        """실제 작성된 구조화 '이슈 발생 보고'를 문체·깊이 few-shot으로 수집.
        (언론대응내역.csv의 템플릿 구조 보고 중 이슈와 주제가 유사한 것 우선)"""
        if self.media_response_data is None or self.media_response_data.empty:
            return []
        df = self.media_response_data
        col = "이슈 발생 보고" if "이슈 발생 보고" in df.columns else None
        if not col:
            return []
        s = df[col].astype(str)
        structured = df[s.str.contains("유관 의견|대응 방안|발생 내용", regex=True)
                        & s.str.len().between(200, 1100)]
        if structured.empty:
            return []
        terms = [t for t in self._extract_key_terms(issue_description.lower()) if len(t) >= 2]

        def _score(txt):
            t = str(txt).lower()
            return sum(1 for term in terms if term in t)

        structured = structured.assign(_sc=structured[col].map(_score))
        structured = structured.sort_values("_sc", ascending=False)
        out = []
        for _, r in structured.head(limit).iterrows():
            out.append(str(r.get(col, "")).strip()[:1000])
        return out

    def _format_gold_examples_block(self, examples: list) -> str:
        """프롬프트용 골드 few-shot 블록 (문체·구성·깊이 기준)."""
        if not examples:
            return ""
        parts = ["=== 실제 작성 보고 예시 (문체·구성·깊이의 기준 — 내용은 복사 금지, 형식·톤만 따를 것) ==="]
        for i, ex in enumerate(examples, 1):
            parts.append(f"[예시 {i}]\n{ex}")
        return "\n\n".join(parts)

    def _format_all_departments_reference(self) -> str:
        """유관부서 지정용 전체 부서 참조 (master_data.json). LLM이 담당이슈·키워드를 보고
        의미 기반으로 가장 적합한 부서를 직접 지정하도록 전체 목록을 제공한다.
        (키워드 문자열 매칭이 'LNG'↔'LNG트레이딩' 등을 놓치는 문제 보완)"""
        depts = (self.master_data or {}).get("departments", {})
        if not depts:
            return "=== 유관 부서 지정 참조 ===\n(부서 데이터 없음 — 홍보그룹 기본 대응)"
        lines = ["=== 유관 부서 지정 참조 (이 목록에서만 선택 / 담당이슈·키워드로 판단) ==="]
        for name, info in depts.items():
            if not info.get("활성상태", True):
                continue
            issues = ", ".join(info.get("담당이슈", [])[:6])
            kw = info.get("키워드", "")
            lines.append(
                f"- {name} | 담당자: {info.get('담당자','')} | 연락처: {info.get('연락처','')} "
                f"| 이메일: {info.get('이메일','')} | 담당이슈: {issues} | 키워드: {kw}"
            )
        return "\n".join(lines)

    def _build_issue_report_prompt(self, media_name, reporter_name, issue_description,
                                   relevant_depts, crisis_hint, media_info,
                                   similar_cases, web_results) -> str:
        """단일 합성 보고서 생성용 user 프롬프트."""
        current_time = self._get_current_time()
        web_context = self._extract_comprehensive_context(web_results)

        depts_block = self._format_all_departments_reference()
        crisis_block = self._format_crisis_block(crisis_hint)
        similar_block = self._format_similar_cases_block(similar_cases)
        media_block = self._format_media_block(media_name, media_info)
        gold_block = self._format_gold_examples_block(self._collect_gold_examples(issue_description))

        prompt = f"""[입력 정보]
- 언론사: {media_name}
- 기자명: {reporter_name}
- 발생 일시(현재 한국시간): {current_time}
- 이슈 내용:
{issue_description}

아래는 보고서 작성에 활용할 내부 데이터와 실시간 검색 결과입니다.
이 자료를 적극 활용하여, 시스템 지침의 <이슈 발생 보고> 템플릿을 정확히 따르되 각 항목을 충실히 분석·작성하십시오.

{depts_block}

{crisis_block}

{similar_block}

{media_block}

=== 실시간 웹 검색 결과 ===
{web_context}

{gold_block}

[문체·깊이 — 위 '실제 작성 보고 예시' 수준으로 (매우 중요)]
- 간결하고 사실 중심으로 쓴다. 홍보성 수식·상투어("중요한 사업", "기여할", "최선을 다하고 있습니다", "성공적 진행")는 배제한다.
- 유관 의견은 해당 부서 실무자 관점의 구체적·사실적 입장으로 서술한다. 사안에 따라 신중론(예: "대외 언급은 자제하는 것이 바람직", "구체적 사항은 정해지지 않은 단계")도 실제 보고처럼 그대로 담는다.
- 확인되지 않은 수치·일정·계약조건을 지어내지 않는다. 아는 사실은 구체적으로, 모르는 것은 '추가 확인 필요'로.
- 형식(항목 번호·제목)은 아래 시스템 지침 템플릿을 따르고, 예시에서는 문체·구체성·실무 톤만 취한다.

[작성 요구사항 — 반드시 준수]
1. '1. 발생 일시'는 위 현재 시각을 그대로 사용한다.
2. '2. 발생 단계' 확정 원칙(엄수): 부정·논란·리스크 요소가 없는 단순 사실·일정·현황·통상 문의는 반드시 '1단계(관심)'로 분류한다. 부정 보도·해명 필요·규제/환경/노사 등 경미한 부정이면 2단계, 반복적 부정 보도·법적 분쟁 등은 3단계, 안전사고·경영진 스캔들·그룹 위기는 4단계. (키워드 추정치보다 이 원칙을 우선.)
3. '3. 발생 내용'은 "({media_name} {reporter_name})" 표기로 시작해 이슈를 사실 중심으로 요약하고, 바로 다음 줄에 "- 문의 매체 담당(당사): {{위 언론사 정보의 '당사 담당자'}}"를 명시한다(값이 없으면 '미지정').
4. '4. 유관 의견'은 다음 순서로 작성한다.
   - 맨 앞에 "- 유관 부서: {{부서명}} ({{담당자}}, {{연락처}})" 로 담당 부서를 명확히 지정한다. 부서는 반드시 위 '유관 부서 지정 참조' 목록에서 담당이슈·키워드가 이슈와 가장 부합하는 실무 부서 1~2곳을 선택하고, 필요 시 홍보그룹을 병기한다. 목록에 없는 부서·담당자·번호를 지어내지 말 것.
   - "- 사실 확인:"에는 [실시간 웹 검색 결과]와 [과거 유사 사례]에 근거해 현재까지 파악된 구체적 현황(진행 단계·최근 발표/동향·일자·수치 등)을 서술한다. '공시를 통해 확인 가능' 같은 회피성 문구 금지 — 검색·자료에서 확인된 내용을 실제로 요약하고, 자료로 확인 안 된 부분만 '추가 확인 필요'로 표기한다.
   - "- 설명 논리:", "- 메시지 방향성:"도 이어서 작성한다.
5. '5. 대응 방안'의 원보이스는 대외 인용이 가능한 정제된 1~2문장으로 작성한다.
6. '6. 대응 결과'는 반드시 공란으로 남긴다.
7. '참조. 최근 유사 사례'는 위 과거 사례에서 실제 1~2건을 (시기·유형·요지·교훈) 형태로 인용한다. 매칭 사례가 없으면 '해당 없음'으로 표기한다.
8. '참조. 이슈 정의 및 개념 정립'은 이슈의 개념과 경영/사회/법률적 함의를 간결히 정리한다.
9. 출력은 시스템 지침대로 <이슈 발생 보고>로 시작하고, 그 외 머리말·코드·주석·메타설명을 포함하지 않는다.
"""
        return prompt
    
    def _get_current_time(self) -> str:
        """현재 시간을 한국시간 기준으로 반환"""
        from datetime import datetime
        return datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
    
    
    def get_relevant_departments_from_master_data(self, issue_description: str) -> list:
        """master_data.json에서 이슈 키워드 기반 부서 매핑 (개선된 버전)"""
        if not self.master_data:
            return []
        
        departments = self.master_data.get("departments", {})
        relevant_depts = []
        
        issue_lower = issue_description.lower()
        
        # 동의어 매핑 테이블
        synonym_map = {
            "실적": ["수익", "매출", "영업이익", "순이익", "분기실적", "연간실적", "재무성과"],
            "공시": ["발표", "보고", "공개", "발표자료", "ir자료"],
            "배당": ["배당금", "주주배당", "배당정책", "배당수익률"],
            "주가": ["주식", "증권", "시가총액", "주식가격"],
            "에너지": ["전력", "발전", "전기", "신재생", "재생에너지", "친환경"],
            "lng": ["천연가스", "액화천연가스", "가스"],
            "철강": ["steel", "철", "강철", "제철", "원료", "코크스", "철광석"],
            "석탄": ["coal", "유연탄", "무연탄", "원료탄"],
            "자원": ["광물", "원자재", "commodity", "원료"],
            "무역": ["trading", "트레이딩", "수출", "수입", "해외사업"],
            "투자": ["investment", "인수", "합병", "ma", "투자계획"],
            "건설": ["construction", "플랜트", "인프라", "토목"],
            "홍보": ["pr", "언론", "미디어", "보도", "기자", "홍보팀"]
        }
        
        # 각 부서별 키워드 매칭 (개선된 알고리즘)
        for dept_name, dept_info in departments.items():
            if not dept_info.get("활성상태", True):
                continue
                
            keywords = dept_info.get("담당이슈", [])
            keyword_str = dept_info.get("키워드", "")
            
            # 모든 키워드를 하나의 리스트로 통합
            all_keywords = keywords + [k.strip() for k in keyword_str.split(",") if k.strip()]
            
            # 키워드 매칭 체크 (개선된 로직)
            match_score = 0
            matched_keywords = []
            
            for keyword in all_keywords:
                keyword_lower = keyword.lower()
                
                # 1. 직접 매칭
                if keyword_lower in issue_lower:
                    match_score += 2  # 직접 매칭은 높은 점수
                    matched_keywords.append(keyword)
                    continue
                
                # 2. 부분 매칭 (키워드가 이슈 설명에 포함)
                if len(keyword_lower) > 2:  # 2글자 이하는 부분매칭 제외
                    for word in issue_lower.split():
                        if keyword_lower in word or word in keyword_lower:
                            match_score += 1
                            matched_keywords.append(f"{keyword}(부분)")
                            break
                
                # 3. 동의어 매칭
                if keyword_lower in synonym_map:
                    for synonym in synonym_map[keyword_lower]:
                        if synonym.lower() in issue_lower:
                            match_score += 1.5  # 동의어 매칭은 중간 점수
                            matched_keywords.append(f"{keyword}→{synonym}")
                            break
                
                # 4. 역방향 동의어 매칭
                for base_word, synonyms in synonym_map.items():
                    if keyword_lower in [s.lower() for s in synonyms]:
                        if base_word in issue_lower:
                            match_score += 1.5
                            matched_keywords.append(f"{keyword}←{base_word}")
                            break
            
            # 특별 가중치: 홍보그룹은 모든 이슈에 기본 점수 부여
            if dept_name == "홍보그룹" and match_score == 0:
                match_score = 0.5
                matched_keywords.append("기본대응부서")
            
            if match_score > 0:
                dept_data = {
                    "부서명": dept_name,
                    "담당자": dept_info.get("담당자", ""),
                    "연락처": dept_info.get("연락처", ""),
                    "이메일": dept_info.get("이메일", ""),
                    "담당이슈": dept_info.get("담당이슈", []),
                    "우선순위": dept_info.get("우선순위", 999),
                    "매칭점수": round(match_score, 1),
                    "매칭키워드": matched_keywords
                }
                relevant_depts.append(dept_data)
        
        # 매칭점수 우선, 우선순위 차순으로 정렬
        relevant_depts.sort(key=lambda x: (-x["매칭점수"], x["우선순위"]))
        
        # 최소 1개 부서는 반환 (홍보그룹)
        if not relevant_depts:
            # 홍보그룹을 기본 부서로 추가
            hongbo_info = departments.get("홍보그룹", {})
            if hongbo_info:
                default_dept = {
                    "부서명": "홍보그룹",
                    "담당자": hongbo_info.get("담당자", ""),
                    "연락처": hongbo_info.get("연락처", ""),
                    "이메일": hongbo_info.get("이메일", ""),
                    "담당이슈": hongbo_info.get("담당이슈", []),
                    "우선순위": hongbo_info.get("우선순위", 2),
                    "매칭점수": 0.1,
                    "매칭키워드": ["기본대응부서"]
                }
                relevant_depts.append(default_dept)
        
        return relevant_depts[:5]  # 상위 5개 부서만 반환
    
    def _assess_crisis_level_from_master_data(self, issue_description: str) -> str:
        """master_data.json의 crisis_levels 기준으로 위기단계 판정 (개선된 버전)"""
        if not self.master_data:
            return "2단계 (주의)"
        
        crisis_levels = self.master_data.get("crisis_levels", {})
        if not crisis_levels:
            return "2단계 (주의)"
            
        issue_lower = issue_description.lower()
        
        # 단계별 매칭 점수 계산
        level_scores = {}
        
        for level_name, level_info in crisis_levels.items():
            score = 0
            examples = level_info.get("예시", [])
            definition = level_info.get("정의", "").lower()
            
            # 1. 예시 키워드 직접 매칭 (높은 점수)
            for example in examples:
                example_lower = example.lower()
                if example_lower in issue_lower:
                    score += 3  # 직접 매칭은 3점
                elif any(word in issue_lower for word in example_lower.split()):
                    score += 1  # 부분 매칭은 1점
            
            # 2. 정의 키워드 매칭
            definition_keywords = definition.split()
            for keyword in definition_keywords:
                if len(keyword) > 2 and keyword in issue_lower:
                    score += 0.5
            
            # 3. 맥락 기반 매칭 (추가 키워드)
            context_keywords = {
                "1단계 (관심)": ["출시", "발표", "수상", "긍정", "성과", "성장", "개선", "기여", "협약", "파트너십", "문의", "현황", "일정", "계획"],
                "2단계 (주의)": ["우려", "논란 조짐", "해명", "반박", "지연", "차질", "규제", "노사"],
                "3단계 (위기)": ["논란", "비판", "항의", "문제", "의혹", "조사", "검찰", "수사", "리콜", "결함"],
                "4단계 (비상)": ["사고", "유출", "폭발", "화재", "인명피해", "환경오염", "대규모", "심각", "비상사태"]
            }
            
            if level_name in context_keywords:
                for keyword in context_keywords[level_name]:
                    if keyword in issue_lower:
                        score += 2  # 맥락 키워드는 2점
            
            level_scores[level_name] = score
        
        # 점수가 가장 높은 단계 선택
        if level_scores:
            best_level = max(level_scores, key=level_scores.get)
            if level_scores[best_level] > 0:
                return best_level
        
        # 점수가 모두 0이면 내용 분석으로 기본 판정
        if any(word in issue_lower for word in ["실적", "발표", "출시", "수상", "성과"]):
            return "1단계 (관심)"
        elif any(word in issue_lower for word in ["사고", "유출", "피해", "비상"]):
            return "4단계 (비상)"
        elif any(word in issue_lower for word in ["논란", "의혹", "조사", "문제"]):
            return "3단계 (위기)"
        else:
            # 부정·리스크 요소가 없는 단순 문의·현황·일정 질의는 관심(1단계)이 기본.
            return "1단계 (관심)"  # 기본값
    
    def _get_media_info_from_master_data(self, media_name: str) -> dict:
        """master_data.json에서 언론사 정보 추출"""
        if not self.master_data:
            return {}
        
        media_contacts = self.master_data.get("media_contacts", {})
        
        # 정확한 매칭 먼저 시도
        if media_name in media_contacts:
            return media_contacts[media_name]
        
        # 부분 매칭 시도
        for media_key, media_info in media_contacts.items():
            if media_name.lower() in media_key.lower() or media_key.lower() in media_name.lower():
                return media_info
        
        return {}
    
    
    def _validate_inputs(self, media_name: str, reporter_name: str, issue_description: str) -> bool:
        """입력 데이터 검증"""
        if not media_name or len(media_name.strip()) < 2:
            return False
        if not reporter_name or len(reporter_name.strip()) < 2:
            return False
        if not issue_description or len(issue_description.strip()) < 10:
            return False
        return True
    
    
    def _conduct_web_research(self, issue_description: str, initial_analysis: dict) -> dict:
        """강화된 다중 소스 웹 검색 수행"""
        web_results = {"sources": {}, "search_summary": "웹 검색 결과 없음"}
        
        try:
            # Enhanced Research Service를 우선 사용
            if self.enhanced_research:
                print("  PROCESSING: 강화된 다중 소스 검색 시작...")
                try:
                    enhanced_results = self.enhanced_research.research_issue_comprehensive(issue_description)
                    if enhanced_results and enhanced_results.get('sources'):
                        # 웹 검색 결과 형식에 맞게 변환
                        total_sources = sum(len(sources) for sources in enhanced_results['sources'].values())
                        web_results = {
                            "sources": enhanced_results['sources'],
                            "search_summary": f"다중 소스 검색 완료 - 총 {total_sources}건 (신뢰도: {enhanced_results.get('analysis_summary', {}).get('credibility_level', 'N/A')})"
                        }
                        print(f"  RESULT: 강화된 다중 소스 검색 완료 - {web_results.get('search_summary')}")
                        return web_results
                except Exception as e:
                    print(f"  WARNING: 강화된 검색 실패, 기본 검색으로 전환: {str(e)}")
            
            # 기본 검색 서비스 사용 (폴백)
            if not self.research_service:
                print("  WARNING: 검색 서비스가 초기화되지 않았습니다.")
                return web_results
            
            print("  PROCESSING: 기본 네이버 API 검색 시작...")
            
            # 기존 IssueResearchService 사용
            search_results = self.research_service.comprehensive_search(issue_description)
            
            if search_results and len(search_results) > 0:
                web_results = {
                    "sources": {"naver_news": search_results},
                    "search_query": issue_description,
                    "search_summary": f"네이버 뉴스 {len(search_results)}건 수집"
                }
            
            print(f"  RESULT: {web_results['search_summary']}")
            return web_results
            
        except Exception as e:
            print(f"  ERROR: 웹 검색 중 오류 발생: {str(e)}")
            return web_results
    
    
    def _extract_comprehensive_context(self, web_results: dict) -> str:
        """다중 소스에서 종합적인 맥락 정보 추출"""
        context_sections = []
        
        # 새로운 다중 소스 구조 처리
        if "sources" in web_results:
            sources = web_results["sources"]
            
            # 네이버 뉴스
            if sources.get("naver_news"):
                context_sections.append("📰 네이버 뉴스 정보:")
                for i, item in enumerate(sources["naver_news"][:5], 1):
                    title = item.get("title", "")
                    desc = item.get("description", "")
                    context_sections.append(f"{i}. {title}")
                    if desc:
                        context_sections.append(f"   요약: {desc[:100]}...")
                context_sections.append("")
            
            # 포스코 공식 소스
            if sources.get("posco_official"):
                context_sections.append("🏢 포스코인터내셔널 공식 정보:")
                for i, item in enumerate(sources["posco_official"][:3], 1):
                    title = item.get("title", "")
                    desc = item.get("description", "")
                    context_sections.append(f"{i}. {title}")
                    if desc:
                        context_sections.append(f"   내용: {desc[:150]}...")
                context_sections.append("")
            
            # DART 공시 정보
            if sources.get("dart_filings"):
                context_sections.append("📋 DART 전자공시 정보:")
                for i, item in enumerate(sources["dart_filings"][:3], 1):
                    title = item.get("title", "")
                    context_sections.append(f"{i}. {title}")
                context_sections.append("")
            
            # 한국거래소 정보
            if sources.get("krx_disclosures"):
                context_sections.append("🏛️ 한국거래소 공시 정보:")
                for i, item in enumerate(sources["krx_disclosures"][:3], 1):
                    title = item.get("title", "")
                    context_sections.append(f"{i}. {title}")
                context_sections.append("")
        
        # 기존 구조 호환성 (폴백)
        elif web_results.get("news"):
            context_sections.append("📰 뉴스 정보:")
            for i, item in enumerate(web_results["news"][:3], 1):
                title = item.get("title", "")
                desc = item.get("description", "")
                context_sections.append(f"{i}. {title}: {desc}")
            context_sections.append("")
        
        if not context_sections:
            return "수집된 정보가 없습니다. 추가적인 조사가 필요합니다."
        
        # 검색 요약 정보 추가
        if web_results.get("search_summary"):
            context_sections.insert(0, f"🔍 검색 요약: {web_results['search_summary']}")
            context_sections.insert(1, "")
        
        return "\n".join(context_sections)
    
    
    
    
    
    
    def _search_by_media(self, media_name: str, limit: int = 5) -> pd.DataFrame:
        """특정 언론사의 과거 사례 검색 (개선된 정규화 검색)"""
        if self.media_response_data is None:
            return pd.DataFrame()
        
        # 1단계: 언론사명 정규화 및 별칭 처리
        normalized_media_name = self._normalize_media_name(media_name)
        media_aliases = self._get_media_aliases(normalized_media_name)
        
        # 2단계: 다중 컬럼에서 언론사 정보 검색
        media_cases = self._multi_column_media_search(media_aliases)
        
        # 3단계: 검색 결과 정리 및 정렬
        if not media_cases.empty:
            # 언론사 컬럼이 없으면 자동 생성
            if '언론사' not in media_cases.columns:
                media_cases = self._add_media_column(media_cases, normalized_media_name)
            
            # 최근 순으로 정렬
            if '발생 일시' in media_cases.columns:
                media_cases = media_cases.sort_values('발생 일시', ascending=False)
        
        return media_cases.head(limit)
    
    def _normalize_media_name(self, media_name: str) -> str:
        """언론사명 정규화"""
        # 공통 접미사/접두사 제거
        normalized = media_name.strip()
        
        # 정규화 규칙들
        normalization_rules = {
            '조선일보': ['조선', '조선일보'],
            '중앙일보': ['중앙', '중앙일보'],
            '동아일보': ['동아', '동아일보'],
            '한국경제': ['한경', '한국경제', '한국경제신문'],
            '매일경제': ['매경', '매일경제', '매일경제신문'],
            '서울경제': ['서울경제', '서울경제신문'],
            '연합뉴스': ['연합', '연합뉴스'],
            '뉴시스': ['뉴시스', 'newsis'],
            '뉴스1': ['뉴스1', 'news1'],
            '뉴스핌': ['뉴스핌', 'newspim'],
            '머니투데이': ['머니투데이', 'mt', '머투'],
            '이데일리': ['이데일리', 'edaily'],
            '파이낸셜뉴스': ['파이낸셜뉴스', 'fn', '파이낸셜'],
            '아시아경제': ['아시아경제', '아경'],
            '헤럴드경제': ['헤럴드경제', '헤럴드'],
            '한겨레': ['한겨레', 'hani'],
            '경향신문': ['경향', '경향신문'],
            '국민일보': ['국민일보', '국민']
        }
        
        # 역방향 매핑 생성 (별칭 → 정규명)
        for standard_name, aliases in normalization_rules.items():
            if normalized.lower() in [alias.lower() for alias in aliases]:
                return standard_name
        
        return normalized
    
    def _get_media_aliases(self, media_name: str) -> List[str]:
        """언론사의 모든 별칭 반환"""
        normalization_rules = {
            '조선일보': ['조선', '조선일보', 'chosun'],
            '중앙일보': ['중앙', '중앙일보', 'joongang'],
            '동아일보': ['동아', '동아일보', 'donga'],
            '한국경제': ['한경', '한국경제', '한국경제신문', 'hankyung'],
            '매일경제': ['매경', '매일경제', '매일경제신문', 'mk'],
            '서울경제': ['서울경제', '서울경제신문', 'sedaily'],
            '연합뉴스': ['연합', '연합뉴스', 'yonhap'],
            '뉴시스': ['뉴시스', 'newsis'],
            '뉴스1': ['뉴스1', 'news1'],
            '뉴스핌': ['뉴스핌', 'newspim'],
            '머니투데이': ['머니투데이', 'mt', '머투'],
            '이데일리': ['이데일리', 'edaily'],
            '파이낸셜뉴스': ['파이낸셜뉴스', 'fn', '파이낸셜'],
            '아시아경제': ['아시아경제', '아경'],
            '헤럴드경제': ['헤럴드경제', '헤럴드'],
            '한겨레': ['한겨레', 'hani'],
            '경향신문': ['경향', '경향신문'],
            '국민일보': ['국민일보', '국민']
        }
        
        return normalization_rules.get(media_name, [media_name])
    
    def _multi_column_media_search(self, media_aliases: List[str]) -> pd.DataFrame:
        """다중 컬럼에서 언론사 정보 검색"""
        search_results = []
        
        # 검색 대상 컬럼들 (우선순위 순)
        search_columns = ['언론사', '대응 결과', '이슈 발생 보고', '발생 유형']
        
        for column in search_columns:
            if column in self.media_response_data.columns:
                for alias in media_aliases:
                    # 각 별칭으로 검색
                    matches = self.media_response_data[
                        self.media_response_data[column].str.contains(
                            alias, case=False, na=False, regex=False
                        )
                    ]
                    if not matches.empty:
                        search_results.append(matches)
        
        # 결과 통합 및 중복 제거
        if search_results:
            combined_results = pd.concat(search_results, ignore_index=True)
            # 중복 제거 (순번 기준)
            if '순번' in combined_results.columns:
                combined_results = combined_results.drop_duplicates(subset=['순번'])
            else:
                combined_results = combined_results.drop_duplicates()
            return combined_results
        
        return pd.DataFrame()
    
    def _add_media_column(self, df: pd.DataFrame, media_name: str) -> pd.DataFrame:
        """데이터프레임에 언론사 컬럼 추가"""
        df_copy = df.copy()
        
        # 언론사 컬럼이 없으면 추가
        if '언론사' not in df_copy.columns:
            df_copy['언론사'] = media_name
            
            # 대응 결과에서 언론사 정보 추출 시도
            if '대응 결과' in df_copy.columns:
                for idx, row in df_copy.iterrows():
                    result_text = str(row.get('대응 결과', ''))
                    extracted_media = self._extract_media_from_text(result_text)
                    if extracted_media:
                        df_copy.at[idx, '언론사'] = extracted_media
        
        return df_copy
    
    def _extract_media_from_text(self, text: str) -> Optional[str]:
        """텍스트에서 언론사명 추출"""
        if not text or pd.isna(text):
            return None
            
        text_lower = text.lower()
        
        # master_data.json의 언론사 정보 활용
        if self.master_data and 'media_contacts' in self.master_data:
            for media_name in self.master_data['media_contacts'].keys():
                if media_name.lower() in text_lower:
                    return media_name
        
        # 일반적인 언론사 패턴 검색
        common_media_patterns = [
            '조선일보', '중앙일보', '동아일보', '한국경제', '매일경제', '서울경제',
            '연합뉴스', '뉴시스', '뉴스1', '뉴스핌', '머니투데이', '이데일리',
            '파이낸셜뉴스', '아시아경제', '헤럴드경제', '한겨레', '경향신문', '국민일보'
        ]
        
        for pattern in common_media_patterns:
            if pattern in text:
                return pattern
        
        return None
    
    def get_media_specific_info(self, media_name: str, reporter_name: str = None) -> Dict[str, Any]:
        """언론사별 맞춤 정보 제공 (정규화된 시스템)"""
        normalized_media = self._normalize_media_name(media_name)
        
        media_info = {
            'normalized_name': normalized_media,
            'classification': None,
            'reporters': [],
            'contact_person': None,
            'past_cases': [],
            'response_strategy': None,
            'reporter_info': None
        }
        
        # master_data.json에서 언론사 정보 조회
        if self.master_data and 'media_contacts' in self.master_data:
            media_contacts = self.master_data['media_contacts']
            
            if normalized_media in media_contacts:
                contact_info = media_contacts[normalized_media]
                media_info.update({
                    'classification': contact_info.get('구분', 'N/A'),
                    'reporters': contact_info.get('출입기자', []),
                    'contact_person': contact_info.get('담당자', 'N/A')
                })
                
                # 특정 기자 정보 검색
                if reporter_name:
                    media_info['reporter_info'] = self._get_reporter_info(
                        normalized_media, reporter_name, contact_info
                    )
        
        # 과거 대응 사례 조회
        past_cases = self._search_by_media(normalized_media, limit=5)
        if not past_cases.empty:
            media_info['past_cases'] = self._summarize_past_cases(past_cases)
        
        # 언론사별 맞춤 대응 전략
        media_info['response_strategy'] = self._get_media_response_strategy(
            normalized_media, media_info['classification']
        )
        
        return media_info
    
    def _get_reporter_info(self, media_name: str, reporter_name: str, contact_info: Dict) -> Dict:
        """특정 기자 정보 조회"""
        reporter_info = {
            'name': reporter_name,
            'confirmed': False,
            'beat': None,
            'contact_history': []
        }
        
        # 출입기자 명단에서 확인
        reporters = contact_info.get('출입기자', [])
        for reporter in reporters:
            if reporter_name in reporter or reporter in reporter_name:
                reporter_info['confirmed'] = True
                reporter_info['name'] = reporter
                # 전문 분야 추출 (괄호 안 정보)
                if '(' in reporter and ')' in reporter:
                    beat = reporter.split('(')[1].split(')')[0]
                    reporter_info['beat'] = beat
                break
        
        # 과거 대응 내역에서 해당 기자 관련 사례 검색
        if self.media_response_data is not None:
            reporter_cases = self.media_response_data[
                self.media_response_data['대응 결과'].str.contains(
                    reporter_name, na=False, case=False
                )
            ]
            if not reporter_cases.empty:
                reporter_info['contact_history'] = len(reporter_cases)
        
        return reporter_info
    
    def _summarize_past_cases(self, past_cases: pd.DataFrame) -> List[Dict]:
        """과거 사례 요약"""
        summaries = []
        
        for _, case in past_cases.head(3).iterrows():  # 최근 3건만
            summary = {
                'date': case.get('발생 일시', 'N/A'),
                'type': case.get('발생 유형', 'N/A'),
                'stage': case.get('단계', 'N/A'),
                'issue': case.get('이슈 발생 보고', 'N/A')[:100] + '...' if len(str(case.get('이슈 발생 보고', ''))) > 100 else case.get('이슈 발생 보고', 'N/A'),
                'outcome': case.get('대응 결과', 'N/A')[:100] + '...' if len(str(case.get('대응 결과', ''))) > 100 else case.get('대응 결과', 'N/A')
            }
            summaries.append(summary)
        
        return summaries
    
    def _get_media_response_strategy(self, media_name: str, classification: str) -> Dict[str, Any]:
        """언론사별 맞춤 대응 전략"""
        
        # 언론사 유형별 기본 전략
        base_strategies = {
            '종합지': {
                'approach': '포괄적 정보 제공',
                'key_points': ['정확한 사실 전달', '배경 설명 상세', '향후 계획 명시'],
                'tone': '공식적, 신중한'
            },
            '경제지': {
                'approach': '경제적 임팩트 중심',
                'key_points': ['재무적 영향', '시장 전망', '투자자 관점'],
                'tone': '전문적, 데이터 중심'
            },
            '통신사': {
                'approach': '신속 정확한 팩트',
                'key_points': ['핵심 사실', '공식 입장', '후속 일정'],
                'tone': '간결하고 명확한'
            },
            '석간지': {
                'approach': '심층 분석 지원',
                'key_points': ['산업 동향', '전략적 의미', '장기 전망'],
                'tone': '분석적, 전략적'
            },
            '영자지': {
                'approach': '글로벌 맥락 강조',
                'key_points': ['국제 경쟁력', '해외 전개', '글로벌 트렌드'],
                'tone': '국제적 관점'
            },
            '기타온라인': {
                'approach': '디지털 친화적',
                'key_points': ['시각적 자료', '인포그래픽', '소셜 확산'],
                'tone': '접근하기 쉬운'
            }
        }
        
        # 기본 전략
        strategy = base_strategies.get(classification, base_strategies['종합지'])
        
        # 언론사별 특화 전략
        specific_strategies = {
            '조선일보': {
                'priority': '정부정책 연관성',
                'focus': ['정책 부합성', '국가 경제 기여', '사회적 책임']
            },
            '한국경제': {
                'priority': '경제성과 강조',
                'focus': ['수익성', '성장성', '시장 점유율', 'ROI']
            },
            '연합뉴스': {
                'priority': '객관적 사실 전달',
                'focus': ['검증된 정보', '다각도 검토', '균형 잡힌 시각']
            },
            '머니투데이': {
                'priority': '투자 관점 부각',
                'focus': ['주가 영향', '투자자 반응', '애널리스트 의견']
            }
        }
        
        if media_name in specific_strategies:
            strategy.update(specific_strategies[media_name])
        
        return strategy
    
    def generate_media_customized_response(self, media_name: str, reporter_name: str, 
                                         issue_description: str) -> str:
        """언론사별 맞춤형 대응 메시지 생성"""
        
        # 언론사 정보 수집
        media_info = self.get_media_specific_info(media_name, reporter_name)
        
        # 기본 이슈 분석
        relevant_depts = self.get_relevant_departments(issue_description)
        crisis_level = self._assess_crisis_level(issue_description)
        
        # 맞춤형 프롬프트 구성
        customized_prompt = f"""
        다음 언론사 특성에 맞는 맞춤형 대응 메시지를 작성해주세요:
        
        === 언론사 정보 ===
        언론사: {media_info['normalized_name']} ({media_info['classification']})
        기자: {reporter_name}
        담당자: {media_info['contact_person']}
        
        === 기자 정보 ===
        {self._format_reporter_info(media_info.get('reporter_info', {}))}
        
        === 이슈 정보 ===
        내용: {issue_description}
        위기단계: {crisis_level}
        관련부서: {', '.join([dept.get('부서명', '') for dept in relevant_depts[:2]])}
        
        === 과거 대응 사례 ===
        {self._format_past_cases(media_info.get('past_cases', []))}
        
        === 대응 전략 ===
        접근방식: {media_info['response_strategy']['approach']}
        핵심포인트: {', '.join(media_info['response_strategy']['key_points'])}
        톤앤메너: {media_info['response_strategy']['tone']}
        
        위 정보를 바탕으로 다음 형식의 대응 메시지를 작성해주세요:
        
        1. 핵심 메시지 (1-2문장)
        2. 상세 설명 (3-4문장)
        3. 추가 제공 가능한 자료
        4. 후속 일정 또는 연락처
        """
        
        try:
            response = self.llm.chat(
                customized_prompt,
                system_prompt="당신은 포스코인터내셔널의 언론대응 전문가입니다. 각 언론사의 특성과 기자의 성향을 고려한 맞춤형 메시지를 작성해주세요.",
                temperature=0.3
            )
            return response
        except Exception as e:
            return f"맞춤형 대응 메시지 생성 중 오류: {str(e)}"
    
    def _format_reporter_info(self, reporter_info: Dict) -> str:
        """기자 정보 포맷팅"""
        if not reporter_info:
            return "기자 정보 없음"
        
        info_str = f"확인됨: {'예' if reporter_info.get('confirmed') else '아니오'}"
        if reporter_info.get('beat'):
            info_str += f", 전문분야: {reporter_info['beat']}"
        if reporter_info.get('contact_history'):
            info_str += f", 과거 접촉: {reporter_info['contact_history']}회"
        
        return info_str
    
    def _format_past_cases(self, past_cases: List[Dict]) -> str:
        """과거 사례 포맷팅"""
        if not past_cases:
            return "과거 대응 사례 없음"
        
        formatted = []
        for case in past_cases:
            case_str = f"- {case['date']} ({case['stage']}): {case['issue']}"
            formatted.append(case_str)
        
        return '\n'.join(formatted)
    
    def _assess_crisis_level(self, issue_description: str, verbose: bool = False) -> str:
        """AI 기반 위기 단계 자동 판단 (개선된 버전)"""
        
        # master_data.json에서 위기 단계 정보 로드
        crisis_levels = self.master_data.get('crisis_levels', {})
        
        # 1차: 기본 키워드 기반 예비 판단
        preliminary_level, score_info = self._preliminary_crisis_assessment(issue_description, return_details=True)
        
        if verbose:
            print(f"[위기단계 판단] 예비 판단: {preliminary_level} (점수: {score_info['total_score']})")
            if score_info['matched_keywords']:
                print(f"[위기단계 판단] 매칭된 키워드: {', '.join(score_info['matched_keywords'])}")
        
        # 2차: AI 기반 정밀 분석
        final_level = self._ai_based_crisis_assessment(issue_description, crisis_levels, preliminary_level)
        
        if verbose and final_level != preliminary_level:
            print(f"[위기단계 판단] AI 정밀 분석 결과: {preliminary_level} → {final_level}")
        
        return final_level
    
    def _preliminary_crisis_assessment(self, issue_description: str, return_details: bool = False):
        """1차 키워드 기반 예비 위기 단계 판단"""
        issue_lower = issue_description.lower()
        
        # 키워드 가중치 기반 점수 계산
        crisis_score = 0
        matched_keywords = []
        
        # 위기 단계별 키워드 매핑 (포스코인터내셔널 특화)
        crisis_keywords = {
            4: {  # 4단계 (비상) - 가중치 10
                'leadership': ['ceo', '대표이사', '회장', '경영진', '임원진'],
                'major_incidents': ['스캔들', '안전사고', '인명피해', '중대재해', '폭발', '화재'],
                'group_crisis': ['그룹위기', '비상사태', '전사위기', '포스코그룹'],
                'legal_severe': ['구속', '기소', '검찰수사', '특검', '국정감사'],
                'business_critical': ['상장폐지', '회사정리', '파산', '해산']
            },
            3: {  # 3단계 (위기) - 가중치 7  
                'business_disruption': ['사업중단', '공장폐쇄', '가동중단', '운영중단'],
                'financial_severe': ['대규모손실', '적자전환', '자금난', '유동성위기'],
                'legal_major': ['법적분쟁', '소송', '손해배상', '제재', '과징금'],
                'regulatory': ['규제위반', '처벌', '영업정지', '허가취소', '과태료'],
                'investigation': ['수사', '압수수색', '감사', '조사', '특별점검'],
                'posco_specific': ['미얀마', '가스전', '석탄발전', '철강', '원료']
            },
            2: {  # 2단계 (주의) - 가중치 4
                'negative_issues': ['부정', '논란', '문제제기', '우려', '비판', '의혹제기'],
                'environmental': ['환경문제', '오염', '탄소배출', '환경규제', '친환경'],
                'labor': ['노사갈등', '파업', '임금협상', '근로조건', '고용'],
                'community': ['민원', '주민반대', '지역갈등', '항의', '시위'],
                'market_negative': ['주가하락', '실적부진', '매출감소', '수익성악화'],
                'operational': ['품질문제', '납기지연', '공급차질', '생산차질']
            },
            1: {  # 1단계 (관심) - 가중치 2
                'positive_news': ['발표', '출시', '수상', '인수', '확장', '신제품'],
                'investment': ['투자', '지분', '펀드', '자본', '출자', '증자'],
                'cooperation': ['협력', '파트너십', '제휴', '계약체결', 'mou'],
                'performance': ['실적발표', '증익', '흑자', '성장', '확대'],
                'csr': ['csr', '사회공헌', '기부', '봉사', '지원사업', '상생'],
                'recognition': ['시상', '인증', '선정', '평가', '등급상향']
            }
        }
        
        # 각 단계별 키워드 점수 적용
        for stage, categories in crisis_keywords.items():
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in issue_lower:
                        matched_keywords.append(f"{keyword}({stage}단계)")
                        if stage == 4:
                            crisis_score += 10
                        elif stage == 3:
                            crisis_score += 7
                        elif stage == 2:
                            crisis_score += 4
                        elif stage == 1:
                            crisis_score += 2
        
        # 부정적 수식어 및 강조 표현 추가 점수
        negative_modifiers = ['대규모', '심각한', '중대한', '치명적', '막대한', '전례없는', '사상최대']
        for modifier in negative_modifiers:
            if modifier in issue_lower:
                crisis_score += 3
                matched_keywords.append(f"{modifier}(수식어)")
        
        # 긴급성 표현 추가 점수
        urgency_words = ['긴급', '즉시', '신속', '조속', '시급']
        for word in urgency_words:
            if word in issue_lower:
                crisis_score += 2
                matched_keywords.append(f"{word}(긴급성)")
        
        # 점수 기반 단계 결정
        if crisis_score >= 15:
            level = "4단계 (비상)"
        elif crisis_score >= 10:
            level = "3단계 (위기)"
        elif crisis_score >= 5:
            level = "2단계 (주의)"
        else:
            level = "1단계 (관심)"
        
        if return_details:
            return level, {
                'total_score': crisis_score,
                'matched_keywords': matched_keywords,
                'level': level
            }
        else:
            return level
    
    def _ai_based_crisis_assessment(self, issue_description: str, crisis_levels: Dict, preliminary_level: str) -> str:
        """AI 기반 정밀 위기 단계 판단"""
        
        # 과거 유사 사례 검색
        similar_cases = self.search_media_responses(issue_description, limit=5)
        similar_cases_info = ""
        
        if not similar_cases.empty:
            similar_cases_info = "\n=== 유사 과거 사례 ===\n"
            for idx, case in similar_cases.head(3).iterrows():
                similar_cases_info += f"- {case.get('단계', 'N/A')}: {case.get('이슈 발생 보고', 'N/A')[:100]}...\n"
        
        # 위기 단계 정의 정보 구성
        crisis_definitions = ""
        for level, info in crisis_levels.items():
            crisis_definitions += f"\n{level}:\n"
            crisis_definitions += f"  - 정의: {info.get('정의', 'N/A')}\n"
            crisis_definitions += f"  - 설명: {info.get('설명', 'N/A')}\n"
            crisis_definitions += f"  - 예시: {', '.join(info.get('예시', []))}\n"
        
        # AI 판단을 위한 프롬프트 구성
        assessment_prompt = f"""
        다음 이슈의 위기 단계를 정확히 판단해주세요:
        
        이슈 내용: {issue_description}
        
        예비 판단 결과: {preliminary_level}
        
        === 위기 단계 기준 ===
        {crisis_definitions}
        
        {similar_cases_info}
        
        위의 기준과 과거 사례를 종합적으로 고려하여, 다음 중 하나만 선택해주세요:
        - 1단계 (관심)
        - 2단계 (주의)  
        - 3단계 (위기)
        - 4단계 (비상)
        
        답변은 위기 단계만 정확히 출력하고, 추가 설명은 하지 마세요.
        """
        
        try:
            # LLM을 통한 정밀 판단
            ai_assessment = self.llm.chat(
                assessment_prompt, 
                system_prompt="당신은 포스코인터내셔널의 위기 관리 전문가입니다. 이슈의 심각도를 정확히 판단하여 적절한 위기 단계를 선택해주세요.",
                temperature=0.1  # 일관성을 위해 낮은 창의성 설정
            )
            
            # AI 응답에서 위기 단계 추출
            ai_level = self._extract_crisis_level_from_response(ai_assessment)
            
            # AI 판단이 유효하면 사용, 아니면 예비 판단 사용
            if ai_level:
                return ai_level
            else:
                return preliminary_level
                
        except Exception as e:
            print(f"AI 기반 위기 단계 판단 중 오류: {str(e)}")
            return preliminary_level
    
    def _extract_crisis_level_from_response(self, response: str) -> str:
        """AI 응답에서 위기 단계 추출"""
        if not response:
            return None
            
        response_lower = response.lower()
        
        # 4단계부터 역순으로 확인 (높은 단계 우선)
        if "4단계" in response_lower or "비상" in response_lower:
            return "4단계 (비상)"
        elif "3단계" in response_lower or "위기" in response_lower:
            return "3단계 (위기)"
        elif "2단계" in response_lower or "주의" in response_lower:
            return "2단계 (주의)"
        elif "1단계" in response_lower or "관심" in response_lower:
            return "1단계 (관심)"
        else:
            return None
    
    def _format_departments(self, departments: List[Dict]) -> str:
        """부서 정보 구체적 포맷팅 (개선된 버전)"""
        if not departments:
            return "관련 부서 정보가 없습니다."
        
        formatted = []
        for i, dept in enumerate(departments, 1):
            dept_info = f"■ {dept.get('부서명', 'N/A')} ({i}순위)"
            
            # 기본 연락처 정보
            if dept.get('담당자'):
                dept_info += f"\n  - 담당자: {dept['담당자']}"
            if dept.get('연락처'):
                dept_info += f"\n  - 연락처: {dept['연락처']}"
            if dept.get('이메일'):
                dept_info += f"\n  - 이메일: {dept['이메일']}"
            
            # 담당 영역 정보
            if dept.get('담당이슈'):
                issues = ', '.join(dept['담당이슈']) if isinstance(dept['담당이슈'], list) else dept['담당이슈']
                dept_info += f"\n  - 담당이슈: {issues}"
            
            # 매칭 정보 (개선된 알고리즘에서 제공)
            if dept.get('관련성점수'):
                dept_info += f"\n  - 관련성점수: {dept['관련성점수']}점"
            
            if dept.get('매칭항목'):
                matching_details = ', '.join(dept['매칭항목'])
                dept_info += f"\n  - 매칭근거: {matching_details}"
            
            # 부서 우선순위
            if dept.get('우선순위'):
                dept_info += f"\n  - 조직우선순위: {dept['우선순위']}"
                
            formatted.append(dept_info)
        
        return "\n\n".join(formatted)
    
    def _format_cases(self, cases: pd.DataFrame) -> str:
        """사례 정보 구체적 포맷팅"""
        if cases.empty:
            return "관련 사례가 없습니다."
        
        formatted = []
        for idx, case in cases.iterrows():
            case_info = f"■ 사례 {idx + 1}"
            case_info += f"\n  - 일시: {case.get('발생 일시', 'N/A')}"
            case_info += f"\n  - 단계: {case.get('단계', 'N/A')}"
            case_info += f"\n  - 유형: {case.get('발생 유형', 'N/A')}"
            
            if '대응 결과' in case and pd.notna(case['대응 결과']):
                result = str(case['대응 결과'])[:100] + "..." if len(str(case['대응 결과'])) > 100 else case['대응 결과']
                case_info += f"\n  - 대응결과: {result}"
                
            if '이슈 발생 보고' in case and pd.notna(case['이슈 발생 보고']):
                issue = str(case['이슈 발생 보고'])[:80] + "..." if len(str(case['이슈 발생 보고'])) > 80 else case['이슈 발생 보고']
                case_info += f"\n  - 이슈내용: {issue}"
                
            formatted.append(case_info)
        
        return "\n\n".join(formatted[:3])  # 최대 3개만 표시
    
    def research_issue_with_web_search(self, issue_description: str) -> str:
        """
        발생 이슈에 대한 웹 검색 기반 종합 연구
        언론 총괄담당자를 위한 배경 정보 및 대응 전략 제공
        
        Args:
            issue_description (str): 발생한 이슈 설명
        
        Returns:
            str: 언론 총괄담당자용 이슈 연구 보고서
        """
        if not self.research_service:
            return "⚠️ 웹 검색 서비스를 사용할 수 없습니다. 네이버 API 설정을 확인해주세요."
        
        print(f"RESEARCH: 이슈 연구 시작: {issue_description}")
        
        # 1. 웹 검색을 통한 정보 수집
        research_data = self.research_service.research_issue(issue_description)
        
        # 2. 기존 내부 데이터와 연결
        internal_context = self._get_internal_context_for_issue(issue_description)
        
        # 3. LLM을 통한 종합 분석 및 보고서 생성
        report = self._generate_issue_research_report(research_data, internal_context, issue_description)
        
        return report
    
    def _get_internal_context_for_issue(self, issue_description: str) -> Dict[str, Any]:
        """이슈와 관련된 내부 데이터 수집"""
        context = {
            "relevant_departments": [],
            "similar_cases": [],
            "response_strategies": []
        }
        
        try:
            # 관련 부서 찾기
            context["relevant_departments"] = self.get_relevant_departments(issue_description)
            
            # 유사한 과거 사례 찾기
            if self.media_response_data is not None:
                context["similar_cases"] = self._find_similar_media_cases(issue_description)
            
            # 대응 전략 추천
            context["response_strategies"] = self._get_response_strategies(issue_description)
            
        except Exception as e:
            print(f"WARNING: 내부 데이터 수집 중 오류: {str(e)}")
        
        return context
    
    def _find_similar_media_cases(self, issue_description: str) -> List[Dict]:
        """유사한 언론대응 사례 검색"""
        if self.media_response_data is None or len(self.media_response_data) == 0:
            return []
        
        similar_cases = []
        issue_keywords = issue_description.lower().split()
        
        for _, case in self.media_response_data.iterrows():
            case_dict = case.to_dict()
            
            # 이슈 내용 비교
            if pd.notna(case.get('이슈 발생 보고')):
                case_issue = str(case['이슈 발생 보고']).lower()
                
                # 키워드 매칭 점수 계산
                match_score = sum(1 for keyword in issue_keywords if keyword in case_issue)
                
                if match_score > 0:
                    case_dict['relevance_score'] = match_score
                    similar_cases.append(case_dict)
        
        # 관련도순으로 정렬하여 상위 3개 반환
        similar_cases.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return similar_cases[:3]
    
    def _get_response_strategies(self, issue_description: str) -> List[str]:
        """이슈 유형에 따른 대응 전략 제안"""
        strategies = []
        issue_lower = issue_description.lower()
        
        # 위기 수준별 기본 전략
        if any(word in issue_lower for word in ['화재', '폭발', '사고', '안전', '위험']):
            strategies.extend([
                "즉시 안전 확보 및 피해 최소화 조치",
                "관계 기관 신속 보고 및 협조 체계 구축",
                "정확한 사실 관계 파악 후 투명한 정보 공개"
            ])
        
        if any(word in issue_lower for word in ['환경', '오염', '배출']):
            strategies.extend([
                "환경 영향 최소화를 위한 즉시 조치",
                "환경 당국과의 협력적 대응",
                "환경 복원 계획 수립 및 공개"
            ])
        
        if any(word in issue_lower for word in ['품질', '리콜', '결함']):
            strategies.extend([
                "고객 안전 최우선 원칙 하에 신속 대응",
                "투명한 원인 조사 및 결과 공개",
                "재발 방지 대책 수립 및 이행"
            ])
        
        # 기본 전략이 없을 경우 일반적인 위기 대응 전략 제공
        if not strategies:
            strategies = [
                "정확한 사실 관계 파악 및 검증",
                "이해관계자별 맞춤 커뮤니케이션 전략 수립",
                "지속적인 모니터링 및 후속 조치 계획"
            ]
        
        return strategies
    
    def _generate_issue_research_report(self, research_data: Dict, internal_context: Dict, original_issue: str) -> str:
        """종합 이슈 연구 보고서 생성"""
        
        # 프롬프트 구성
        prompt = f"""
당신은 20년 경력의 언론 총괄 담당자입니다. 
다음 발생 이슈에 대한 종합적인 연구 보고서를 작성해주세요.

**발생 이슈:** {original_issue}

**웹 검색 결과:**
- 전체 검색 결과: {research_data['analysis_summary']['total_sources']}건
- 뉴스 기사: {research_data['analysis_summary']['news_count']}건  
- 블로그/포럼: {research_data['analysis_summary']['blog_count']}건
- 언론 관심도: {research_data['analysis_summary']['coverage_level']}

**주요 뉴스 헤드라인:**
{self._format_news_headlines(research_data.get('news_results', []))}

**내부 관련 정보:**
- 담당 부서: {len(internal_context.get('relevant_departments', []))}개 부서
- 유사 과거 사례: {len(internal_context.get('similar_cases', []))}건
- 권장 대응 전략: {len(internal_context.get('response_strategies', []))}개

다음 형식으로 **언론 총괄담당자용 이슈 연구 보고서**를 작성해주세요:

## 📋 이슈 연구 보고서

### 1. 이슈 개요
- 이슈 성격 및 심각도
- 현재 언론 관심도 및 보도 동향

### 2. 외부 여론 현황
- 주요 언론 보도 내용 분석
- 여론의 주요 관심사 및 우려사항
- 향후 보도 확산 가능성

### 3. 내부 대응 현황  
- 관련 담당 부서 및 역할
- 과거 유사 사례 대응 경험
- 현재 대응 체계 점검 사항

### 4. 언론 대응 전략 권고
- 즉시 대응 사항 (24시간 내)
- 단기 대응 계획 (1주일 내)
- 중장기 이미지 관리 방안

### 5. 주의사항 및 리스크
- 잠재적 2차 이슈 가능성
- 언론 대응 시 주의사항
- 모니터링 포인트

보고서는 간결하고 실무적으로 작성하되, 구체적인 실행 방안을 포함해주세요.
"""
        
        # LLM 호출하여 보고서 생성
        try:
            report = self.llm.chat(prompt)
            return report
        except Exception as e:
            return f"⚠️ 보고서 생성 중 오류 발생: {str(e)}"
    
    def _format_news_headlines(self, news_results: List[Dict]) -> str:
        """뉴스 헤드라인 포맷팅"""
        if not news_results:
            return "검색된 뉴스 없음"
        
        headlines = []
        for i, news in enumerate(news_results[:5], 1):  # 상위 5개만
            headline = news.get('title', '제목 없음')
            pub_date = news.get('pub_date', '')
            headlines.append(f"{i}. {headline} ({pub_date})")
        
        return "\n".join(headlines)

def main():
    """데이터 기반 LLM 테스트"""
    print("=== 데이터 기반 LLM 시스템 테스트 ===\n")
    
    # 데이터 기반 LLM 초기화
    data_llm = DataBasedLLM()
    
    # 테스트 질의들
    test_queries = [
        "배당 관련 이슈가 발생했을 때 누구에게 연락해야 하나요?",
        "전기차 관련 언론 보도에 어떻게 대응해야 하나요?",
        "최근 언론대응 트렌드를 분석해주세요"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. 질문: {query}")
        print("-" * 50)
        
        if "트렌드" in query:
            response = data_llm.analyze_issue_trends(30)
        else:
            response = data_llm.generate_data_based_response(query)
        
        print(f"답변: {response}\n")
        print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
