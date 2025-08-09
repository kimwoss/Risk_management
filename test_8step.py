#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
완전한 8단계 프로세스 직접 테스트
"""

import sys
import os
from datetime import datetime
import time

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_8step_process():
    """8단계 프로세스 직접 테스트"""
    
    print("=" * 60)
    print("포스코인터내셔널 완전한 8단계 프로세스 테스트")
    print("=" * 60)
    
    try:
        from data_based_llm import DataBasedLLM
        
        # 시작 시간 기록
        start_time = time.time()
        
        # DataBasedLLM 초기화
        print("1. DataBasedLLM 초기화 중...")
        llm = DataBasedLLM()
        print("   초기화 완료!")
        
        # 테스트 데이터
        media_name = "조선일보"
        reporter_name = "김철수"
        issue_description = "포스코인터내셔널 2차전지 소재에서 리튬 배터리 결함이 발견되어 전기차 5만대 리콜 검토"
        
        print(f"\n2. 테스트 입력 데이터:")
        print(f"   언론사: {media_name}")
        print(f"   기자명: {reporter_name}")
        print(f"   이슈: {issue_description}")
        
        print(f"\n3. 완전한 8단계 프로세스 실행 시작...")
        print("-" * 40)
        
        # 완전한 8단계 프로세스 실행
        report = llm.generate_comprehensive_issue_report(
            media_name, 
            reporter_name, 
            issue_description
        )
        
        # 종료 시간 기록
        end_time = time.time()
        processing_time = end_time - start_time
        
        print("-" * 40)
        print("4. 실행 완료!")
        print(f"   처리 시간: {processing_time:.2f}초")
        print(f"   보고서 길이: {len(report):,}자")
        
        # 결과 저장
        output_file = f"test_8step_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("포스코인터내셔널 완전한 8단계 프로세스 테스트 결과\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"처리 시간: {processing_time:.2f}초\n")
            f.write(f"보고서 길이: {len(report):,}자\n\n")
            f.write("테스트 입력:\n")
            f.write(f"- 언론사: {media_name}\n")
            f.write(f"- 기자명: {reporter_name}\n")
            f.write(f"- 이슈: {issue_description}\n\n")
            f.write("=" * 60 + "\n")
            f.write("생성된 보고서:\n")
            f.write("=" * 60 + "\n\n")
            f.write(report)
        
        print(f"\n5. 결과 파일 저장: {output_file}")
        
        # 보고서 미리보기 (처음 500자)
        print(f"\n6. 생성된 보고서 미리보기:")
        print("-" * 40)
        preview = report[:500] + "..." if len(report) > 500 else report
        print(preview)
        print("-" * 40)
        
        return {
            'success': True,
            'processing_time': processing_time,
            'report_length': len(report),
            'output_file': output_file
        }
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    print("8단계 프로세스 직접 테스트를 시작합니다...")
    result = test_8step_process()
    
    if result['success']:
        print(f"\n✅ 테스트 성공!")
        print(f"   처리 시간: {result['processing_time']:.2f}초")
        print(f"   보고서 길이: {result['report_length']:,}자")
        print(f"   결과 파일: {result['output_file']}")
        print("\n🎯 완전한 8단계 프로세스가 성공적으로 실행되었습니다!")
    else:
        print(f"\n❌ 테스트 실패: {result['error']}")
    
    print("\n테스트 완료.")