# -*- coding: utf-8 -*-
# app/components/input_form.py

import streamlit as st

def input_form():
    st.subheader("📝 이슈 정보 입력")

    with st.form(key="input_form"):
        media = st.text_input("📰 문의/게재 매체, 기자명", placeholder="예: 조선일보 안성수 기자")
        issue_content = st.text_area("📌 문의/게재 내용", height=100, placeholder="예: 알래스카 프로젝트 협업 여부 및 에너지 사업 내용 문의")
        external_news_url = st.text_input("🌐 외부 기사 URL (선택)", placeholder="예: https://...")
        response = st.text_area("📬 대응 결과 (입력)", height=100, placeholder="예: 현재 검토 중이며 공식 입장은...")
        save_history = st.checkbox("📂 대응이력에 저장하기", value=True)

        submitted = st.form_submit_button("입력 완료")

        if submitted:
            if not media or not issue_content:
                st.error("⚠️ 매체 및 문의 내용을 입력해주세요.")
                return None

            return {
                "media": media,
                "issue_content": issue_content,
                "external_news_url": external_news_url,
                "response": response,
                "save_history": save_history
            }
