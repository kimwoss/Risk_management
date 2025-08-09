"""
기존 DataBasedLLM 클래스 강화 버전
8단계 프로세스 구조는 유지하되 성능과 안정성 개선
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

class EnhancedDataBasedLLM:
    """강화된 DataBasedLLM - 기존 구조 + 성능 최적화"""
    
    def __init__(self, original_llm):
        """기존 DataBasedLLM 인스턴스를 래핑"""
        self.original = original_llm
        self.performance_tracker = PerformanceTracker()
        self.cache = SimpleCache()
        
    def generate_comprehensive_issue_report_enhanced(self, media_name: str, reporter_name: str, issue_description: str) -> str:
        """강화된 8단계 프로세스 - 성능 최적화 적용"""
        
        start_time = time.time()
        self.performance_tracker.start_tracking(media_name, issue_description)
        
        print(f"START: 강화된 8단계 프로세스 시작 - {media_name} / {reporter_name}")
        
        try:
            # 1. 사용자 인풋 데이터 검증 (기존 유지)
            step_start = time.time()
            if not self.original._validate_inputs(media_name, reporter_name, issue_description):
                return "입력 데이터 검증 실패"
            self.performance_tracker.log_step(1, time.time() - step_start)
            
            # 2. LLM 기반 이슈 초기 분석 (개선: 더 빠른 프롬프트)
            step_start = time.time()
            print("STEP 2: 이슈 초기 분석 (최적화됨)...")
            initial_analysis = self._optimized_issue_analysis(issue_description)
            self.performance_tracker.log_step(2, time.time() - step_start)
            
            # 3. 데이터 기반 부서/위기단계 지정 (기존 유지 + 캐싱)
            step_start = time.time()
            print("STEP 3: 부서 및 위기단계 지정 (캐싱 적용)...")
            cache_key = f"dept_crisis_{hash(issue_description[:100])}"
            
            if self.cache.get(cache_key):
                relevant_depts, crisis_level = self.cache.get(cache_key)
                print("  CACHE HIT: 부서/위기단계 캐시 사용")
            else:
                relevant_depts = self.original.get_relevant_departments_from_master_data(issue_description)
                crisis_level = self.original._assess_crisis_level_from_master_data(issue_description)
                self.cache.set(cache_key, (relevant_depts, crisis_level), ttl=3600)  # 1시간 캐시
            
            media_info = self.original._get_media_info_from_master_data(media_name)
            self.performance_tracker.log_step(3, time.time() - step_start)
            
            # 4-5단계 병렬 처리 (개선: 웹 검색 + 기초 분석 동시 수행)
            step_start = time.time()
            print("STEP 4-5: 웹 검색 + 사실확인 (병렬 처리)...")
            web_results, fact_verification = self._parallel_web_and_fact_check(issue_description, initial_analysis)
            self.performance_tracker.log_step("4-5", time.time() - step_start)
            
            # 6. 부서 의견 생성 (개선: 배치 처리)
            step_start = time.time()
            print("STEP 6: 부서 의견 생성 (배치 최적화)...")
            department_opinions = self._batch_department_opinions(relevant_depts, issue_description, web_results)
            self.performance_tracker.log_step(6, time.time() - step_start)
            
            # 7. PR 전략 수립 (개선: 컨텍스트 압축)
            step_start = time.time()
            print("STEP 7: PR 전략 수립 (최적화됨)...")
            pr_strategy = self._optimized_pr_strategy(issue_description, crisis_level, fact_verification, department_opinions)
            self.performance_tracker.log_step(7, time.time() - step_start)
            
            # 8. 최종 보고서 생성 (기존 구조 유지)
            step_start = time.time()
            print("STEP 8: 최종 보고서 생성...")
            final_report = self.original._generate_final_comprehensive_report(
                media_name=media_name,
                reporter_name=reporter_name,
                issue_description=issue_description,
                initial_analysis=initial_analysis,
                relevant_depts=relevant_depts,
                crisis_level=crisis_level,
                media_info=media_info,
                web_search_results=web_results,
                fact_verification=fact_verification,
                department_opinions=department_opinions,
                pr_strategy=pr_strategy
            )
            self.performance_tracker.log_step(8, time.time() - step_start)
            
            total_time = time.time() - start_time
            print(f"COMPLETE: 강화된 8단계 프로세스 완료 ({total_time:.2f}초)")
            print(f"  위기단계: {crisis_level}, 관련부서: {len(relevant_depts)}개")
            
            # 성능 리포트
            self.performance_tracker.finish_tracking(total_time, len(final_report))
            
            return final_report
            
        except Exception as e:
            error_time = time.time() - start_time
            print(f"ERROR: 처리 실패 ({error_time:.2f}초) - {str(e)}")
            
            # 에러 시 기본 보고서 생성
            return self._generate_fallback_report(media_name, reporter_name, issue_description, str(e))
    
    def _optimized_issue_analysis(self, issue_description: str) -> Dict:
        """최적화된 이슈 초기 분석 (더 짧은 프롬프트)"""
        
        optimized_prompt = f"""
다음 이슈를 간결하게 분석하고 JSON으로 응답하세요:

이슈: {issue_description}

형식:
{{
  "category": "제품품질/환경안전/재무성과/사업운영",
  "complexity": "높음/중간/낮음", 
  "impact_scope": "글로벌/국내/지역",
  "urgency": "높음/중간/낮음",
  "summary": "핵심 요약 (50자 이내)"
}}
        """
        
        try:
            response = self.original.llm.chat(optimized_prompt)
            return json.loads(response)
        except:
            return self._get_default_analysis(issue_description)
    
    def _parallel_web_and_fact_check(self, issue_description: str, initial_analysis: Dict) -> tuple:
        """4-5단계 병렬 처리: 웹 검색과 기초 사실 확인 동시 수행"""
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 웹 검색 (4단계)
            web_future = executor.submit(
                self.original._conduct_web_research, 
                issue_description, initial_analysis
            )
            
            # 기초 사실 분석 준비 (5단계 준비)
            basic_fact_future = executor.submit(
                self._prepare_fact_analysis,
                issue_description, initial_analysis
            )
            
            web_results = web_future.result()
            basic_facts = basic_fact_future.result()
            
            # 웹 결과를 포함한 완전한 사실 확인
            fact_verification = self.original._verify_facts_and_background(
                issue_description, web_results, initial_analysis
            )
            
            return web_results, fact_verification
    
    def _batch_department_opinions(self, relevant_depts: List, issue_description: str, web_results: Dict) -> Dict:
        """부서 의견을 배치로 처리하여 API 호출 최소화"""
        
        if not relevant_depts:
            return {}
        
        # 상위 3개 부서만 처리 (성능 최적화)
        top_depts = relevant_depts[:3]
        
        batch_prompt = f"""
다음 이슈에 대해 {len(top_depts)}개 부서의 의견을 생성하세요:

이슈: {issue_description}
관련 부서: {[dept.get('부서명', '') for dept in top_depts]}

각 부서별로 다음 형식의 JSON 응답:
{{
  "{top_depts[0].get('부서명', 'dept1')}": {{
    "opinion": "해당 부서 관점의 의견 (100자 이내)",
    "action": "권장 조치사항 (50자 이내)"
  }}
}}

모든 부서를 포함하여 응답하세요.
        """
        
        try:
            response = self.original.llm.chat(batch_prompt)
            return json.loads(response)
        except:
            return self._get_default_department_opinions(top_depts)
    
    def _optimized_pr_strategy(self, issue_description: str, crisis_level: str, 
                             fact_verification: Dict, department_opinions: Dict) -> Dict:
        """최적화된 PR 전략 수립 (컨텍스트 압축)"""
        
        # 핵심 정보만 추출하여 프롬프트 크기 축소
        fact_status = fact_verification.get('fact_status', 'N/A')
        credibility = fact_verification.get('credibility', 'N/A')
        
        key_opinions = []
        for dept, opinion in department_opinions.items():
            if isinstance(opinion, dict):
                key_opinions.append(f"{dept}: {opinion.get('opinion', '')[:50]}")
        
        compact_prompt = f"""
PR 전략 수립:

이슈: {issue_description[:100]}
위기단계: {crisis_level}
사실확인: {fact_status} (신뢰도: {credibility})
주요 의견: {'; '.join(key_opinions[:2])}

JSON 응답:
{{
  "communication_tone": "신중함/투명성/적극성",
  "key_messages": ["메시지1", "메시지2", "메시지3"],
  "immediate_actions": ["조치1", "조치2"]
}}
        """
        
        try:
            response = self.original.llm.chat(compact_prompt)
            return json.loads(response)
        except:
            return self._get_default_pr_strategy(crisis_level)
    
    def _prepare_fact_analysis(self, issue_description: str, initial_analysis: Dict) -> Dict:
        """사실 분석 준비 (웹 검색과 병렬 수행)"""
        return {
            "prepared_context": issue_description,
            "analysis_ready": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_default_analysis(self, issue_description: str) -> Dict:
        """기본 분석 결과"""
        return {
            "category": "사업운영",
            "complexity": "중간",
            "impact_scope": "국내", 
            "urgency": "중간",
            "summary": issue_description[:50] + "..." if len(issue_description) > 50 else issue_description
        }
    
    def _get_default_department_opinions(self, depts: List) -> Dict:
        """기본 부서 의견"""
        opinions = {}
        for dept in depts:
            dept_name = dept.get('부서명', '미상')
            opinions[dept_name] = {
                "opinion": f"{dept_name}에서 해당 이슈 검토 중",
                "action": "추가 정보 수집 및 분석"
            }
        return opinions
    
    def _get_default_pr_strategy(self, crisis_level: str) -> Dict:
        """기본 PR 전략"""
        return {
            "communication_tone": "신중함",
            "key_messages": ["정확한 사실 확인", "투명한 소통", "지속적 개선"],
            "immediate_actions": ["관련 부서 협의", "추가 조사 실시"]
        }
    
    def _generate_fallback_report(self, media_name: str, reporter_name: str, 
                                issue_description: str, error_msg: str) -> str:
        """에러 시 기본 보고서"""
        return f"""
<이슈 발생 보고>

1. 발생 일시: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}

2. 발생 단계: 2단계(주의)

3. 발생 내용:
({media_name} {reporter_name})
{issue_description}

4. 유관 의견:
- 사실 확인: 현재 관련 부서에서 사실 관계 확인 중
- 설명 논리: 정확한 정보 파악 후 투명한 소통 예정
- 메시지 방향성: 신중하고 책임감 있는 대응

5. 대응 방안:
- 원보이스: '정확한 사실 확인 후 성실히 대응하겠습니다'
- 이후 대응 방향성: 관련 부서 긴급 회의 및 추가 조사

6. 대응 결과: (추후 업데이트)

※ 시스템 처리 중 일시적 오류가 발생하여 기본 형식으로 생성되었습니다.
상세 분석이 필요한 경우 재실행을 권장합니다.

오류 정보: {error_msg}
        """


class PerformanceTracker:
    """성능 추적기"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.start_time = None
        self.step_times = {}
        self.current_case = None
    
    def start_tracking(self, media_name: str, issue: str):
        self.start_time = time.time()
        self.current_case = f"{media_name}_{hash(issue) % 10000}"
        self.step_times = {}
        
    def log_step(self, step_num, duration):
        self.step_times[step_num] = duration
        print(f"  TIMING: Step {step_num} - {duration:.2f}초")
    
    def finish_tracking(self, total_time: float, report_length: int):
        performance_summary = {
            "case": self.current_case,
            "total_time": total_time,
            "report_length": report_length,
            "step_times": self.step_times,
            "timestamp": datetime.now().isoformat()
        }
        
        # 성능 로그 저장 (선택적)
        try:
            with open("performance_log.json", "a", encoding="utf-8") as f:
                f.write(json.dumps(performance_summary, ensure_ascii=False) + "\n")
        except:
            pass  # 로그 실패해도 메인 기능에 영향 없음


class SimpleCache:
    """간단한 메모리 캐시"""
    
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """캐시 설정 (TTL: 초 단위)"""
        self.cache[key] = value
        self.timestamps[key] = time.time() + ttl
    
    def get(self, key: str) -> Any:
        """캐시 조회"""
        if key not in self.cache:
            return None
            
        if time.time() > self.timestamps.get(key, 0):
            # TTL 만료
            self.cache.pop(key, None)
            self.timestamps.pop(key, None)
            return None
            
        return self.cache[key]
    
    def clear(self):
        """캐시 클리어"""
        self.cache.clear()
        self.timestamps.clear()


def main():
    """테스트 함수"""
    print("강화된 DataBasedLLM 테스트")
    
    # 실제 사용 예시 (원래 DataBasedLLM 필요)
    print("실제 사용을 위해서는 다음과 같이 사용:")
    print("""
from data_based_llm import DataBasedLLM
from enhanced_data_based_llm import EnhancedDataBasedLLM

# 기존 시스템 래핑
original_llm = DataBasedLLM()
enhanced_llm = EnhancedDataBasedLLM(original_llm)

# 강화된 처리
report = enhanced_llm.generate_comprehensive_issue_report_enhanced(
    "조선일보", "김기자", "포스코 관련 이슈"
)
    """)

if __name__ == "__main__":
    main()