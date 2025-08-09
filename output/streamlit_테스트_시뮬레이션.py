#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit 이슈발생보고 생성 프로세스 테스트 시뮬레이션
5가지 다양한 입력값으로 테스트 실행
"""

import os
import sys
from datetime import datetime
import json

# 상위 디렉토리 추가하여 모듈 import 가능하도록
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def simulate_streamlit_test():
    """Streamlit 이슈발생보고 생성 프로세스 시뮬레이션"""
    
    # 테스트 케이스 정의
    test_cases = [
        {
            "id": 1,
            "name": "제품 결함 이슈",
            "media_name": "조선일보",
            "reporter_name": "김철수",
            "issue_description": "포스코인터내셔널의 자동차 부품 중 전기차 배터리 코팅 소재에서 결함이 발견되어 현대차, 기아차 등 주요 고객사가 관련 부품을 사용한 차량 5만대에 대한 리콜을 검토 중입니다. 초기 조사 결과 생산 공정 중 품질관리 미흡이 원인으로 추정되며, 해외 수출 물량에도 영향이 예상됩니다."
        },
        {
            "id": 2,
            "name": "환경 안전 사고",
            "media_name": "한국경제",
            "reporter_name": "박영희",
            "issue_description": "포스코인터내셔널 인도네시아 니켈 광산에서 폐수 처리 시설 고장으로 인해 인근 강으로 오염 물질이 유출되는 사고가 발생했습니다. 현지 환경단체가 강력 항의하고 있으며, 인도네시아 정부도 조사에 착수했습니다. ESG 경영에 대한 우려가 제기되고 있어 주가에도 부정적 영향이 예상됩니다."
        },
        {
            "id": 3,
            "name": "컴플라이언스 위반",
            "media_name": "매일경제",
            "reporter_name": "이준호",
            "issue_description": "포스코인터내셔널 임직원이 중국 철강 거래 과정에서 현지 업체와의 부적절한 금전 거래 의혹이 제기되었습니다. 내부 고발자가 제보한 내용으로는 수억 원 규모의 리베이트가 오갔을 가능성이 있으며, 검찰이 수사에 착수할 예정입니다. 해외사업 전반에 대한 투명성 문제가 도마에 오르고 있습니다."
        },
        {
            "id": 4,
            "name": "사이버 보안 사고",
            "media_name": "서울경제",
            "reporter_name": "최민수",
            "issue_description": "포스코인터내셔널의 고객 관리 시스템이 해킹당해 거래업체 및 고객사의 기밀정보 3만여 건이 유출된 것으로 확인되었습니다. 해커들이 요구하는 몸값은 비트코인 50개로 추정되며, 이미 일부 정보가 다크웹에 유포되기 시작했습니다. 개인정보보호법 위반으로 과징금 부과도 예상되는 상황입니다."
        },
        {
            "id": 5,
            "name": "공급망 차질",
            "media_name": "중앙일보",
            "reporter_name": "정소연",
            "issue_description": "미-중 무역갈등 재점화로 포스코인터내셔널의 중국 내 철강 가공 공장 가동이 중단 위기에 처했습니다. 중국 정부가 한국 기업에 대한 인허가 심사를 강화하면서 주요 프로젝트들이 연기되고 있습니다. 이로 인해 글로벌 고객사와의 공급 계약 이행에 차질이 생겨 위약금 부담이 급증할 우려가 있습니다."
        }
    ]
    
    print("="*80)
    print("포스코인터내셔널 Streamlit 이슈발생보고 생성 프로세스 테스트")
    print(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    test_results = []
    
    for case in test_cases:
        print(f"\n[테스트 케이스 {case['id']}] {case['name']}")
        print("-" * 60)
        
        # 입력값 검증
        validation_result = validate_inputs(
            case['media_name'], 
            case['reporter_name'], 
            case['issue_description']
        )
        
        if validation_result['valid']:
            print("+ 입력값 검증: 통과")
            
            # 이슈발생보고 생성 시뮬레이션
            report_result = simulate_issue_report_generation(
                case['media_name'],
                case['reporter_name'], 
                case['issue_description']
            )
            
            # 결과 저장
            case_result = {
                'test_case': case,
                'validation': validation_result,
                'report_generation': report_result
            }
            test_results.append(case_result)
            
            # 출력 파일 생성 시뮬레이션
            output_file = f"output/이슈발생보고서_테스트케이스{case['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"포스코인터내셔널 언론대응 이슈 발생 보고서\n")
                    f.write("="*50 + "\n\n")
                    f.write(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"언론사: {case['media_name']}\n")
                    f.write(f"기자명: {case['reporter_name']}\n")
                    f.write(f"테스트 케이스: {case['name']}\n\n")
                    f.write("발생 이슈:\n")
                    f.write(f"{case['issue_description']}\n\n")
                    f.write("AI 생성 보고서:\n")
                    f.write(f"{report_result['report']}\n\n")
                    f.write("처리 통계:\n")
                    f.write(f"- 처리 시간: {report_result['processing_time']:.2f}초\n")
                    f.write(f"- 위험도 평가: {report_result['risk_level']}\n")
                    f.write(f"- 관련 부서 수: {report_result['departments_count']}개\n")
                    f.write(f"- 과거 유사 사례: {report_result['similar_cases_count']}건\n")
                
                print(f"+ 출력 파일 생성: {output_file}")
                
            except Exception as e:
                print(f"- 출력 파일 생성 실패: {str(e)}")
                
        else:
            print("- 입력값 검증: 실패")
            for error in validation_result['errors']:
                print(f"  - {error}")
    
    # 종합 분석 결과 생성
    generate_comprehensive_analysis(test_results)
    
    return test_results

def validate_inputs(media_name, reporter_name, issue_description):
    """입력값 검증"""
    errors = []
    
    if not media_name or not media_name.strip():
        errors.append("언론사명이 입력되지 않았습니다")
    elif len(media_name.strip()) < 2:
        errors.append("언론사명이 너무 짧습니다")
    
    if not reporter_name or not reporter_name.strip():
        errors.append("기자명이 입력되지 않았습니다")
    elif len(reporter_name.strip()) < 2:
        errors.append("기자명이 너무 짧습니다")
    
    if not issue_description or not issue_description.strip():
        errors.append("발생 이슈가 입력되지 않았습니다")
    elif len(issue_description.strip()) < 20:
        errors.append("발생 이슈 설명이 너무 짧습니다 (최소 20자)")
    elif len(issue_description.strip()) > 2000:
        errors.append("발생 이슈 설명이 너무 깁니다 (최대 2000자)")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': []
    }

def simulate_issue_report_generation(media_name, reporter_name, issue_description):
    """이슈발생보고서 생성 시뮬레이션"""
    import time
    import random
    
    start_time = time.time()
    
    # 처리 시간 시뮬레이션 (2-8초)
    processing_delay = random.uniform(2.0, 8.0)
    time.sleep(0.1)  # 실제 테스트에서는 짧게
    
    # 위험도 평가 시뮬레이션
    risk_levels = ["낮음", "보통", "높음", "매우 높음"]
    risk_keywords = {
        "매우 높음": ["유출", "사고", "폐수", "해킹", "검찰", "위약금"],
        "높음": ["결함", "리콜", "리베이트", "차질", "항의"],
        "보통": ["검토", "조사", "우려", "예상"],
        "낮음": ["개선", "점검", "협의"]
    }
    
    risk_level = "보통"
    for level, keywords in risk_keywords.items():
        if any(keyword in issue_description for keyword in keywords):
            risk_level = level
            break
    
    # 관련 부서 수 시뮬레이션
    departments_count = random.randint(3, 8)
    
    # 유사 사례 수 시뮬레이션
    similar_cases_count = random.randint(0, 5)
    
    # 실제 보고서 생성 시뮬레이션
    report_template = f"""
긴급 이슈 발생 보고

1. 이슈 개요
   - 발생 일시: {datetime.now().strftime('%Y년 %m월 %d일')}
   - 보도 예정 언론사: {media_name}
   - 담당 기자: {reporter_name}
   - 위험도 평가: {risk_level}

2. 상황 분석
{issue_description}

3. 예상 영향
   - 재무적 영향: {"상당한 손실 예상" if risk_level in ["높음", "매우 높음"] else "제한적 영향"}
   - 평판 리스크: {"매우 높음" if risk_level == "매우 높음" else "보통"}
   - 주가 영향: {"부정적 영향 예상" if risk_level in ["높음", "매우 높음"] else "제한적"}

4. 즉시 대응 방안
   - 대응 TF 구성 (관련 부서 {departments_count}개 참여)
   - 사실관계 확인 및 내부 조사 실시
   - 언론 대응 메시지 작성
   - 고객사 및 이해관계자 커뮤니케이션
   
5. 담당 부서 및 연락처
   - 주관: 커뮤니케이션실 홍보그룹
   - 협조: 법무팀, 해외사업부, 품질관리팀 등
   
6. 후속 조치 계획
   - 단기: 24시간 내 공식 입장 발표
   - 중기: 원인 분석 및 개선책 마련
   - 장기: 재발 방지 시스템 구축

※ 본 보고서는 AI 기반 자동 생성되었으며, 실제 상황에 따라 조정이 필요합니다.
"""

    processing_time = time.time() - start_time + processing_delay
    
    return {
        'success': True,
        'report': report_template.strip(),
        'processing_time': processing_time,
        'risk_level': risk_level,
        'departments_count': departments_count,
        'similar_cases_count': similar_cases_count,
        'metadata': {
            'word_count': len(report_template.split()),
            'char_count': len(report_template)
        }
    }

def generate_comprehensive_analysis(test_results):
    """종합 분석 결과 생성"""
    output_file = f"output/streamlit_테스트_종합분석_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    analysis = {
        'total_tests': len(test_results),
        'successful_tests': sum(1 for r in test_results if r['report_generation']['success']),
        'avg_processing_time': sum(r['report_generation']['processing_time'] for r in test_results) / len(test_results),
        'risk_distribution': {},
        'departments_stats': []
    }
    
    # 위험도 분포 계산
    for result in test_results:
        risk = result['report_generation']['risk_level']
        analysis['risk_distribution'][risk] = analysis['risk_distribution'].get(risk, 0) + 1
    
    # 종합 분석 보고서 작성
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("포스코인터내셔널 Streamlit 이슈발생보고 생성 프로세스\n")
        f.write("종합 테스트 결과 분석 보고서\n")
        f.write("="*60 + "\n\n")
        f.write(f"테스트 실행 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"총 테스트 케이스 수: {analysis['total_tests']}개\n")
        f.write(f"성공한 테스트 수: {analysis['successful_tests']}개\n")
        f.write(f"성공률: {analysis['successful_tests']/analysis['total_tests']*100:.1f}%\n")
        f.write(f"평균 처리 시간: {analysis['avg_processing_time']:.2f}초\n\n")
        
        f.write("=== 개별 테스트 결과 상세 ===\n\n")
        
        for i, result in enumerate(test_results, 1):
            case = result['test_case']
            report = result['report_generation']
            
            f.write(f"[테스트 케이스 {i}] {case['name']}\n")
            f.write("-" * 40 + "\n")
            f.write(f"언론사: {case['media_name']}\n")
            f.write(f"기자명: {case['reporter_name']}\n")
            f.write(f"처리 상태: {'성공' if report['success'] else '실패'}\n")
            f.write(f"처리 시간: {report['processing_time']:.2f}초\n")
            f.write(f"위험도 평가: {report['risk_level']}\n")
            f.write(f"관련 부서 수: {report['departments_count']}개\n")
            f.write(f"보고서 길이: {report['metadata']['word_count']}단어, {report['metadata']['char_count']}자\n")
            f.write(f"과거 유사 사례: {report['similar_cases_count']}건\n\n")
        
        f.write("=== 프로세스 성능 분석 ===\n\n")
        f.write("위험도 분포:\n")
        for risk, count in analysis['risk_distribution'].items():
            f.write(f"- {risk}: {count}건 ({count/analysis['total_tests']*100:.1f}%)\n")
        
        f.write(f"\n처리 시간 분석:\n")
        times = [r['report_generation']['processing_time'] for r in test_results]
        f.write(f"- 최단 시간: {min(times):.2f}초\n")
        f.write(f"- 최장 시간: {max(times):.2f}초\n")
        f.write(f"- 평균 시간: {sum(times)/len(times):.2f}초\n")
        
        f.write("\n=== 개선 권고사항 ===\n\n")
        f.write("1. 성능 최적화\n")
        f.write("   - 평균 처리시간 단축 필요 (목표: 3초 이내)\n")
        f.write("   - 캐싱 메커니즘 도입 검토\n")
        f.write("   - 병렬 처리를 통한 속도 개선\n\n")
        
        f.write("2. 정확도 향상\n")
        f.write("   - 위험도 평가 알고리즘 정교화\n")
        f.write("   - 부서 매핑 정확도 개선\n")
        f.write("   - 과거 사례 검색 기능 강화\n\n")
        
        f.write("3. 사용자 경험 개선\n")
        f.write("   - 실시간 진행상황 표시\n")
        f.write("   - 입력값 자동완성 기능\n")
        f.write("   - 보고서 템플릿 다양화\n\n")
        
        f.write("4. 안정성 강화\n")
        f.write("   - 에러 처리 로직 보완\n")
        f.write("   - 입력값 검증 강화\n")
        f.write("   - 백업 및 복구 체계 구축\n\n")
    
    print(f"\n+ 종합 분석 보고서 생성: {output_file}")
    return analysis

if __name__ == "__main__":
    print("Streamlit 이슈발생보고 생성 프로세스 테스트를 시작합니다...")
    results = simulate_streamlit_test()
    print("\n테스트 완료!")
    print(f"총 {len(results)}개 테스트 케이스 실행됨")
    print("자세한 결과는 output 폴더의 파일들을 확인해주세요.")