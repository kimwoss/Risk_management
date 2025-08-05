#!/usr/bin/env python3
"""
외부 뉴스 정보 검증 기능이 포함된 프롬프트 테스트
"""

import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from generate_report import ReportGenerator

def test_news_verification_prompt():
    """외부 뉴스 정보 검증 기능 테스트"""
    
    print("=" * 60)
    print("📰 외부 뉴스 정보 검증 기능 테스트")
    print("=" * 60)
    
    # 외부 뉴스 정보가 포함된 테스트 데이터
    test_input = {
        "발생_일시": "2025.08.05 14:00",
        "매체": "한국경제",
        "기자": "박상현 기자",
        "주요내용": """포스코인터내셔널이 인도네시아 팜오일 사업 확장을 위해 5억 달러 규모의 추가 투자를 검토 중이라는 보도가 나왔습니다. 
        
        관련 외부 기사 정보:
        - 매체: 블룸버그 통신 (2025.08.04)
        - 제목: "POSCO International considers $500M palm oil expansion in Indonesia"
        - 주요 내용: "포스코인터는 지속가능한 팜오일 생산을 위해 인도네시아 현지 파트너와 합작 투자를 논의 중이며, ESG 기준을 만족하는 새로운 농장 개발에 초점을 맞추고 있다고 보도"
        - 출처: https://www.bloomberg.com/news/articles/2025-08-04/posco-palm-oil-expansion
        
        기자 질의사항:
        1. 5억 달러 투자 규모의 정확성
        2. 인도네시아 정부와의 협의 진행 상황
        3. ESG 기준 준수 방안
        4. 기존 팜오일 사업과의 시너지 효과"""
    }
    
    print(f"📝 테스트 입력 (외부 뉴스 정보 포함):")
    print(f"  매체: {test_input['매체']}")
    print(f"  기자: {test_input['기자']}")
    print(f"  이슈 유형: 팜오일 사업 확장 (외부 보도 기반 질의)")
    print(f"  외부 정보: 블룸버그 통신 보도 내용 포함")
    
    try:
        generator = ReportGenerator()
        print(f"\n🔄 보고서 생성 중 (외부 정보 검증 포함)...")
        
        result = generator.generate_report(test_input)
        
        if result['success']:
            print(f"\n✅ 보고서 생성 성공!")
            print(f"📊 분석 결과:")
            print(f"  위기 단계: {result['analysis']['crisis_level']}")
            print(f"  추천 부서: {result['analysis']['suggested_department']['부서명']} / {result['analysis']['suggested_department']['담당자']}")
            print(f"  유사 사례: {result['analysis']['similar_cases_count']}건")
            
            print(f"\n📋 생성된 보고서:")
            print("=" * 60)
            print(result['report_content'])
            print("=" * 60)
            
            # 외부 뉴스 검증 기능이 제대로 작동하는지 확인
            report_content = result['report_content']
            
            print(f"\n🔍 외부 정보 검증 기능 확인:")
            
            # 외부 기사 언급 확인
            if "블룸버그" in report_content or "Bloomberg" in report_content:
                print(f"  ✅ 외부 기사 출처(블룸버그) 언급됨")
            else:
                print(f"  ❌ 외부 기사 출처 누락")
            
            # 사실 검증 문구 확인
            if "사실 확인" in report_content and "검증" in report_content:
                print(f"  ✅ 사실 검증 과정 포함됨")
            else:
                print(f"  ❌ 사실 검증 과정 누락")
            
            # 투자 규모 언급 확인
            if "5억" in report_content or "$500M" in report_content:
                print(f"  ✅ 구체적 투자 규모 반영됨")
            else:
                print(f"  ❌ 투자 규모 정보 누락")
            
            # ESG 관련 언급 확인
            if "ESG" in report_content:
                print(f"  ✅ ESG 기준 관련 내용 포함됨")
            else:
                print(f"  ❌ ESG 관련 내용 누락")
            
            # 가안 표기 확인
            if "(가안)" in report_content:
                print(f"  ✅ 가안 표기 정상 적용됨")
            else:
                print(f"  ❌ 가안 표기 누락")
            
        else:
            print(f"❌ 보고서 생성 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_news_verification_prompt()
