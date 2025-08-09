#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
포스코인터내셔널 AI 시스템 성능 모니터링 및 지속적 개선 시스템
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import sqlite3
from dataclasses import dataclass, asdict

@dataclass
class PerformanceMetrics:
    """성능 지표 데이터 클래스"""
    timestamp: str
    processing_time: float
    report_length: int
    user_rating: Optional[int] = None
    accuracy_score: Optional[float] = None
    error_count: int = 0
    issue_category: str = ""
    departments_count: int = 0

@dataclass  
class UserFeedback:
    """사용자 피드백 데이터 클래스"""
    timestamp: str
    report_id: str
    rating: int  # 1-5 점
    feedback_text: str = ""
    corrections: List[str] = None
    usage_type: str = ""  # "download", "modify", "reuse"

class PerformanceMonitor:
    """AI 시스템 성능 모니터링 클래스"""
    
    def __init__(self, db_path: str = "data/performance.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """성능 데이터베이스 초기화"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 성능 지표 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    processing_time REAL NOT NULL,
                    report_length INTEGER NOT NULL,
                    user_rating INTEGER,
                    accuracy_score REAL,
                    error_count INTEGER DEFAULT 0,
                    issue_category TEXT,
                    departments_count INTEGER DEFAULT 0
                )
            """)
            
            # 사용자 피드백 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    report_id TEXT NOT NULL,
                    rating INTEGER NOT NULL,
                    feedback_text TEXT,
                    corrections TEXT,
                    usage_type TEXT
                )
            """)
            
            # 시스템 개선 로그 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS improvement_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    improvement_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    impact_score REAL,
                    status TEXT DEFAULT 'applied'
                )
            """)
    
    def log_performance(self, metrics: PerformanceMetrics):
        """성능 지표 로깅"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics 
                (timestamp, processing_time, report_length, user_rating, 
                 accuracy_score, error_count, issue_category, departments_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metrics.timestamp,
                metrics.processing_time,
                metrics.report_length,
                metrics.user_rating,
                metrics.accuracy_score,
                metrics.error_count,
                metrics.issue_category,
                metrics.departments_count
            ))
    
    def log_feedback(self, feedback: UserFeedback):
        """사용자 피드백 로깅"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_feedback
                (timestamp, report_id, rating, feedback_text, corrections, usage_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                feedback.timestamp,
                feedback.report_id,
                feedback.rating,
                feedback.feedback_text,
                json.dumps(feedback.corrections) if feedback.corrections else None,
                feedback.usage_type
            ))
    
    def get_daily_metrics(self, date: str = None) -> Dict[str, Any]:
        """일일 성능 지표 조회"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 기본 통계
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_reports,
                    AVG(processing_time) as avg_processing_time,
                    AVG(user_rating) as avg_user_rating,
                    AVG(accuracy_score) as avg_accuracy,
                    SUM(error_count) as total_errors
                FROM performance_metrics 
                WHERE date(timestamp) = ?
            """, (date,))
            
            result = cursor.fetchone()
            
            return {
                'date': date,
                'total_reports': result[0] or 0,
                'avg_processing_time': round(result[1] or 0, 2),
                'avg_user_rating': round(result[2] or 0, 2),
                'avg_accuracy': round(result[3] or 0, 2),
                'total_errors': result[4] or 0
            }
    
    def get_trending_issues(self, days: int = 7) -> List[Dict[str, Any]]:
        """최근 이슈 트렌드 분석"""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    issue_category,
                    COUNT(*) as count,
                    AVG(processing_time) as avg_time,
                    AVG(user_rating) as avg_rating
                FROM performance_metrics 
                WHERE date(timestamp) >= ? AND issue_category != ''
                GROUP BY issue_category
                ORDER BY count DESC
                LIMIT 10
            """, (start_date,))
            
            return [
                {
                    'category': row[0],
                    'count': row[1],
                    'avg_processing_time': round(row[2], 2),
                    'avg_rating': round(row[3] or 0, 2)
                }
                for row in cursor.fetchall()
            ]
    
    def identify_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """개선 기회 식별"""
        opportunities = []
        
        # 처리 시간이 긴 케이스 분석
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AVG(processing_time) as avg_time
                FROM performance_metrics 
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            avg_time = cursor.fetchone()[0] or 0
            
            if avg_time > 5.0:  # 5초 이상
                opportunities.append({
                    'type': 'performance',
                    'issue': 'slow_processing',
                    'description': f'평균 처리시간이 {avg_time:.2f}초로 목표(3초)를 초과',
                    'priority': 'high'
                })
        
        # 낮은 평점 케이스 분석
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT AVG(user_rating) as avg_rating, COUNT(*) as count
                FROM performance_metrics 
                WHERE user_rating IS NOT NULL AND timestamp >= datetime('now', '-7 days')
            """)
            result = cursor.fetchone()
            avg_rating = result[0] or 0
            rating_count = result[1] or 0
            
            if rating_count > 0 and avg_rating < 4.0:
                opportunities.append({
                    'type': 'quality',
                    'issue': 'low_satisfaction',
                    'description': f'사용자 평점이 {avg_rating:.2f}점으로 목표(4.0)에 미달',
                    'priority': 'medium'
                })
        
        # 에러 발생 빈도 분석
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT SUM(error_count) as total_errors, COUNT(*) as total_reports
                FROM performance_metrics 
                WHERE timestamp >= datetime('now', '-7 days')
            """)
            result = cursor.fetchone()
            total_errors = result[0] or 0
            total_reports = result[1] or 0
            
            if total_reports > 0 and (total_errors / total_reports) > 0.1:  # 10% 이상 에러율
                opportunities.append({
                    'type': 'reliability',
                    'issue': 'high_error_rate',
                    'description': f'에러 발생률이 {(total_errors/total_reports)*100:.1f}%로 높음',
                    'priority': 'high'
                })
        
        return opportunities
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """종합 성능 보고서 생성"""
        return {
            'timestamp': datetime.now().isoformat(),
            'daily_metrics': self.get_daily_metrics(),
            'weekly_trend': self.get_trending_issues(),
            'improvement_opportunities': self.identify_improvement_opportunities(),
            'system_health': self._assess_system_health()
        }
    
    def _assess_system_health(self) -> Dict[str, str]:
        """시스템 건강도 평가"""
        metrics = self.get_daily_metrics()
        health = {}
        
        # 처리 시간 건강도
        if metrics['avg_processing_time'] < 3.0:
            health['processing_speed'] = 'excellent'
        elif metrics['avg_processing_time'] < 5.0:
            health['processing_speed'] = 'good'
        elif metrics['avg_processing_time'] < 8.0:
            health['processing_speed'] = 'fair'
        else:
            health['processing_speed'] = 'poor'
        
        # 사용자 만족도 건강도
        if metrics['avg_user_rating'] >= 4.5:
            health['user_satisfaction'] = 'excellent'
        elif metrics['avg_user_rating'] >= 4.0:
            health['user_satisfaction'] = 'good'
        elif metrics['avg_user_rating'] >= 3.5:
            health['user_satisfaction'] = 'fair'
        else:
            health['user_satisfaction'] = 'poor'
        
        # 전체 건강도
        health_scores = {'excellent': 4, 'good': 3, 'fair': 2, 'poor': 1}
        avg_health = sum(health_scores[v] for v in health.values()) / len(health)
        
        if avg_health >= 3.5:
            health['overall'] = 'excellent'
        elif avg_health >= 2.5:
            health['overall'] = 'good'
        elif avg_health >= 1.5:
            health['overall'] = 'fair'
        else:
            health['overall'] = 'poor'
        
        return health

class AutoOptimizer:
    """자동 최적화 시스템"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.optimization_history = []
    
    def analyze_patterns(self) -> List[Dict[str, Any]]:
        """성능 패턴 분석"""
        patterns = []
        
        # 처리 시간 패턴 분석
        opportunities = self.monitor.identify_improvement_opportunities()
        
        for opportunity in opportunities:
            if opportunity['type'] == 'performance':
                patterns.append({
                    'pattern_type': 'slow_categories',
                    'description': '특정 이슈 카테고리에서 처리 시간 지연',
                    'recommendation': 'naver API 캐싱 또는 병렬 처리 적용'
                })
        
        return patterns
    
    def suggest_optimizations(self) -> List[Dict[str, Any]]:
        """최적화 제안"""
        suggestions = []
        
        # 캐싱 제안
        suggestions.append({
            'type': 'caching',
            'title': '부서 매핑 결과 캐싱',
            'description': '동일한 키워드 조합에 대한 부서 매핑 결과를 캐시하여 속도 향상',
            'expected_improvement': '20-30% 처리 시간 단축',
            'implementation_priority': 'high'
        })
        
        # 병렬 처리 제안
        suggestions.append({
            'type': 'parallel_processing',
            'title': '비동기 웹 검색',
            'description': 'naver API 검색과 부서 의견 생성을 병렬 수행',
            'expected_improvement': '30-40% 처리 시간 단축',
            'implementation_priority': 'medium'
        })
        
        # 프롬프트 최적화 제안
        suggestions.append({
            'type': 'prompt_optimization',
            'title': 'A/B 테스트 기반 프롬프트 개선',
            'description': '이슈 유형별 최적화된 프롬프트 적용',
            'expected_improvement': '15-25% 정확도 향상',
            'implementation_priority': 'medium'
        })
        
        return suggestions

def create_performance_dashboard_data():
    """성능 대시보드용 데이터 생성"""
    monitor = PerformanceMonitor()
    
    return {
        'current_metrics': monitor.get_daily_metrics(),
        'trending_issues': monitor.get_trending_issues(),
        'system_health': monitor._assess_system_health(),
        'improvement_opportunities': monitor.identify_improvement_opportunities(),
        'last_updated': datetime.now().isoformat()
    }

if __name__ == "__main__":
    # 테스트용 데이터 생성
    monitor = PerformanceMonitor()
    
    # 샘플 성능 데이터 추가
    sample_metrics = PerformanceMetrics(
        timestamp=datetime.now().isoformat(),
        processing_time=4.2,
        report_length=1500,
        user_rating=4,
        accuracy_score=0.85,
        error_count=0,
        issue_category="제품",
        departments_count=3
    )
    
    monitor.log_performance(sample_metrics)
    
    # 성능 보고서 생성
    report = monitor.generate_performance_report()
    print("성능 모니터링 시스템이 초기화되었습니다.")
    print(f"시스템 상태: {report['system_health']['overall']}")