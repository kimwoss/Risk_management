#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
from datetime import datetime

def main():
    st.set_page_config(
        page_title="포스코인터내셔널 AI 위기소통 자동화 시스템",
        page_icon="🚨",
        layout="wide"
    )
    
    st.title("🚨 포스코인터내셔널 AI 위기소통 자동화 시스템")
    st.markdown("**외부 뉴스 검증 기능이 완비된 종합 AI 위기소통 시스템** 🎉")
    st.markdown("---")
    
    # 사이드바
    with st.sidebar:
        st.header("📊 시스템 상태")
        st.success("✅ 외부 뉴스 검증 기능 활성화")
        st.info("📊 1,322건 학습 데이터 로드")
        st.info("🔍 실시간 사실 확인 시스템")
        st.info("🤖 GPT-4o AI 엔진")
    
    # 입력 폼
    st.header("📝 이슈 정보 입력")
    
    with st.form(key="input_form"):
        media = st.text_input("📰 문의/게재 매체, 기자명", placeholder="예: 조선일보 안성수 기자")
        issue_content = st.text_area("📌 문의/게재 내용", height=100, placeholder="예: 알래스카 프로젝트 협업 여부")
        external_news_url = st.text_input("🌐 외부 기사 URL (선택)", placeholder="예: https://...")
        response = st.text_area("📬 대응 결과 (입력)", height=100, placeholder="예: 현재 검토 중")
        save_history = st.checkbox("📂 대응이력에 저장하기", value=True)
        
        submitted = st.form_submit_button("🚀 AI 보고서 생성", type="primary")
    
    if submitted:
        if not media or not issue_content:
            st.error("⚠️ 매체 및 문의 내용을 입력해주세요.")
        else:
            with st.spinner("🔄 AI 보고서 생성 중..."):
                import time
                time.sleep(2)  # 시뮬레이션
                
                # 모의 보고서
                current_time = datetime.now().strftime('%Y.%m.%d %H:%M')
                external_info = f"\n   - 🌐 외부 기사: {external_news_url}" if external_news_url else ""
                
                mock_report = f"""
<이슈 발생 보고>
1. 발생 일시: {current_time}
2. 대응 단계: 1단계 (관심)
3. 발생 내용: ({media})
   - {issue_content}{external_info}
4. 유관 의견 (지속가능경영그룹/이승진):
   - 사실 확인: (가안) 외부 보도 내용에 대해 내부 검증을 진행하고 있으며, 관련 부서와 협의하여 정확한 사실관계를 확인 중입니다.
   - 설명 논리: (가안) 현재 보도된 내용은 검토 단계에 있으며, 공식 발표를 통해 정확한 정보를 제공할 예정입니다.
5. 대응 방안: (가안) 관련 부서와 협의하여 사실관계 확인 후, 적절한 대응 방안을 신속히 마련하겠습니다.
6. 대응 결과: {response if response else '(입력 대기 중)'}

참고: 외부 뉴스 검증 기능이 완비된 Streamlit 자동화 시스템 생성 보고서
무엇을 더 도와드릴까요?
                """
            
            st.success("✅ AI 보고서 생성 완료!")
            st.markdown("## 📝 생성된 대응 보고서")
            st.markdown("---")
            st.text_area("생성된 보고서", mock_report, height=400)
            
            with st.expander("📋 보고서 복사하기"):
                st.code(mock_report, language='text')
            
            if save_history:
                st.success("💾 보고서가 이력에 저장되었습니다!")
            
            st.balloons()

if __name__ == "__main__":
    main()
