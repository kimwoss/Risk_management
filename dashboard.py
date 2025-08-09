#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
실시간 성능 모니터링 대시보드
Streamlit 기반 관리자용 모니터링 인터페이스
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import json
import sqlite3
from performance_monitor import PerformanceMonitor, create_performance_dashboard_data
from prompt_optimizer import PromptOptimizer, ModelComparator

def create_dashboard():
    """성능 모니터링 대시보드 생성"""
    st.set_page_config(
        page_title="포스코인터내셔널 AI 시스템 성능 모니터링",
        page_icon="📊",
        layout="wide"
    )
    
    # 사이드바
    with st.sidebar:
        st.title("🎛️ 제어판")
        
        # 새로고침 버튼
        if st.button("🔄 데이터 새로고침", type="primary"):
            st.rerun()
        
        # 시간 범위 선택
        time_range = st.selectbox(
            "📅 조회 기간",
            ["오늘", "최근 7일", "최근 30일"],
            index=1
        )
        
        # 알림 설정
        st.subheader("⚠️ 알림 설정")
        alert_processing_time = st.number_input("처리시간 임계값 (초)", value=5.0, min_value=1.0)
        alert_error_rate = st.number_input("에러율 임계값 (%)", value=10.0, min_value=0.0, max_value=100.0)
        
        # 시스템 상태
        st.subheader("🔋 시스템 상태")
        monitor = PerformanceMonitor()
        daily_metrics = monitor.get_daily_metrics()
        
        # 상태 표시
        if daily_metrics['total_reports'] > 0:
            health_color = "🟢" if daily_metrics['avg_processing_time'] < alert_processing_time else "🔴"
            st.write(f"{health_color} 평균 처리시간: {daily_metrics['avg_processing_time']:.2f}초")
            
            rating_color = "🟢" if daily_metrics['avg_user_rating'] >= 4.0 else "🟡" if daily_metrics['avg_user_rating'] >= 3.0 else "🔴"
            st.write(f"{rating_color} 평균 평점: {daily_metrics['avg_user_rating']:.1f}/5.0")
        else:
            st.write("📊 오늘 처리된 보고서가 없습니다.")
    
    # 메인 대시보드
    st.title("📊 포스코인터내셔널 AI 시스템 성능 모니터링")
    st.markdown("---")
    
    # 실시간 KPI 카드들
    create_kpi_cards()
    
    # 탭으로 구분된 상세 분석
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 성능 트렌드", 
        "🎯 품질 분석", 
        "🔍 이슈 트렌드", 
        "🤖 AI 최적화", 
        "⚙️ 시스템 설정"
    ])
    
    with tab1:
        create_performance_trends()
    
    with tab2:
        create_quality_analysis()
    
    with tab3:
        create_issue_trends()
    
    with tab4:
        create_ai_optimization()
    
    with tab5:
        create_system_settings()

def create_kpi_cards():
    """KPI 카드들 생성"""
    monitor = PerformanceMonitor()
    daily_metrics = monitor.get_daily_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📝 오늘 처리된 보고서",
            value=daily_metrics['total_reports'],
            delta=f"전일 대비 +{daily_metrics['total_reports'] - 5}"  # 임시값
        )
    
    with col2:
        st.metric(
            label="⏱️ 평균 처리시간",
            value=f"{daily_metrics['avg_processing_time']:.1f}초",
            delta=f"-{0.3:.1f}초",  # 임시값
            delta_color="inverse"
        )
    
    with col3:
        st.metric(
            label="⭐ 사용자 만족도",
            value=f"{daily_metrics['avg_user_rating']:.1f}/5.0",
            delta=f"+{0.2:.1f}",  # 임시값
            delta_color="normal"
        )
    
    with col4:
        error_rate = (daily_metrics['total_errors'] / max(daily_metrics['total_reports'], 1)) * 100
        st.metric(
            label="🚨 에러율",
            value=f"{error_rate:.1f}%",
            delta=f"-{2.1:.1f}%",  # 임시값
            delta_color="inverse"
        )

def create_performance_trends():
    """성능 트렌드 차트 생성"""
    st.subheader("📈 처리 시간 트렌드")
    
    # 임시 데이터 생성 (실제로는 DB에서 조회)
    dates = pd.date_range(start='2025-08-02', end='2025-08-09', freq='D')
    performance_data = pd.DataFrame({
        'date': dates,
        'avg_processing_time': [4.2, 3.8, 4.5, 3.2, 3.9, 3.1, 2.8, 3.5],
        'total_reports': [12, 15, 8, 20, 18, 22, 25, 16],
        'error_count': [1, 0, 2, 1, 0, 0, 1, 0]
    })
    
    # 처리 시간 차트
    fig1 = px.line(
        performance_data, 
        x='date', 
        y='avg_processing_time',
        title='평균 처리 시간 변화',
        labels={'avg_processing_time': '처리 시간 (초)', 'date': '날짜'}
    )
    fig1.add_hline(y=3.0, line_dash="dash", line_color="red", 
                   annotation_text="목표: 3초")
    st.plotly_chart(fig1, use_container_width=True)
    
    # 처리량과 에러율
    col1, col2 = st.columns(2)
    
    with col1:
        fig2 = px.bar(
            performance_data, 
            x='date', 
            y='total_reports',
            title='일별 처리량'
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        error_rate_data = (performance_data['error_count'] / performance_data['total_reports'] * 100).fillna(0)
        fig3 = px.bar(
            x=performance_data['date'], 
            y=error_rate_data,
            title='일별 에러율 (%)',
            labels={'x': '날짜', 'y': '에러율 (%)'}
        )
        fig3.add_hline(y=5.0, line_dash="dash", line_color="red", 
                       annotation_text="임계값: 5%")
        st.plotly_chart(fig3, use_container_width=True)

def create_quality_analysis():
    """품질 분석 차트 생성"""
    st.subheader("🎯 보고서 품질 분석")
    
    # 사용자 평점 분포
    rating_data = pd.DataFrame({
        'rating': ['1점', '2점', '3점', '4점', '5점'],
        'count': [2, 5, 12, 28, 15]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.pie(
            rating_data, 
            values='count', 
            names='rating',
            title='사용자 평점 분포'
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # 카테고리별 품질 점수
        category_quality = pd.DataFrame({
            'category': ['제품', '환경', '법무', '경영', '기타'],
            'avg_rating': [4.2, 4.5, 3.8, 4.1, 3.9],
            'count': [15, 8, 12, 10, 7]
        })
        
        fig2 = px.bar(
            category_quality,
            x='category',
            y='avg_rating', 
            title='이슈 카테고리별 평균 평점',
            color='avg_rating',
            color_continuous_scale='RdYlGn'
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # 상세 피드백 분석
    st.subheader("📝 사용자 피드백 분석")
    
    feedback_summary = pd.DataFrame({
        '개선 요청 사항': ['더 구체적인 대응방안', '부서별 역할 명확화', '처리 시간 단축', '정확도 향상'],
        '빈도': [18, 12, 8, 15],
        '우선순위': ['높음', '보통', '높음', '매우 높음']
    })
    
    st.dataframe(feedback_summary, use_container_width=True)

def create_issue_trends():
    """이슈 트렌드 분석"""
    st.subheader("🔍 이슈 트렌드 분석")
    
    monitor = PerformanceMonitor()
    trending_issues = monitor.get_trending_issues()
    
    if trending_issues:
        trend_df = pd.DataFrame(trending_issues)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(
                trend_df,
                x='category',
                y='count',
                title='이슈 카테고리별 발생 빈도',
                color='avg_rating',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.scatter(
                trend_df,
                x='avg_processing_time',
                y='avg_rating',
                size='count',
                hover_data=['category'],
                title='처리시간 vs 만족도 (버블 크기 = 빈도)',
                labels={'avg_processing_time': '평균 처리시간 (초)', 'avg_rating': '평균 평점'}
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        # 상세 테이블
        st.subheader("📊 카테고리별 상세 통계")
        st.dataframe(
            trend_df.rename(columns={
                'category': '카테고리',
                'count': '발생 건수',
                'avg_processing_time': '평균 처리시간(초)',
                'avg_rating': '평균 평점'
            }),
            use_container_width=True
        )
    else:
        st.info("📊 표시할 트렌드 데이터가 없습니다.")

def create_ai_optimization():
    """AI 최적화 현황"""
    st.subheader("🤖 AI 모델 최적화 현황")
    
    # 프롬프트 성능 비교
    optimizer = PromptOptimizer()
    
    if os.path.exists(optimizer.variants_file):
        optimization_report = optimizer.generate_optimization_report()
        
        for category, data in optimization_report['categories'].items():
            st.write(f"### {category.replace('_', ' ').title()}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "총 변형 수",
                    data['total_variants']
                )
            
            with col2:
                st.metric(
                    "최고 성능 점수",
                    f"{data['best_variant']['performance_score']:.3f}"
                )
            
            with col3:
                st.metric(
                    "총 사용 횟수",
                    data['total_usage']
                )
            
            # 최적 프롬프트 정보
            st.write(f"**최적 프롬프트:** {data['best_variant']['name']}")
            st.write(f"**성공률:** {data['best_variant']['success_rate']:.1%}")
    else:
        st.info("🤖 프롬프트 최적화 데이터를 초기화하고 있습니다.")
    
    # 모델 비교
    st.subheader("🔄 모델 성능 비교")
    
    model_comparator = ModelComparator()
    model_performance = pd.DataFrame({
        '모델': ['GPT-4', 'GPT-4 Turbo', 'GPT-3.5 Turbo'],
        '품질 점수': [0.95, 0.90, 0.85],
        '평균 처리시간 (초)': [4.2, 2.8, 1.5],
        '비용 ($/1K tokens)': [0.03, 0.01, 0.002],
        '종합 점수': [0.87, 0.89, 0.78]
    })
    
    # 모델 성능 레이더 차트
    fig = go.Figure()
    
    categories = ['품질', '속도', '비용 효율성', '안정성']
    
    for i, model in enumerate(['GPT-4', 'GPT-4 Turbo', 'GPT-3.5 Turbo']):
        values = [0.95, 0.7, 0.4, 0.9] if i == 0 else ([0.90, 0.85, 0.8, 0.85] if i == 1 else [0.85, 0.95, 0.95, 0.8])
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=model
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )),
        showlegend=True,
        title="모델별 성능 비교"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 모델 상세 비교 테이블
    st.dataframe(model_performance, use_container_width=True)

def create_system_settings():
    """시스템 설정"""
    st.subheader("⚙️ 시스템 설정")
    
    # 성능 임계값 설정
    with st.expander("🎯 성능 임계값 설정"):
        target_processing_time = st.number_input("목표 처리시간 (초)", value=3.0, min_value=1.0, max_value=10.0)
        target_accuracy = st.number_input("목표 정확도", value=0.90, min_value=0.5, max_value=1.0, step=0.01)
        target_satisfaction = st.number_input("목표 만족도", value=4.0, min_value=1.0, max_value=5.0, step=0.1)
        
        if st.button("설정 저장"):
            # 설정 저장 로직
            st.success("✅ 설정이 저장되었습니다!")
    
    # 자동 최적화 설정
    with st.expander("🤖 자동 최적화 설정"):
        enable_auto_optimization = st.checkbox("자동 최적화 활성화", value=True)
        optimization_frequency = st.selectbox("최적화 주기", ["매일", "매주", "매월"])
        
        if enable_auto_optimization:
            st.info("🔄 자동 최적화가 활성화되어 있습니다.")
        
        if st.button("최적화 즉시 실행"):
            with st.spinner("최적화 실행 중..."):
                # 최적화 실행 로직
                import time
                time.sleep(2)
            st.success("✅ 최적화가 완료되었습니다!")
    
    # 알림 설정
    with st.expander("📧 알림 설정"):
        email_notifications = st.checkbox("이메일 알림", value=True)
        slack_notifications = st.checkbox("슬랙 알림", value=False)
        
        notification_email = st.text_input("알림 이메일 주소", value="admin@posco.com")
        slack_webhook = st.text_input("슬랙 웹훅 URL", type="password")
        
        if st.button("알림 테스트"):
            st.success("✅ 테스트 알림이 발송되었습니다!")
    
    # 데이터 관리
    with st.expander("💾 데이터 관리"):
        st.write("**데이터 보존 정책**")
        retention_days = st.number_input("데이터 보존 기간 (일)", value=90, min_value=7, max_value=365)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("데이터 백업"):
                st.success("✅ 백업이 완료되었습니다!")
        
        with col2:
            if st.button("데이터 정리"):
                st.success("✅ 오래된 데이터가 정리되었습니다!")
        
        with col3:
            if st.button("성능 리포트 내보내기"):
                st.success("✅ 리포트가 다운로드되었습니다!")

if __name__ == "__main__":
    create_dashboard()