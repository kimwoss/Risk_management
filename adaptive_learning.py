#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
지속적 학습 시스템
사용자 피드백 기반 자동 개선 시스템
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import hashlib
import re
from collections import Counter, defaultdict
import logging

@dataclass
class LearningPattern:
    """학습 패턴 데이터 클래스"""
    pattern_id: str
    pattern_type: str  # 'correction', 'enhancement', 'error'
    description: str
    frequency: int
    confidence: float
    last_observed: str
    impact_score: float

@dataclass
class AdaptationRule:
    """적응 규칙 데이터 클래스"""
    rule_id: str
    trigger_pattern: str
    action_type: str  # 'prompt_modify', 'template_update', 'logic_adjust'
    action_description: str
    effectiveness_score: float
    created_at: str
    last_applied: str

class AdaptiveLearner:
    """적응형 학습 시스템"""
    
    def __init__(self, data_path: str = "data/adaptive_learning.db"):
        self.data_path = data_path
        self.patterns_cache = {}
        self.rules_cache = {}
        self.init_database()
        self.setup_logging()
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            filename="data/adaptive_learning.log",
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """학습 데이터베이스 초기화"""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            
            # 사용자 수정사항 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    original_output TEXT NOT NULL,
                    corrected_output TEXT NOT NULL,
                    correction_type TEXT,
                    user_feedback TEXT,
                    issue_category TEXT,
                    processing_context TEXT
                )
            """)
            
            # 학습 패턴 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_patterns (
                    pattern_id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    confidence REAL DEFAULT 0.5,
                    last_observed TEXT NOT NULL,
                    impact_score REAL DEFAULT 0.5
                )
            """)
            
            # 적응 규칙 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS adaptation_rules (
                    rule_id TEXT PRIMARY KEY,
                    trigger_pattern TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_description TEXT NOT NULL,
                    effectiveness_score REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    last_applied TEXT,
                    application_count INTEGER DEFAULT 0
                )
            """)
            
            # 적응 효과 추적 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS adaptation_effects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL,
                    applied_at TEXT NOT NULL,
                    before_metrics TEXT,
                    after_metrics TEXT,
                    effectiveness REAL,
                    FOREIGN KEY (rule_id) REFERENCES adaptation_rules (rule_id)
                )
            """)
    
    def record_user_correction(self, original_output: str, corrected_output: str, 
                              context: Dict[str, Any], feedback: str = ""):
        """사용자 수정사항 기록"""
        correction_type = self._classify_correction_type(original_output, corrected_output)
        
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_corrections 
                (timestamp, original_output, corrected_output, correction_type, 
                 user_feedback, issue_category, processing_context)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                original_output,
                corrected_output,
                correction_type,
                feedback,
                context.get('issue_category', ''),
                json.dumps(context)
            ))
        
        # 즉시 패턴 분석 수행
        self.analyze_correction_patterns()
        self.logger.info(f"User correction recorded: {correction_type}")
    
    def _classify_correction_type(self, original: str, corrected: str) -> str:
        """수정 유형 분류"""
        original_len = len(original.split())
        corrected_len = len(corrected.split())
        
        # 길이 기반 분류
        if corrected_len > original_len * 1.5:
            return "insufficient_detail"
        elif corrected_len < original_len * 0.5:
            return "excessive_detail"
        
        # 키워드 기반 분류
        missing_keywords = self._find_missing_keywords(original, corrected)
        if missing_keywords:
            return "missing_information"
        
        # 구조적 변경
        if self._has_structural_changes(original, corrected):
            return "structural_improvement"
        
        # 톤앤매너 변경
        if self._has_tone_changes(original, corrected):
            return "tone_adjustment"
        
        return "general_improvement"
    
    def _find_missing_keywords(self, original: str, corrected: str) -> List[str]:
        """원본에 누락된 키워드 찾기"""
        important_keywords = ['부서', '담당자', '연락처', '대응방안', '시급성', '위험도']
        missing = []
        
        for keyword in important_keywords:
            if keyword not in original and keyword in corrected:
                missing.append(keyword)
        
        return missing
    
    def _has_structural_changes(self, original: str, corrected: str) -> bool:
        """구조적 변경 여부 판단"""
        # 섹션 헤더 패턴 확인
        original_headers = re.findall(r'\d+\.\s*[^:\n]+:', original)
        corrected_headers = re.findall(r'\d+\.\s*[^:\n]+:', corrected)
        
        return len(corrected_headers) != len(original_headers)
    
    def _has_tone_changes(self, original: str, corrected: str) -> bool:
        """톤앤매너 변경 여부 판단"""
        formal_words = ['검토', '확인', '추진', '협조', '조치']
        urgent_words = ['즉시', '긴급', '신속', '우선', '중요']
        
        original_formal = sum(1 for word in formal_words if word in original)
        corrected_formal = sum(1 for word in formal_words if word in corrected)
        
        original_urgent = sum(1 for word in urgent_words if word in original)
        corrected_urgent = sum(1 for word in urgent_words if word in corrected)
        
        return abs(corrected_formal - original_formal) > 2 or abs(corrected_urgent - original_urgent) > 2
    
    def analyze_correction_patterns(self):
        """수정 패턴 분석"""
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            
            # 최근 30일 수정사항 분석
            cursor.execute("""
                SELECT correction_type, COUNT(*) as frequency, 
                       user_feedback, issue_category
                FROM user_corrections 
                WHERE timestamp >= date('now', '-30 days')
                GROUP BY correction_type, issue_category
                ORDER BY frequency DESC
            """)
            
            results = cursor.fetchall()
            
            for row in results:
                correction_type, frequency, feedback, category = row
                
                pattern_id = f"{correction_type}_{category or 'general'}"
                confidence = min(0.95, 0.5 + (frequency * 0.1))  # 빈도 기반 신뢰도
                
                # 패턴 저장/업데이트
                self._update_pattern(
                    pattern_id=pattern_id,
                    pattern_type="correction",
                    description=f"{correction_type} in {category or 'general'} issues",
                    frequency=frequency,
                    confidence=confidence,
                    impact_score=self._calculate_impact_score(correction_type, frequency)
                )
    
    def _update_pattern(self, pattern_id: str, pattern_type: str, description: str,
                       frequency: int, confidence: float, impact_score: float):
        """패턴 업데이트"""
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO learning_patterns
                (pattern_id, pattern_type, description, frequency, confidence, 
                 last_observed, impact_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                pattern_id,
                pattern_type,
                description,
                frequency,
                confidence,
                datetime.now().isoformat(),
                impact_score
            ))
        
        self.logger.info(f"Pattern updated: {pattern_id} (confidence: {confidence:.2f})")
    
    def _calculate_impact_score(self, correction_type: str, frequency: int) -> float:
        """영향 점수 계산"""
        type_weights = {
            'insufficient_detail': 0.8,
            'missing_information': 0.9,
            'structural_improvement': 0.7,
            'tone_adjustment': 0.6,
            'excessive_detail': 0.5,
            'general_improvement': 0.4
        }
        
        base_score = type_weights.get(correction_type, 0.5)
        frequency_multiplier = min(2.0, 1.0 + (frequency * 0.1))
        
        return min(1.0, base_score * frequency_multiplier)
    
    def generate_adaptation_rules(self):
        """적응 규칙 생성"""
        patterns = self._get_high_confidence_patterns()
        
        for pattern in patterns:
            rule = self._create_rule_from_pattern(pattern)
            if rule:
                self._save_adaptation_rule(rule)
    
    def _get_high_confidence_patterns(self) -> List[LearningPattern]:
        """높은 신뢰도 패턴 조회"""
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM learning_patterns 
                WHERE confidence > 0.7 AND frequency >= 3
                ORDER BY impact_score DESC, confidence DESC
            """)
            
            patterns = []
            for row in cursor.fetchall():
                patterns.append(LearningPattern(
                    pattern_id=row[0],
                    pattern_type=row[1],
                    description=row[2],
                    frequency=row[3],
                    confidence=row[4],
                    last_observed=row[5],
                    impact_score=row[6]
                ))
            
            return patterns
    
    def _create_rule_from_pattern(self, pattern: LearningPattern) -> Optional[AdaptationRule]:
        """패턴으로부터 적응 규칙 생성"""
        rule_templates = {
            'insufficient_detail': {
                'action_type': 'prompt_modify',
                'action_description': 'Add instruction for more detailed information'
            },
            'missing_information': {
                'action_type': 'template_update',
                'action_description': 'Include missing mandatory sections'
            },
            'structural_improvement': {
                'action_type': 'logic_adjust',
                'action_description': 'Improve report structure and flow'
            },
            'tone_adjustment': {
                'action_type': 'prompt_modify',
                'action_description': 'Adjust tone and formality level'
            }
        }
        
        correction_type = pattern.pattern_id.split('_')[0]
        template = rule_templates.get(correction_type)
        
        if not template:
            return None
        
        rule_id = f"rule_{pattern.pattern_id}_{int(datetime.now().timestamp())}"
        
        return AdaptationRule(
            rule_id=rule_id,
            trigger_pattern=pattern.pattern_id,
            action_type=template['action_type'],
            action_description=template['action_description'],
            effectiveness_score=pattern.impact_score,
            created_at=datetime.now().isoformat(),
            last_applied=""
        )
    
    def _save_adaptation_rule(self, rule: AdaptationRule):
        """적응 규칙 저장"""
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            
            # 중복 규칙 확인
            cursor.execute("""
                SELECT rule_id FROM adaptation_rules 
                WHERE trigger_pattern = ? AND action_type = ?
            """, (rule.trigger_pattern, rule.action_type))
            
            if cursor.fetchone():
                return  # 이미 존재하는 규칙
            
            cursor.execute("""
                INSERT INTO adaptation_rules
                (rule_id, trigger_pattern, action_type, action_description,
                 effectiveness_score, created_at, last_applied, application_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule.rule_id,
                rule.trigger_pattern,
                rule.action_type,
                rule.action_description,
                rule.effectiveness_score,
                rule.created_at,
                rule.last_applied,
                0
            ))
        
        self.logger.info(f"Adaptation rule created: {rule.rule_id}")
    
    def apply_adaptations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """적응 규칙 적용"""
        applicable_rules = self._get_applicable_rules(context)
        adaptations = {}
        
        for rule in applicable_rules:
            adaptation = self._apply_rule(rule, context)
            if adaptation:
                adaptations[rule.action_type] = adaptation
                self._record_rule_application(rule.rule_id)
        
        return adaptations
    
    def _get_applicable_rules(self, context: Dict[str, Any]) -> List[AdaptationRule]:
        """적용 가능한 규칙 조회"""
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM adaptation_rules 
                WHERE effectiveness_score > 0.6
                ORDER BY effectiveness_score DESC
                LIMIT 5
            """)
            
            rules = []
            for row in cursor.fetchall():
                rule = AdaptationRule(
                    rule_id=row[0],
                    trigger_pattern=row[1],
                    action_type=row[2],
                    action_description=row[3],
                    effectiveness_score=row[4],
                    created_at=row[5],
                    last_applied=row[6] or ""
                )
                
                # 컨텍스트와 매칭 여부 확인
                if self._rule_matches_context(rule, context):
                    rules.append(rule)
            
            return rules
    
    def _rule_matches_context(self, rule: AdaptationRule, context: Dict[str, Any]) -> bool:
        """규칙이 컨텍스트와 매칭되는지 확인"""
        # 간단한 매칭 로직 (실제로는 더 정교하게 구현)
        issue_category = context.get('issue_category', 'general')
        
        if issue_category in rule.trigger_pattern:
            return True
        
        # 일반적인 패턴은 항상 적용
        if 'general' in rule.trigger_pattern:
            return True
        
        return False
    
    def _apply_rule(self, rule: AdaptationRule, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """규칙 적용"""
        adaptations = {
            'prompt_modify': self._modify_prompt,
            'template_update': self._update_template,
            'logic_adjust': self._adjust_logic
        }
        
        apply_func = adaptations.get(rule.action_type)
        if apply_func:
            return apply_func(rule, context)
        
        return None
    
    def _modify_prompt(self, rule: AdaptationRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """프롬프트 수정"""
        modifications = {}
        
        if 'insufficient_detail' in rule.trigger_pattern:
            modifications['additional_instruction'] = """
반드시 다음 사항을 포함하여 상세히 작성해주세요:
- 구체적인 대응 방안과 실행 계획
- 각 부서별 역할과 책임
- 예상 일정과 마일스톤
- 리스크 요소와 대응책
"""
        
        if 'missing_information' in rule.trigger_pattern:
            modifications['mandatory_sections'] = [
                "즉시 대응사항",
                "부서별 담당자 정보",
                "후속 조치 계획",
                "모니터링 방안"
            ]
        
        return modifications
    
    def _update_template(self, rule: AdaptationRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """템플릿 업데이트"""
        updates = {}
        
        if 'structural_improvement' in rule.trigger_pattern:
            updates['improved_structure'] = {
                'add_executive_summary': True,
                'enhance_action_items': True,
                'add_timeline': True
            }
        
        return updates
    
    def _adjust_logic(self, rule: AdaptationRule, context: Dict[str, Any]) -> Dict[str, Any]:
        """로직 조정"""
        adjustments = {}
        
        if 'tone_adjustment' in rule.trigger_pattern:
            adjustments['tone_settings'] = {
                'formality_level': 'high',
                'urgency_emphasis': True,
                'professional_language': True
            }
        
        return adjustments
    
    def _record_rule_application(self, rule_id: str):
        """규칙 적용 기록"""
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE adaptation_rules 
                SET last_applied = ?, application_count = application_count + 1
                WHERE rule_id = ?
            """, (datetime.now().isoformat(), rule_id))
        
        self.logger.info(f"Rule applied: {rule_id}")
    
    def evaluate_adaptation_effectiveness(self, rule_id: str, 
                                        before_metrics: Dict[str, float],
                                        after_metrics: Dict[str, float]):
        """적응 효과 평가"""
        effectiveness = self._calculate_effectiveness(before_metrics, after_metrics)
        
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO adaptation_effects
                (rule_id, applied_at, before_metrics, after_metrics, effectiveness)
                VALUES (?, ?, ?, ?, ?)
            """, (
                rule_id,
                datetime.now().isoformat(),
                json.dumps(before_metrics),
                json.dumps(after_metrics),
                effectiveness
            ))
            
            # 규칙의 효과성 점수 업데이트
            cursor.execute("""
                UPDATE adaptation_rules
                SET effectiveness_score = (effectiveness_score + ?) / 2
                WHERE rule_id = ?
            """, (effectiveness, rule_id))
        
        self.logger.info(f"Adaptation effectiveness evaluated: {rule_id} = {effectiveness:.2f}")
    
    def _calculate_effectiveness(self, before: Dict[str, float], after: Dict[str, float]) -> float:
        """효과성 계산"""
        improvements = []
        
        for metric in ['user_rating', 'processing_time', 'accuracy_score']:
            if metric in before and metric in after:
                if metric == 'processing_time':
                    # 처리시간은 낮을수록 좋음
                    improvement = (before[metric] - after[metric]) / before[metric]
                else:
                    # 나머지는 높을수록 좋음
                    improvement = (after[metric] - before[metric]) / before[metric]
                
                improvements.append(max(-1.0, min(1.0, improvement)))  # -1 ~ 1 범위로 제한
        
        return sum(improvements) / len(improvements) if improvements else 0.0
    
    def generate_learning_report(self) -> Dict[str, Any]:
        """학습 보고서 생성"""
        with sqlite3.connect(self.data_path) as conn:
            cursor = conn.cursor()
            
            # 기본 통계
            cursor.execute("SELECT COUNT(*) FROM user_corrections")
            total_corrections = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM learning_patterns")
            total_patterns = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM adaptation_rules")
            total_rules = cursor.fetchone()[0]
            
            # 효과적인 적응 규칙
            cursor.execute("""
                SELECT rule_id, action_description, effectiveness_score, application_count
                FROM adaptation_rules 
                WHERE effectiveness_score > 0.7
                ORDER BY effectiveness_score DESC
                LIMIT 5
            """)
            effective_rules = cursor.fetchall()
            
            # 최근 패턴 트렌드
            cursor.execute("""
                SELECT pattern_type, AVG(confidence), COUNT(*)
                FROM learning_patterns 
                GROUP BY pattern_type
                ORDER BY AVG(confidence) DESC
            """)
            pattern_trends = cursor.fetchall()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_corrections': total_corrections,
            'total_patterns': total_patterns,
            'total_rules': total_rules,
            'effective_rules': [
                {
                    'rule_id': row[0],
                    'description': row[1],
                    'effectiveness': row[2],
                    'applications': row[3]
                }
                for row in effective_rules
            ],
            'pattern_trends': [
                {
                    'type': row[0],
                    'avg_confidence': row[1],
                    'count': row[2]
                }
                for row in pattern_trends
            ]
        }

def example_usage():
    """사용 예제"""
    learner = AdaptiveLearner()
    
    # 사용자 수정사항 기록
    original = "포스코인터내셔널에서 이슈가 발생했습니다."
    corrected = """포스코인터내셔널 제품 품질 이슈 발생

1. 즉시 대응사항:
   - 품질관리팀 긴급 점검
   - 고객사 통보 및 사과
   - 담당자: 김철수 (02-1234-5678)

2. 후속 조치:
   - 원인 분석 및 개선방안 수립
   - 재발 방지 시스템 구축"""
    
    context = {
        'issue_category': '제품',
        'crisis_level': '높음'
    }
    
    learner.record_user_correction(original, corrected, context, "더 구체적이고 실무적인 대응방안 필요")
    
    # 적응 규칙 생성 및 적용
    learner.generate_adaptation_rules()
    adaptations = learner.apply_adaptations(context)
    
    print("적용된 적응사항:", adaptations)
    
    # 학습 보고서 생성
    report = learner.generate_learning_report()
    print("학습 현황:", report)

if __name__ == "__main__":
    example_usage()