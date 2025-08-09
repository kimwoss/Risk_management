#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
개선된 테이블 디자인 테스트용 간단한 스크립트
"""

import streamlit as st
import pandas as pd

def test_table_design():
    """테이블 디자인 테스트"""
    st.title("담당자 정보 테이블 디자인 테스트")
    
    # 테스트용 데이터
    test_data = pd.DataFrame({
        "성명": ["김철수", "이영희", "박민수"],
        "직책": ["과장", "대리", "주임"],
        "사무실 번호": ["02-1234-5678", "02-1234-5679", "02-1234-5680"]
    })
    
    # 개선된 스타일이 적용된 테이블
    st.markdown("### 개선된 디자인 (contact-table 클래스)")
    st.markdown('<div class="contact-table">', unsafe_allow_html=True)
    st.dataframe(test_data, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 기본 테이블 (비교용)
    st.markdown("### 기본 디자인 (비교용)")
    st.dataframe(test_data, use_container_width=True)

if __name__ == "__main__":
    test_table_design()