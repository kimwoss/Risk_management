#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 모델 성능 최적화 시스템
프롬프트 A/B 테스트, 모델 비교, 동적 최적화
"""

import json
import os
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import random

@dataclass
class PromptVariant:
    """프롬프트 변형 데이터 클래스"""
    id: str
    name: str
    prompt_template: str
    performance_score: float = 0.0
    usage_count: int = 0
    success_rate: float = 0.0

@dataclass
class ABTestResult:
    """A/B 테스트 결과"""
    test_id: str
    variant_a_id: str
    variant_b_id: str
    variant_a_score: float
    variant_b_score: float
    winner_id: str
    confidence: float
    sample_size: int

class PromptOptimizer:
    """프롬프트 최적화 클래스"""
    
    def __init__(self, variants_file: str = "data/prompt_variants.json"):
        self.variants_file = variants_file
        self.variants = {}
        self.test_results = []
        self.load_variants()
    
    def load_variants(self):
        """저장된 프롬프트 변형들 로드"""
        if os.path.exists(self.variants_file):
            with open(self.variants_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for category, variants_data in data.items():
                    self.variants[category] = [
                        PromptVariant(**variant_data) for variant_data in variants_data
                    ]
        else:
            self.init_default_variants()
    
    def save_variants(self):
        """프롬프트 변형들 저장"""
        os.makedirs(os.path.dirname(self.variants_file), exist_ok=True)
        data = {}
        for category, variants in self.variants.items():
            data[category] = [variant.__dict__ for variant in variants]
        
        with open(self.variants_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def init_default_variants(self):
        """기본 프롬프트 변형들 초기화"""
        
        # 이슈 분석용 프롬프트 변형들
        self.variants['issue_analysis'] = [
            PromptVariant(
                id="analysis_v1",
                name="상세 분석형",
                prompt_template="""다음 이슈를 체계적으로 분석해주세요:

이슈 내용: {issue_description}

분석 항목:
1. 이슈 카테고리: (제품/환경/법무/경영/기타)
2. 복잡도: (단순/보통/복잡/매우복잡) 
3. 영향 범위: (내부/업계/사회전반)
4. 시급성: (낮음/보통/높음/매우높음)
5. 핵심 리스크: (주요 위험 요소)

JSON 형식으로 응답해주세요."""
            ),
            PromptVariant(
                id="analysis_v2", 
                name="간결 분석형",
                prompt_template="""이슈 분석: {issue_description}

다음 형식으로 분석해주세요:
- 카테고리: 
- 복잡도:
- 시급성:
- 핵심리스크:

JSON 형식 응답 필수."""
            ),
            PromptVariant(
                id="analysis_v3",
                name="전문가 관점형", 
                prompt_template="""위기관리 전문가로서 다음 이슈를 분석하세요:
{issue_description}

전문가 분석:
• 이슈 성격과 파급력 평가
• 대응 시급도 판단 (4단계)
• 관련 부서 및 이해관계자 예상
• 리스크 우선순위

구조화된 JSON으로 답변하세요."""
            )
        ]
        
        # 부서 의견 생성용 프롬프트 변형들
        self.variants['department_opinion'] = [
            PromptVariant(
                id="dept_v1",
                name="역할 몰입형",
                prompt_template="""당신은 포스코인터내셔널 {department}의 {position} 담당자입니다.

현재 이슈: {issue_description}
담당 영역: {responsibilities}

담당자 관점에서 다음에 대해 의견을 제시해주세요:
1. 사실 관계 확인 사항
2. 우리 부서 관련 주요 우려점
3. 즉시 필요한 대응 조치
4. 다른 부서와의 협조 사항

실무진 관점에서 구체적으로 답변해주세요."""
            ),
            PromptVariant(
                id="dept_v2",
                name="체크리스트형",
                prompt_template="""{department} 부서 검토 의견:

이슈: {issue_description}

□ 사실확인: 
□ 위험요소: 
□ 대응방안: 
□ 필요협조: 

각 항목을 전문가 관점에서 체크해주세요."""
            )
        ]
        
        # PR 전략용 프롬프트 변형들  
        self.variants['pr_strategy'] = [
            PromptVariant(
                id="pr_v1",
                name="전략적 접근형",
                prompt_template="""포스코인터내셔널 언론홍보 책임자로서 대응전략을 수립하세요.

이슈 상황: {issue_description}
위기 단계: {crisis_level}
관련 부서: {departments}

전략 수립:
1. 커뮤니케이션 기조 (투명성/신속성/책임감)
2. 핵심 메시지 (3가지)
3. 대상별 맞춤 메시지 (언론/고객/임직원)
4. 즉시 대응사항 (24시간 내)
5. 중장기 평판 관리 방안

포스코인터내셔널 브랜드 가치를 보호하는 관점에서 답변하세요."""
            ),
            PromptVariant(
                id="pr_v2",
                name="위기대응 매뉴얼형", 
                prompt_template="""위기대응 매뉴얼:

상황: {issue_description}
위기등급: {crisis_level}

Step 1: 즉시대응 (1시간 내)
Step 2: 공식발표 (24시간 내)  
Step 3: 후속조치 (1주일 내)

각 단계별 구체적 Action Plan을 제시하세요."""
            )
        ]
        
        self.save_variants()
    
    def get_best_prompt(self, category: str, context: Dict[str, Any] = None) -> PromptVariant:
        """카테고리별 최적 프롬프트 선택"""
        if category not in self.variants:
            raise ValueError(f"Unknown category: {category}")
        
        variants = self.variants[category]
        
        # 성능 기반 선택 (80%) + 탐험 (20%)
        if random.random() < 0.8 and any(v.performance_score > 0 for v in variants):
            # 성능이 좋은 것 선택
            best_variant = max(variants, key=lambda x: x.performance_score)
        else:
            # 랜덤 선택 (탐험)
            best_variant = random.choice(variants)
        
        best_variant.usage_count += 1
        return best_variant
    
    def update_performance(self, variant_id: str, score: float, success: bool):
        """프롬프트 성능 업데이트"""
        for category_variants in self.variants.values():
            for variant in category_variants:
                if variant.id == variant_id:
                    # 이동평균으로 성능 점수 업데이트
                    alpha = 0.1  # 학습률
                    variant.performance_score = (1 - alpha) * variant.performance_score + alpha * score
                    
                    # 성공률 업데이트
                    if variant.usage_count > 0:
                        current_success_count = variant.success_rate * (variant.usage_count - 1)
                        if success:
                            current_success_count += 1
                        variant.success_rate = current_success_count / variant.usage_count
                    
                    break
        
        self.save_variants()
    
    def run_ab_test(self, category: str, sample_size: int = 10) -> ABTestResult:
        """A/B 테스트 실행"""
        if category not in self.variants or len(self.variants[category]) < 2:
            raise ValueError(f"Need at least 2 variants for category: {category}")
        
        variants = self.variants[category]
        variant_a, variant_b = random.sample(variants, 2)
        
        test_id = f"test_{category}_{int(time.time())}"
        
        print(f"A/B 테스트 시작: {variant_a.name} vs {variant_b.name}")
        
        # 실제 테스트는 운영 중 자동으로 수행됨
        # 여기서는 테스트 프레임워크만 설정
        
        test_result = ABTestResult(
            test_id=test_id,
            variant_a_id=variant_a.id,
            variant_b_id=variant_b.id,
            variant_a_score=variant_a.performance_score,
            variant_b_score=variant_b.performance_score,
            winner_id=variant_a.id if variant_a.performance_score > variant_b.performance_score else variant_b.id,
            confidence=0.95,  # 임시값
            sample_size=sample_size
        )
        
        self.test_results.append(test_result)
        return test_result
    
    def generate_optimization_report(self) -> Dict[str, Any]:
        """최적화 보고서 생성"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'categories': {}
        }
        
        for category, variants in self.variants.items():
            best_variant = max(variants, key=lambda x: x.performance_score)
            
            report['categories'][category] = {
                'total_variants': len(variants),
                'best_variant': {
                    'name': best_variant.name,
                    'performance_score': best_variant.performance_score,
                    'success_rate': best_variant.success_rate,
                    'usage_count': best_variant.usage_count
                },
                'avg_performance': sum(v.performance_score for v in variants) / len(variants),
                'total_usage': sum(v.usage_count for v in variants)
            }
        
        return report

class ModelComparator:
    """다중 모델 성능 비교"""
    
    def __init__(self):
        self.models = {
            'gpt-4': {'cost_per_token': 0.00003, 'speed_factor': 1.0},
            'gpt-4-turbo': {'cost_per_token': 0.00001, 'speed_factor': 1.5},
            'gpt-3.5-turbo': {'cost_per_token': 0.000002, 'speed_factor': 2.0}
        }
        self.performance_history = {}
    
    def compare_models(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """모델별 성능 비교"""
        results = {}
        
        for model_name in self.models.keys():
            # 각 모델별 성능 측정 (실제 구현 시에는 실제 API 호출)
            results[model_name] = {
                'response_quality': random.uniform(0.7, 1.0),  # 임시값
                'processing_time': random.uniform(2.0, 8.0) / self.models[model_name]['speed_factor'],
                'cost_estimate': len(prompt) * self.models[model_name]['cost_per_token'],
                'error_rate': random.uniform(0.0, 0.1)
            }
        
        # 종합 점수 계산 (품질 50%, 속도 30%, 비용 20%)
        for model_name, metrics in results.items():
            score = (
                metrics['response_quality'] * 0.5 +
                (1.0 - min(metrics['processing_time'] / 10.0, 1.0)) * 0.3 +
                (1.0 - min(metrics['cost_estimate'] / 0.1, 1.0)) * 0.2
            )
            results[model_name]['overall_score'] = score
        
        return results
    
    def recommend_best_model(self, use_case: str) -> str:
        """사용 사례별 최적 모델 추천"""
        if use_case == 'fast_response':
            return 'gpt-3.5-turbo'
        elif use_case == 'high_quality':
            return 'gpt-4'
        elif use_case == 'balanced':
            return 'gpt-4-turbo'
        else:
            return 'gpt-4-turbo'

class ContinuousLearner:
    """지속적 학습 시스템"""
    
    def __init__(self, optimizer: PromptOptimizer):
        self.optimizer = optimizer
        self.learning_patterns = []
    
    def analyze_user_corrections(self, original_output: str, corrected_output: str) -> Dict[str, Any]:
        """사용자 수정사항 분석"""
        patterns = {
            'common_corrections': [],
            'improvement_areas': [],
            'pattern_frequency': {}
        }
        
        # 간단한 패턴 분석 (실제로는 더 정교한 NLP 분석 필요)
        if '부서' in corrected_output and '부서' not in original_output:
            patterns['common_corrections'].append('missing_department_info')
        
        if len(corrected_output) > len(original_output) * 1.5:
            patterns['improvement_areas'].append('insufficient_detail')
        
        return patterns
    
    def adapt_prompts(self, correction_patterns: Dict[str, Any]):
        """수정 패턴 기반 프롬프트 적응"""
        for category, variants in self.optimizer.variants.items():
            for variant in variants:
                if 'missing_department_info' in correction_patterns['common_corrections']:
                    if '부서' not in variant.prompt_template:
                        # 부서 관련 내용 추가
                        variant.prompt_template += "\n\n관련 부서 정보를 반드시 포함해주세요."
        
        self.optimizer.save_variants()

# 사용 예제
def example_usage():
    """사용 예제"""
    optimizer = PromptOptimizer()
    
    # 최적 프롬프트 선택
    best_prompt = optimizer.get_best_prompt('issue_analysis')
    print(f"선택된 프롬프트: {best_prompt.name}")
    
    # 성능 피드백
    optimizer.update_performance(best_prompt.id, score=0.85, success=True)
    
    # A/B 테스트 실행
    test_result = optimizer.run_ab_test('issue_analysis')
    print(f"A/B 테스트 완료. 승자: {test_result.winner_id}")
    
    # 최적화 보고서 생성
    report = optimizer.generate_optimization_report()
    print("최적화 보고서 생성 완료")

if __name__ == "__main__":
    example_usage()