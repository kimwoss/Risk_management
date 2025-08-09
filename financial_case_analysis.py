#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
두 번째 이상적 사례 분석 - 실적 공시 유형
"""

def analyze_second_ideal_case():
    """두 번째 이상적 사례 분석"""
    
    second_case_features = {
        "기본_정보": {
            "이슈_성격": "실적 문의 (정기 공시 사항)",
            "위기_단계": "1단계(관심) - 적정",
            "담당_부서": "IR그룹/유근석 리더 - 매우 구체적",
            "일시_형식": "2025. 08. 09. 13:00 - 이상적 간결 형식"
        },
        
        "내용_특징": {
            "구체적_수치": {
                "매출": "약 8조 1,440억 원",
                "영업이익": "약 3,137억 원", 
                "순이익": "약 905억 원",
                "증감률": "전년 동기 대비 -1.7%, -10.3%, -52.3%"
            },
            "사업부문별_세분화": {
                "철강부문": "글로벌 수요 회복, 고부가 제품 확대",
                "에너지부문": "언급 (일부 내용 누락됨)",
                "전체전망": "핵심 사업 안정적 성장, 공급망 강화, 재무구조 개선"
            }
        },
        
        "고급_특징": {
            "투명성": "구체적 실적 수치 완전 공개",
            "균형성": "부정적 실적도 정확히 제시",
            "전문성": "IR 전문 용어 활용 (연결기준, 영업이익 등)",
            "전략적_메시징": "단기 악화를 장기 성장 맥락에서 설명"
        },
        
        "결과_모니터링": {
            "성과": "단일 기사 게재, 공시자료 인용 중심",
            "평가": "부정적 해석 없이 마무리",
            "핵심": "투명한 공개가 신뢰성 확보로 이어짐"
        }
    }
    
    return second_case_features

def compare_case_types():
    """첫 번째(식량사업 문의) vs 두 번째(실적 문의) 사례 비교"""
    
    case_comparison = {
        "공통점": {
            "위기단계": "1단계(관심) - 문의성 이슈는 낮은 단계",
            "날짜형식": "2025. 08. 09. XX:XX - 간결한 형식",
            "담당자명시": "부서명/담당자명 - 구체적 표기",
            "사실기반접근": "정확한 정보 제공 우선"
        },
        
        "차이점": {
            "정보공개범위": {
                "식량사업": "일부 비공개 (매출계획 수치)",
                "실적문의": "완전 공개 (법정 공시사항)"
            },
            "수치구체성": {
                "식량사업": "정성적 표현 ('수십만 톤')",
                "실적문의": "정량적 표현 ('8조 1,440억 원')"
            },
            "대응톤": {
                "식량사업": "긍정적 기여 강조",
                "실적문의": "객관적 사실 중심"
            }
        },
        
        "시사점": {
            "맞춤형대응": "이슈 유형별 차별화된 접근 필요",
            "정보공개원칙": "공시사항은 투명하게, 전략정보는 선별적으로",
            "메시징전략": "사업문의는 가치제안, 실적문의는 객관적 설명"
        }
    }
    
    return case_comparison

def identify_system_gaps():
    """현재 시스템의 실적 공시 유형 대응 부족점"""
    
    gaps_analysis = {
        "HIGH_PRIORITY": {
            "구체적_재무수치": {
                "현재상태": "일반적 표현 ('양호한 실적')",
                "개선필요": "정확한 금액과 증감률 표시",
                "구현방법": "재무데이터 DB 연동 또는 템플릿 확장"
            },
            
            "사업부문별_세분화": {
                "현재상태": "전체적 언급",
                "개선필요": "철강/에너지/식량/기타 부문별 구분",
                "구현방법": "사업부문 매핑 로직 강화"
            },
            
            "IR전문용어": {
                "현재상태": "일반 비즈니스 용어",
                "개선필요": "연결기준, EBITDA, ROE 등 IR 전문용어",
                "구현방법": "용어사전 확장"
            }
        },
        
        "MEDIUM_PRIORITY": {
            "증감률_분석": {
                "현재상태": "정성적 평가 ('개선', '악화')",
                "개선필요": "정확한 퍼센트 증감률",
                "구현방법": "전년동기 비교 로직"
            },
            
            "투명성_균형": {
                "현재상태": "긍정적 측면 강조",
                "개선필요": "부정적 실적도 객관적 제시",
                "구현방법": "프롬프트 균형성 강화"
            }
        },
        
        "LOW_PRIORITY": {
            "결과모니터링": {
                "현재상태": "대응결과 일반적 언급",
                "개선필요": "구체적 결과 추적",
                "구현방법": "후속 모니터링 시스템"
            }
        }
    }
    
    return gaps_analysis

def create_financial_test_cases():
    """실적 공시 유형 테스트 케이스 생성"""
    
    financial_test_cases = [
        {
            "name": "2분기_실적_문의",
            "input": {
                "media": "조선일보",
                "reporter": "김조선",
                "issue": "2025년 2분기 포스코인터내셔널 주요사업별 실적과 향후 계획 관련 문의"
            },
            "expected_features": {
                "위기단계": "1단계(관심)",
                "담당부서": "IR그룹/유근석 리더",
                "구체적_수치": ["8조", "3,137억", "905억", "1.7%", "10.3%", "52.3%"],
                "사업부문": ["철강", "에너지", "식량"],
                "전문용어": ["연결기준", "영업이익", "순이익", "전년동기대비"],
                "균형성": "부정적 실적도 객관적 제시"
            }
        },
        
        {
            "name": "연간_실적_발표",
            "input": {
                "media": "매일경제",
                "reporter": "이경제",
                "issue": "포스코인터내셔널 2024년 연간 실적 발표 및 2025년 사업 계획"
            },
            "expected_features": {
                "위기단계": "1단계(관심)",
                "구체적_수치": "연매출, 영업이익, 당기순이익",
                "사업계획": "부문별 목표 및 전략"
            }
        },
        
        {
            "name": "배당정책_문의",
            "input": {
                "media": "한국경제",
                "reporter": "박한경",
                "issue": "포스코인터내셔널 2025년 배당 정책 및 주주환원 계획 문의"
            },
            "expected_features": {
                "위기단계": "1단계(관심)",
                "전문용어": ["배당수익률", "주주환원", "잉여현금흐름"],
                "IR_대응": "투자자 관점 메시징"
            }
        }
    ]
    
    return financial_test_cases

def main():
    print("=== 두 번째 이상적 사례 분석 (실적 공시 유형) ===")
    
    # 1. 두 번째 이상적 사례 특징
    features = analyze_second_ideal_case()
    print("\n1. 실적 공시 사례 특징:")
    for category, items in features.items():
        print(f"\n[{category}]")
        if isinstance(items, dict):
            for key, value in items.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"    - {sub_key}: {sub_value}")
                else:
                    print(f"  - {key}: {value}")
        else:
            print(f"  - {items}")
    
    # 2. 사례 유형 비교
    comparison = compare_case_types()
    print("\n\n=== 사례 유형 비교 분석 ===")
    for category, items in comparison.items():
        print(f"\n[{category}]")
        for key, value in items.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    - {sub_key}: {sub_value}")
            else:
                print(f"  - {key}: {value}")
    
    # 3. 시스템 부족점 분석
    gaps = identify_system_gaps()
    print("\n\n=== 시스템 개선 필요 영역 (실적 공시 대응) ===")
    for priority, areas in gaps.items():
        print(f"\n[{priority}]")
        for area, details in areas.items():
            print(f"  - {area}:")
            print(f"    현재: {details['현재상태']}")
            print(f"    목표: {details['개선필요']}")
            print(f"    방법: {details['구현방법']}")
    
    # 4. 테스트 케이스
    test_cases = create_financial_test_cases()
    print("\n\n=== 실적 공시 유형 테스트 케이스 ===")
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}:")
        print(f"   입력: {case['input']['issue']}")
        print(f"   기대 특징:")
        for key, value in case['expected_features'].items():
            print(f"     - {key}: {value}")
    
    return features, comparison, gaps, test_cases

if __name__ == "__main__":
    main()