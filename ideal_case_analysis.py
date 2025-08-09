#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이상적 답변 사례 분석 및 벤치마킹
"""

def analyze_ideal_case():
    """이상적 사례의 특징 분석"""
    
    ideal_case_features = {
        "구조적_특징": {
            "템플릿_준수": "완벽한 6단계 구조",
            "일시_형식": "2025. 08. 09. 10:30 (간결한 형식)",
            "위기_단계": "1단계(관심) - 적절한 낮은 단계",
            "언론사_기자": "조선일보, 김조선 기자 - 명확한 표기"
        },
        
        "내용적_특징": {
            "이슈_성격": "단순 정보 문의 (문제 상황 아님)",
            "대응_부서": "소재바이오사업운영섹션/김준표 리더 - 구체적 담당자",
            "사실_확인": "매우 구체적이고 전문적인 사업 정보",
            "설명_논리": "긍정적 프레임 + 제한사항 합리적 설명"
        },
        
        "품질적_특징": {
            "사실성": "구체적 수치와 지역명 포함",
            "전문성": "업계 용어와 사업 구조 정확 설명",
            "균형성": "공개 가능 정보 vs 비공개 정보 구분",
            "대응성": "기자 질문에 직접적 답변"
        },
        
        "커뮤니케이션_특징": {
            "톤앤매너": "전문적이면서 협조적",
            "메시지_일관성": "식량안보 기여라는 큰 그림 제시",
            "투명성": "공개 한계 명확히 설명",
            "원보이스": "구체적이고 실행 가능한 메시지"
        }
    }
    
    return ideal_case_features

def extract_improvement_points():
    """현재 시스템 대비 개선 필요 영역"""
    
    improvement_areas = {
        "HIGH_PRIORITY": {
            "구체성_부족": {
                "문제": "일반적인 표현이 많고 구체적 정보 부족",
                "목표": "지역명, 수치, 업계 용어 등 구체적 정보 포함",
                "예시": "'해외 거점' → '우크라이나·호주·미얀마 등 해외 곡물 생산 거점'"
            },
            
            "담당자_정보": {
                "문제": "부서명만 언급, 구체적 담당자 없음",
                "목표": "부서/담당자명 구체적 표기",
                "예시": "'경영기획팀' → '소재바이오사업운영섹션/김준표 리더'"
            },
            
            "메시지_실행가능성": {
                "문제": "추상적 원보이스, 실제 사용하기 어려움",
                "목표": "기자가 바로 인용할 수 있는 구체적 메시지",
                "예시": "구체적 인용문 형태로 제공"
            }
        },
        
        "MEDIUM_PRIORITY": {
            "일시_형식": {
                "문제": "2025년 8월 9일 15시 8분 (장황함)",
                "목표": "2025. 08. 09. 10:30 (간결함)",
                "구현": "날짜 형식 변경"
            },
            
            "위기단계_정확도": {
                "문제": "단순 문의도 2단계(주의)로 분류하는 경우",
                "목표": "이슈 성격에 따른 정확한 단계 분류",
                "구현": "키워드 기반 분류 알고리즘 개선"
            },
            
            "설명논리_구조": {
                "문제": "사실 확인 + 일반적 설명",
                "목표": "긍정적 프레임 + 제한사항 합리적 설명",
                "구현": "프롬프트 개선"
            }
        },
        
        "LOW_PRIORITY": {
            "언어_톤": {
                "문제": "다소 딱딱한 공식적 어투",
                "목표": "전문적이면서 협조적인 톤",
                "구현": "언어 스타일 조정"
            }
        }
    }
    
    return improvement_areas

def create_benchmark_test():
    """벤치마킹 테스트 케이스 생성"""
    
    benchmark_cases = [
        {
            "name": "식량사업_문의_사례",
            "input": {
                "media": "조선일보",
                "reporter": "김조선",
                "issue": "포스코인터내셔널 식량사업 생산지, 주요 납품처, 올해 매출 계획 관련 문의"
            },
            "expected_features": {
                "위기단계": "1단계(관심)",
                "담당부서": "소재바이오사업운영섹션",
                "구체적_정보": ["우크라이나", "호주", "미얀마", "곡물", "수십만 톤"],
                "원보이스": "구체적 인용문 형태",
                "설명논리": "긍정적 프레임 + 비공개 정보 한계 설명"
            }
        },
        
        {
            "name": "일반_사업_문의",
            "input": {
                "media": "매일경제",
                "reporter": "이기자",
                "issue": "포스코인터내셔널 철강사업부 올해 실적 및 향후 계획 문의"
            },
            "expected_features": {
                "위기단계": "1단계(관심)",
                "구체적_정보": "사업부별 실적, 지역별 현황",
                "비공개_처리": "구체적 수치는 비공개, 대신 전략 방향성 제시"
            }
        }
    ]
    
    return benchmark_cases

def main():
    print("=== 이상적 답변 사례 분석 ===")
    
    # 1. 이상적 사례 특징 분석
    features = analyze_ideal_case()
    print("\n1. 이상적 사례 특징:")
    for category, items in features.items():
        print(f"\n[{category}]")
        for key, value in items.items():
            print(f"  - {key}: {value}")
    
    # 2. 개선 영역 도출
    improvements = extract_improvement_points()
    print("\n\n=== 개선 필요 영역 ===")
    for priority, areas in improvements.items():
        print(f"\n[{priority}]")
        for area, details in areas.items():
            print(f"  - {area}:")
            print(f"    문제: {details['문제']}")
            print(f"    목표: {details['목표']}")
            if '예시' in details:
                print(f"    예시: {details['예시']}")
    
    # 3. 벤치마킹 테스트 케이스
    benchmarks = create_benchmark_test()
    print("\n\n=== 벤치마킹 테스트 케이스 ===")
    for i, case in enumerate(benchmarks, 1):
        print(f"\n{i}. {case['name']}:")
        print(f"   입력: {case['input']['issue']}")
        print(f"   기대 특징:")
        for key, value in case['expected_features'].items():
            print(f"     - {key}: {value}")
    
    return features, improvements, benchmarks

if __name__ == "__main__":
    main()