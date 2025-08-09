#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
템플릿 이슈 테스트 및 분석
"""

import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_current_template_usage():
    """현재 템플릿 사용 방식 테스트"""
    print("=== 현재 템플릿 사용 방식 분석 ===")
    
    try:
        from data_based_llm import DataBasedLLM
        
        llm = DataBasedLLM()
        
        # 템플릿 로드 테스트
        template_content = llm._load_report_template()
        print(f"템플릿 로드 성공: {len(template_content)}자")
        
        # 변수 치환 테스트
        media_name = "조선일보"
        reporter_name = "김기자"
        issue_description = "포스코 배터리 이슈"
        
        template_with_vars = template_content.replace("{{MEDIA_OUTLET}}", media_name)
        template_with_vars = template_with_vars.replace("{{REPORTER_NAME}}", reporter_name)
        template_with_vars = template_with_vars.replace("{{ISSUE}}", issue_description)
        
        print(f"변수 치환 완료")
        
        # 문제점 분석
        print("\n=== 문제점 분석 ===")
        print("1. 템플릿 구조:")
        lines = template_content.split('\n')
        template_sections = []
        for line in lines:
            if line.strip().startswith('🧾') or line.strip().startswith('1.') or line.strip().startswith('2.') or line.strip().startswith('3.') or line.strip().startswith('4.') or line.strip().startswith('5.') or line.strip().startswith('6.'):
                template_sections.append(line.strip())
        
        for section in template_sections:
            print(f"   - {section}")
        
        print(f"\n2. 변수 치환만 되는 항목:")
        print(f"   - MEDIA_OUTLET: {media_name}")
        print(f"   - REPORTER_NAME: {reporter_name}") 
        print(f"   - ISSUE: {issue_description}")
        
        print(f"\n3. 분석 결과가 매핑되지 않는 항목:")
        print("   - 발생 단계 (위기 분류)")
        print("   - 유관 의견 (부서별 의견)")
        print("   - 대응 방안 (PR 전략)")
        print("   - 참조 유사 사례")
        print("   - 이슈 정의 및 개념")
        
        return True
        
    except Exception as e:
        print(f"오류: {str(e)}")
        return False

def analyze_template_structure():
    """템플릿 구조 상세 분석"""
    print("\n=== 템플릿 구조 상세 분석 ===")
    
    try:
        with open('data/risk_report.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 섹션별 분석
        sections = {
            '템플릿 구조': [],
            '변수 위치': [],
            '지시사항': []
        }
        
        lines = content.split('\n')
        current_section = None
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            # 템플릿 구조 섹션
            if '템플릿' in line and ('이슈 발생 보고' in line or '출력 형식' in line):
                current_section = 'template'
            elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.')):
                sections['템플릿 구조'].append(f"라인 {line_num}: {line}")
            
            # 변수 위치
            elif '{{' in line and '}}' in line:
                sections['변수 위치'].append(f"라인 {line_num}: {line}")
            
            # 주요 지시사항
            elif any(keyword in line for keyword in ['지침', '작성', '출력', '보고서']):
                if len(line) < 100:  # 너무 긴 줄은 제외
                    sections['지시사항'].append(f"라인 {line_num}: {line}")
        
        for section_name, items in sections.items():
            print(f"\n{section_name}:")
            for item in items[:5]:  # 상위 5개만 표시
                print(f"  {item}")
        
        return True
        
    except Exception as e:
        print(f"템플릿 분석 오류: {str(e)}")
        return False

def main():
    """메인 테스트"""
    print("템플릿 이슈 진단 및 분석 시작")
    print("=" * 50)
    
    # 1. 현재 템플릿 사용 방식 테스트
    template_success = test_current_template_usage()
    
    # 2. 템플릿 구조 분석
    structure_success = analyze_template_structure()
    
    print("\n" + "=" * 50)
    print("결론:")
    
    if template_success and structure_success:
        print("✓ 템플릿은 정상적으로 로드됨")
        print("✗ 하지만 구조적 매핑이 부족함")
        print("\n핵심 문제:")
        print("1. 변수 치환만 되고 실제 분석 결과가 구조화되지 않음")
        print("2. LLM이 템플릿 구조를 따르지 않고 자유형식으로 생성")
        print("3. 8단계 분석 결과와 6단계 템플릿 간 매핑 로직 부재")
        
        print("\n개선 방향:")
        print("1. 구조화된 프롬프트 설계")
        print("2. 분석 결과를 템플릿 섹션별로 강제 매핑")
        print("3. LLM 출력 형식 엄격화")
    else:
        print("기본적인 템플릿 처리에 문제가 있습니다.")
    
    print("\n분석 완료.")

if __name__ == "__main__":
    main()