#!/usr/bin/env python3
"""
검증 로직 통합 기능 테스트
"""

import sys
import json
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from generate_report import ReportGenerator

def test_verification_logic():
    """강화된 검증 로직 테스트"""
    
    print("=" * 60)
    print("🔍 검증 로직 통합 기능 테스트")
    print("=" * 60)
    
    # 검증이 필요한 복잡한 테스트 데이터
    test_input = {
        "발생_일시": "2025.08.05 15:00",
        "매체": "파이낸셜뉴스",
        "기자": "최민지 기자",
        "주요내용": """포스코인터내셔널이 호주 리튬 광산 개발을 위해 30억 달러를 투자하기로 결정했다는 로이터 통신 보도가 나왔습니다.
        
        🔍 외부 기사 정보 (검증 필요):
        - 매체: 로이터 통신 (2025.08.05)
        - 제목: "POSCO International commits $3B for Australian lithium mine development"
        - 주요 주장: 
          * 30억 달러 투자 확정 (이사회 승인 완료)
          * 2026년 상업 생산 시작 예정
          * 호주 정부와 최종 계약 체결
          * 연간 50만 톤 리튬 생산 목표
          
        ⚠️ 검증 포인트:
        1. 30억 달러 투자 규모의 정확성 (IR 자료 확인 필요)
        2. 이사회 승인 완료 여부 (공시 자료 확인 필요)
        3. 호주 정부 계약 체결 사실 여부
        4. 생산 일정 및 규모의 현실성
        
        기자 질의:
        1. 투자 결정의 정확한 시점과 승인 과정
        2. 기존 발표된 계획과의 차이점
        3. 다른 경쟁사 대비 투자 규모 적정성
        4. ESG 리스크 관리 방안"""
    }
    
    print(f"📝 테스트 입력 (검증 로직 집중 테스트):")
    print(f"  매체: {test_input['매체']}")
    print(f"  기자: {test_input['기자']}")
    print(f"  이슈 유형: 호주 리튬 광산 30억 달러 투자 (로이터 보도)")
    print(f"  검증 필요: 투자 규모, 승인 여부, 계약 체결, 생산 일정")
    
    try:
        generator = ReportGenerator()
        print(f"\n🔄 보고서 생성 중 (강화된 검증 로직 적용)...")
        
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
            
            # 강화된 검증 로직이 제대로 작동하는지 확인
            report_content = result['report_content']
            
            print(f"\n🔍 검증 로직 기능 확인:")
            
            # 1. 내부 일치성 확인 관련 문구
            if "내부 확인" in report_content or "공식 자료" in report_content:
                print(f"  ✅ 내부 일치성 확인 프로세스 포함")
            else:
                print(f"  ❌ 내부 일치성 확인 누락")
            
            # 2. 수치 검증 관련 문구
            if "30억" in report_content and ("검토" in report_content or "확인" in report_content):
                print(f"  ✅ 수치 정보 검증 프로세스 포함")
            else:
                print(f"  ❌ 수치 정보 검증 누락")
            
            # 3. 불확실 정보 표시
            if "검토 중" in report_content or "내부 확인 중" in report_content or "확정되지" in report_content:
                print(f"  ✅ 불확실 정보 적절히 표시됨")
            else:
                print(f"  ❌ 불확실 정보 표시 누락")
            
            # 4. IR 자료 언급
            if "IR" in report_content or "공시" in report_content or "이사회" in report_content:
                print(f"  ✅ 공식 자료 검증 언급됨")
            else:
                print(f"  ❌ 공식 자료 검증 누락")
            
            # 5. 로이터 출처 명시
            if "로이터" in report_content or "Reuters" in report_content:
                print(f"  ✅ 외부 기사 출처 정확히 명시")
            else:
                print(f"  ❌ 외부 기사 출처 누락")
            
            # 6. 단계별 검증 표현
            verification_phrases = ["일부 맞으나", "확인되지 않습니다", "판단됩니다", "아직 언급되지"]
            has_verification = any(phrase in report_content for phrase in verification_phrases)
            
            if has_verification:
                print(f"  ✅ 단계별 검증 표현 적용됨")
            else:
                print(f"  ❌ 단계별 검증 표현 누락")
            
        else:
            print(f"❌ 보고서 생성 실패: {result.get('error', '알 수 없는 오류')}")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_verification_logic()
