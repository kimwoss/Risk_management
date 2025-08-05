# -*- coding: utf-8 -*-
# app/components/report_display.py

import streamlit as st

def display_report(report_text: str):
    """GPT가 생성한 보고서를 보기 좋게 출력"""
    st.markdown("## 📝 생성된 대응 보고서", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"<pre style='font-size:15px; white-space: pre-wrap;'>{report_text}</pre>", unsafe_allow_html=True)
    st.markdown("---")

    with st.expander("📋 보고서 복사하기"):
        st.code(report_text, language='text')
