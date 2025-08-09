#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
기술적 성능 향상 시스템
캐싱, 병렬처리, 에러복구 기능 구현
"""

import asyncio
import json
import os
import time
import hashlib
import pickle
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools
import sqlite3
from threading import Lock

@dataclass
class CacheEntry:
    """캐시 엔트리 데이터 클래스"""
    key: str
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = None

class SmartCache:
    """지능형 캐싱 시스템"""
    
    def __init__(self, cache_dir: str = "data/cache", max_size_mb: int = 100):
        self.cache_dir = cache_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.memory_cache = {}
        self.cache_lock = Lock()
        self.setup_cache_dir()
        self.setup_logging()
    
    def setup_cache_dir(self):
        """캐시 디렉토리 설정"""
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(f"{self.cache_dir}/memory", exist_ok=True)
        os.makedirs(f"{self.cache_dir}/disk", exist_ok=True)
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_cache_key(self, *args, **kwargs) -> str:
        """캐시 키 생성"""
        # 입력 파라미터 기반 해시 생성
        cache_data = {
            'args': args,
            'kwargs': kwargs
        }
        cache_string = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def get(self, key: str, default=None) -> Any:
        """캐시에서 값 조회"""
        with self.cache_lock:
            # 메모리 캐시 먼저 확인
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if datetime.now() < entry.expires_at:
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()
                    return entry.value
                else:
                    # 만료된 엔트리 제거
                    del self.memory_cache[key]
            
            # 디스크 캐시 확인
            disk_path = f"{self.cache_dir}/disk/{key}.pkl"
            if os.path.exists(disk_path):
                try:
                    with open(disk_path, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if datetime.now() < entry.expires_at:
                        # 메모리 캐시로 승격
                        self.memory_cache[key] = entry
                        entry.access_count += 1
                        entry.last_accessed = datetime.now()
                        return entry.value
                    else:
                        # 만료된 파일 제거
                        os.remove(disk_path)
                except Exception as e:
                    self.logger.error(f"Cache read error: {e}")
                    if os.path.exists(disk_path):
                        os.remove(disk_path)
        
        return default
    
    def set(self, key: str, value: Any, ttl_hours: int = 24, priority: str = "normal"):
        """캐시에 값 저장"""
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now(),
            expires_at=expires_at,
            last_accessed=datetime.now()
        )
        
        with self.cache_lock:
            # 우선순위에 따라 저장 위치 결정
            if priority == "high" or self._should_store_in_memory(entry):
                self.memory_cache[key] = entry
                
                # 메모리 사이즈 체크 및 정리
                self._cleanup_memory_cache()
            else:
                # 디스크에 저장
                self._store_to_disk(key, entry)
        
        self.logger.info(f"Cache set: {key} (priority: {priority}, ttl: {ttl_hours}h)")
    
    def _should_store_in_memory(self, entry: CacheEntry) -> bool:
        """메모리 저장 여부 결정"""
        # 작은 데이터는 메모리에 저장
        value_size = len(str(entry.value))
        return value_size < 10000  # 10KB 미만
    
    def _store_to_disk(self, key: str, entry: CacheEntry):
        """디스크에 캐시 저장"""
        try:
            disk_path = f"{self.cache_dir}/disk/{key}.pkl"
            with open(disk_path, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            self.logger.error(f"Disk cache write error: {e}")
    
    def _cleanup_memory_cache(self):
        """메모리 캐시 정리"""
        if len(self.memory_cache) > 1000:  # 최대 1000개 엔트리
            # LRU 방식으로 정리
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: (x[1].last_accessed or x[1].created_at)
            )
            
            # 오래된 엔트리의 절반 제거
            items_to_remove = len(sorted_items) // 2
            for key, _ in sorted_items[:items_to_remove]:
                del self.memory_cache[key]
    
    def clear_expired(self):
        """만료된 캐시 정리"""
        now = datetime.now()
        
        with self.cache_lock:
            # 메모리 캐시 정리
            expired_keys = [
                key for key, entry in self.memory_cache.items()
                if now >= entry.expires_at
            ]
            for key in expired_keys:
                del self.memory_cache[key]
            
            # 디스크 캐시 정리
            disk_cache_dir = f"{self.cache_dir}/disk"
            for filename in os.listdir(disk_cache_dir):
                if filename.endswith('.pkl'):
                    filepath = os.path.join(disk_cache_dir, filename)
                    try:
                        with open(filepath, 'rb') as f:
                            entry = pickle.load(f)
                        if now >= entry.expires_at:
                            os.remove(filepath)
                    except Exception as e:
                        self.logger.error(f"Cache cleanup error: {e}")
                        os.remove(filepath)  # 손상된 파일 제거

def cache_result(ttl_hours: int = 24, priority: str = "normal"):
    """캐싱 데코레이터"""
    def decorator(func: Callable):
        cache = SmartCache()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{func.__name__}_{cache.get_cache_key(*args, **kwargs)}"
            
            # 캐시에서 조회
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 캐시 미스 - 함수 실행
            result = func(*args, **kwargs)
            
            # 결과 캐싱
            cache.set(cache_key, result, ttl_hours, priority)
            
            return result
        
        return wrapper
    return decorator

class ParallelProcessor:
    """병렬 처리 시스템"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger(__name__)
    
    async def process_parallel(self, tasks: List[Tuple[Callable, tuple, dict]]) -> List[Any]:
        """병렬 작업 처리"""
        loop = asyncio.get_event_loop()
        
        # 각 작업을 Future로 변환
        futures = []
        for func, args, kwargs in tasks:
            future = loop.run_in_executor(self.executor, func, *args, **kwargs)
            futures.append(future)
        
        # 모든 작업 완료 대기
        try:
            results = await asyncio.gather(*futures, return_exceptions=True)
            return results
        except Exception as e:
            self.logger.error(f"Parallel processing error: {e}")
            return []
    
    def process_with_timeout(self, func: Callable, timeout: float, *args, **kwargs) -> Any:
        """타임아웃을 가진 작업 처리"""
        future = self.executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            self.logger.error(f"Task timeout: {func.__name__}")
            future.cancel()
            return None
        except Exception as e:
            self.logger.error(f"Task error: {func.__name__} - {e}")
            return None

class ErrorRecoverySystem:
    """에러 복구 시스템"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.error_history = {}
        self.logger = logging.getLogger(__name__)
    
    def with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """재시도를 포함한 함수 실행"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # 성공 시 에러 기록 초기화
                func_key = f"{func.__name__}_{id(args)}_{id(kwargs)}"
                if func_key in self.error_history:
                    del self.error_history[func_key]
                
                return result
                
            except Exception as e:
                last_exception = e
                func_key = f"{func.__name__}_{id(args)}_{id(kwargs)}"
                
                # 에러 기록
                if func_key not in self.error_history:
                    self.error_history[func_key] = []
                self.error_history[func_key].append({
                    'attempt': attempt,
                    'error': str(e),
                    'timestamp': datetime.now()
                })
                
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)  # 지수 백오프
                    self.logger.warning(f"Retry {attempt + 1}/{self.max_retries} for {func.__name__} after {delay}s: {e}")
                    time.sleep(delay)
                else:
                    self.logger.error(f"All retries failed for {func.__name__}: {e}")
        
        raise last_exception
    
    def with_fallback(self, primary_func: Callable, fallback_func: Callable, 
                     *args, **kwargs) -> Any:
        """폴백을 포함한 함수 실행"""
        try:
            return self.with_retry(primary_func, *args, **kwargs)
        except Exception as e:
            self.logger.warning(f"Primary function failed, using fallback: {e}")
            try:
                return self.with_retry(fallback_func, *args, **kwargs)
            except Exception as fallback_error:
                self.logger.error(f"Fallback also failed: {fallback_error}")
                raise e  # 원래 에러를 던짐
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """에러 통계 조회"""
        stats = {
            'total_functions_with_errors': len(self.error_history),
            'functions': {}
        }
        
        for func_key, errors in self.error_history.items():
            stats['functions'][func_key] = {
                'error_count': len(errors),
                'last_error': errors[-1] if errors else None,
                'error_types': list(set(error['error'] for error in errors))
            }
        
        return stats

class PerformanceEnhancer:
    """통합 성능 향상 시스템"""
    
    def __init__(self):
        self.cache = SmartCache()
        self.parallel_processor = ParallelProcessor()
        self.error_recovery = ErrorRecoverySystem()
        self.logger = logging.getLogger(__name__)
    
    # 부서 매핑 최적화
    @cache_result(ttl_hours=6, priority="high")
    def get_cached_department_mapping(self, issue_description: str, 
                                    master_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """캐시된 부서 매핑"""
        return self._compute_department_mapping(issue_description, master_data)
    
    def _compute_department_mapping(self, issue_description: str, 
                                  master_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """부서 매핑 계산 (실제 로직)"""
        # 실제 구현에서는 data_based_llm.py의 로직 사용
        departments = master_data.get('departments', [])
        relevant_departments = []
        
        for dept in departments:
            keywords = dept.get('keywords', [])
            score = sum(1 for keyword in keywords if keyword in issue_description)
            
            if score > 0:
                dept_info = dept.copy()
                dept_info['relevance_score'] = score
                relevant_departments.append(dept_info)
        
        return sorted(relevant_departments, key=lambda x: x['relevance_score'], reverse=True)[:3]
    
    # 웹 검색 최적화
    async def enhanced_web_search(self, search_queries: List[str]) -> Dict[str, Any]:
        """향상된 웹 검색 (병렬 처리)"""
        # 병렬 검색 작업 정의
        search_tasks = []
        for query in search_queries:
            search_tasks.append((self._single_web_search, (query,), {}))
        
        # 병렬 실행
        results = await self.parallel_processor.process_parallel(search_tasks)
        
        # 결과 통합
        combined_results = {
            'queries': search_queries,
            'results': [r for r in results if r is not None],
            'search_time': time.time(),
            'success_count': len([r for r in results if r is not None])
        }
        
        return combined_results
    
    def _single_web_search(self, query: str) -> Optional[Dict[str, Any]]:
        """단일 웹 검색 (에러 복구 포함)"""
        def search_with_retry():
            # 실제 웹 검색 로직 (모의)
            time.sleep(0.5)  # API 호출 시뮬레이션
            return {
                'query': query,
                'results': [f"Result for {query}"],
                'timestamp': datetime.now().isoformat()
            }
        
        def fallback_search():
            # 폴백 검색 로직
            return {
                'query': query,
                'results': [f"Cached result for {query}"],
                'source': 'fallback'
            }
        
        try:
            return self.error_recovery.with_fallback(
                search_with_retry, 
                fallback_search
            )
        except Exception as e:
            self.logger.error(f"Web search failed completely for query '{query}': {e}")
            return None
    
    # LLM 호출 최적화
    def optimized_llm_call(self, prompt: str, context: Dict[str, Any], 
                          timeout: float = 30.0) -> Optional[str]:
        """최적화된 LLM 호출"""
        # 캐시 키 생성
        cache_key = f"llm_{hashlib.md5(prompt.encode()).hexdigest()}"
        
        # 캐시 확인
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # LLM 호출 (타임아웃 포함)
        def llm_call():
            # 실제 LLM API 호출 로직
            time.sleep(2)  # API 호출 시뮬레이션
            return f"LLM response for: {prompt[:50]}..."
        
        def fallback_response():
            return f"Fallback response based on template for: {prompt[:50]}..."
        
        try:
            result = self.error_recovery.with_fallback(
                lambda: self.parallel_processor.process_with_timeout(llm_call, timeout),
                fallback_response
            )
            
            # 성공한 결과만 캐싱
            if result and "Fallback" not in result:
                self.cache.set(cache_key, result, ttl_hours=2, priority="normal")
            
            return result
            
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return None
    
    # 종합 보고서 생성 최적화
    async def generate_optimized_report(self, media_name: str, reporter_name: str, 
                                      issue_description: str) -> Dict[str, Any]:
        """최적화된 보고서 생성"""
        start_time = time.time()
        
        try:
            # 1단계: 기본 데이터 병렬 로딩
            data_loading_tasks = [
                (self._load_master_data, (), {}),
                (self._load_risk_template, (), {}),
                (self._analyze_issue_keywords, (issue_description,), {})
            ]
            
            master_data, risk_template, keywords = await self.parallel_processor.process_parallel(data_loading_tasks)
            
            # 2단계: 부서 매핑 (캐시 활용)
            relevant_departments = self.get_cached_department_mapping(issue_description, master_data)
            
            # 3단계: 웹 검색 (병렬)
            search_queries = [issue_description] + keywords[:2]  # 최대 3개 쿼리
            web_results = await self.enhanced_web_search(search_queries)
            
            # 4단계: LLM 기반 분석 (최적화)
            analysis_prompt = f"Analyze issue: {issue_description}"
            analysis_result = self.optimized_llm_call(analysis_prompt, {
                'departments': relevant_departments,
                'web_data': web_results
            })
            
            # 5단계: 최종 보고서 조립
            final_report = self._assemble_report({
                'media_name': media_name,
                'reporter_name': reporter_name,
                'issue_description': issue_description,
                'departments': relevant_departments,
                'web_results': web_results,
                'analysis': analysis_result,
                'template': risk_template
            })
            
            processing_time = time.time() - start_time
            
            return {
                'report': final_report,
                'processing_time': processing_time,
                'performance_metrics': {
                    'cache_hits': self._get_cache_hit_count(),
                    'parallel_tasks': 6,  # 실행된 병렬 작업 수
                    'error_count': len(self.error_recovery.error_history)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return {
                'report': f"Error generating report: {e}",
                'processing_time': time.time() - start_time,
                'error': True
            }
    
    def _load_master_data(self) -> Dict[str, Any]:
        """마스터 데이터 로딩"""
        # 실제 구현에서는 JSON 파일 로딩
        return {'departments': [], 'crisis_levels': []}
    
    def _load_risk_template(self) -> str:
        """위험 보고서 템플릿 로딩"""
        return "Risk report template..."
    
    def _analyze_issue_keywords(self, issue_description: str) -> List[str]:
        """이슈 키워드 분석"""
        # 간단한 키워드 추출
        keywords = ['품질', '안전', '환경'] if '품질' in issue_description else ['일반']
        return keywords
    
    def _assemble_report(self, data: Dict[str, Any]) -> str:
        """최종 보고서 조립"""
        return f"""
최적화된 이슈 발생 보고서

언론사: {data['media_name']}
기자명: {data['reporter_name']}
이슈: {data['issue_description']}

관련 부서: {len(data['departments'])}개
웹 검색 결과: {data['web_results']['success_count']}건
AI 분석: {data['analysis'][:100] if data['analysis'] else 'N/A'}...

[최적화된 처리 완료]
"""
    
    def _get_cache_hit_count(self) -> int:
        """캐시 히트 수 조회"""
        return len(self.cache.memory_cache)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 보고서 생성"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cache_statistics': {
                'memory_entries': len(self.cache.memory_cache),
                'disk_entries': len(os.listdir(f"{self.cache.cache_dir}/disk"))
            },
            'error_statistics': self.error_recovery.get_error_statistics(),
            'parallel_processing': {
                'max_workers': self.parallel_processor.max_workers
            }
        }

# 사용 예제
async def example_usage():
    """사용 예제"""
    enhancer = PerformanceEnhancer()
    
    # 최적화된 보고서 생성
    result = await enhancer.generate_optimized_report(
        "조선일보",
        "김철수", 
        "포스코인터내셔널 제품 품질 이슈 발생"
    )
    
    print("생성된 보고서:")
    print(result['report'])
    print(f"\n처리 시간: {result['processing_time']:.2f}초")
    print(f"성능 지표: {result['performance_metrics']}")
    
    # 성능 보고서
    performance_report = enhancer.get_performance_report()
    print(f"\n성능 보고서: {performance_report}")

if __name__ == "__main__":
    asyncio.run(example_usage())