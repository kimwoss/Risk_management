#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
세 번째 이상적 사례 분석 - 3단계 위기 사례 (미얀마 가스전)
"""

def analyze_third_ideal_case():
    """세 번째 이상적 사례 분석 - 고위험 정치적 민감 사안"""
    
    third_case_features = {
        "위기_특성": {
            "위기단계": "3단계(위기) - 기존 1단계와 완전히 다른 수준",
            "이슈_복잡도": "매우 높음 (정치적 민감성 + 제재 + ESG)",
            "대응_긴급도": "높음 (군부 연관 의혹)",
            "파급_범위": "국제적 (EU/미국 제재 관련)"
        },
        
        "내용_복잡성": {
            "다중_질문": "4개의 서로 다른 질문 (실적/개발/관계/의혹)",
            "전문_용어": "PSC, UJV, EPC, MOGE, OFAC, HRDD 등",
            "법적_쟁점": "국제 제재, 준법 환경, 인권실사",
            "사업_구조": "비법인 합작, 생산물분배계약"
        },
        
        "대응_조직": {
            "다부서_협업": "법무+ESG+대외협력 동시 협의",
            "보고_라인": "대표이사/홀딩스 보고",
            "현업_담당자": "2개 부서 + 직통 연락처",
            "담당자_구체성": "이름+직급+연락처 완전 공개"
        },
        
        "메시지_전략": {
            "원보이스_길이": "4개 문장의 체계적 구성",
            "방어_논리": "PSC 구조 → 제재 준수 → 비공개 원칙 → 공시 참조",
            "Q&A_브릿지": "군부 관계 질문에 대한 사전 대응 준비",
            "법적_방어": "제재 준수 + 내부 통제 강조"
        }
    }
    
    return third_case_features

def compare_crisis_levels():
    """위기단계별 대응 특성 비교"""
    
    crisis_comparison = {
        "1단계_관심": {
            "이슈_성격": "단순 문의, 정보 요청",
            "대응_조직": "해당 부서 단독 대응",
            "메시지_톤": "협조적, 정보 제공 중심",
            "보고_라인": "부서 내 처리",
            "예시": "식량사업 생산지 문의, 실적 문의"
        },
        
        "2단계_주의": {
            "이슈_성격": "부정적 가능성, 모니터링 필요",
            "대응_조직": "관련 부서 + 홍보팀",
            "메시지_톤": "신중함, 사실 기반",
            "보고_라인": "팀장급 보고"
        },
        
        "3단계_위기": {
            "이슈_성격": "심각한 평판 리스크, 법적 쟁점",
            "대응_조직": "다부서 TF (법무+ESG+대외협력)",
            "메시지_톤": "방어적, 법적 근거 중심",
            "보고_라인": "대표이사/홀딩스 보고",
            "예시": "미얀마 군부 연관 의혹"
        },
        
        "4단계_비상": {
            "이슈_성격": "회사 존립 위협, 즉시 대응",
            "대응_조직": "전사 위기관리위원회",
            "메시지_톤": "공식 성명, 강력 대응",
            "보고_라인": "이사회 긴급 소집"
        }
    }
    
    return crisis_comparison

def identify_advanced_gaps():
    """고위험 사안 대응을 위한 시스템 부족점"""
    
    advanced_gaps = {
        "CRITICAL": {
            "위기단계_판정": {
                "현재": "키워드 기반 단순 분류",
                "필요": "복합 요소 분석 (정치적 민감성, 제재 관련, ESG 리스크)",
                "구현": "고위험 키워드 데이터베이스 + 가중치 알고리즘"
            },
            
            "다부서_협업": {
                "현재": "단일 부서 담당자 지정",
                "필요": "법무+ESG+대외협력 동시 협의 체계",
                "구현": "위기 수준별 협업 매트릭스"
            },
            
            "법적_방어논리": {
                "현재": "일반적 설명 중심",
                "필요": "제재 준수, 내부 통제, 준법 경영 강조",
                "구현": "법무 전문 템플릿 + 용어집"
            }
        },
        
        "HIGH": {
            "전문_용어_체계": {
                "현재": "일반 비즈니스 용어",
                "필요": "PSC, UJV, EPC 등 에너지 전문용어 + 법률 용어",
                "구현": "업종별 전문용어 데이터베이스"
            },
            
            "원보이스_구조화": {
                "현재": "단순한 인용문",
                "필요": "체계적 4단계 구성 (사업구조→준법→비공개→참조)",
                "구현": "위기 수준별 메시지 템플릿"
            },
            
            "연락처_관리": {
                "현재": "일반적 담당자명",
                "필요": "직통 전화번호 포함 완전한 연락처",
                "구현": "비상 연락망 데이터베이스"
            }
        },
        
        "MEDIUM": {
            "Q&A_브릿지": {
                "현재": "없음",
                "필요": "예상 추가 질문에 대한 사전 대응 메시지",
                "구현": "이슈별 Q&A 템플릿"
            },
            
            "보고라인_자동화": {
                "현재": "일반적 언급",
                "필요": "위기 수준별 보고 체계 명시",
                "구현": "조직도 기반 에스컬레이션"
            }
        }
    }
    
    return advanced_gaps

def create_crisis_test_cases():
    """위기 사안 테스트 케이스"""
    
    crisis_test_cases = [
        {
            "name": "미얀마_가스전_의혹",
            "input": {
                "media": "동아일보",
                "reporter": "김동아",
                "issue": "미얀마 가스전 실적 개선 배경, 4단계 개발 진척, 군부 관계, 영업이익 지원금 의혹 해명 요구"
            },
            "expected_features": {
                "위기단계": "3단계(위기)",
                "담당부서": ["가스사업운영섹션/김승모 부장", "대외협력그룹/고영택 차장"],
                "전문용어": ["PSC", "UJV", "EPC", "MOGE", "OFAC", "HRDD"],
                "법적방어": "국제 제재 준수, 내부 통제 강화",
                "원보이스_구조": "4단계 논리 구성",
                "연락처": "직통 전화번호 포함"
            }
        },
        
        {
            "name": "ESG_인권_리스크",
            "input": {
                "media": "한겨레",
                "reporter": "박한겨례",
                "issue": "포스코인터내셔널 해외 투자 사업장의 인권 침해 의혹 및 ESG 경영 실태"
            },
            "expected_features": {
                "위기단계": "3단계(위기)",
                "법적대응": "HRDD, 국제 가이드라인 준수",
                "다부서협업": "법무+ESG+대외협력"
            }
        },
        
        {
            "name": "국제제재_위반_의혹",
            "input": {
                "media": "경향신문",
                "reporter": "이경향",
                "issue": "러시아 제재 대상 기업과의 거래 연관성 및 제재 위반 가능성"
            },
            "expected_features": {
                "위기단계": "3단계(위기)",
                "법적방어": "제재 준수 체계, 준법 모니터링",
                "보고라인": "대표이사 보고"
            }
        }
    ]
    
    return crisis_test_cases

def main():
    print("=== 세 번째 이상적 사례 분석 (3단계 위기 사안) ===")
    
    # 1. 세 번째 이상적 사례 특징
    features = analyze_third_ideal_case()
    print("\n1. 위기 사안 특징:")
    for category, items in features.items():
        print(f"\n[{category}]")
        for key, value in items.items():
            print(f"  - {key}: {value}")
    
    # 2. 위기단계별 비교
    comparison = compare_crisis_levels()
    print("\n\n=== 위기단계별 대응 특성 비교 ===")
    for level, characteristics in comparison.items():
        print(f"\n[{level}]")
        for key, value in characteristics.items():
            print(f"  - {key}: {value}")
    
    # 3. 고위험 대응 부족점
    gaps = identify_advanced_gaps()
    print("\n\n=== 고위험 사안 대응 시스템 부족점 ===")
    for priority, areas in gaps.items():
        print(f"\n[{priority}]")
        for area, details in areas.items():
            print(f"  - {area}:")
            print(f"    현재: {details['현재']}")
            print(f"    필요: {details['필요']}")
            print(f"    구현: {details['구현']}")
    
    # 4. 위기 사안 테스트 케이스
    test_cases = create_crisis_test_cases()
    print("\n\n=== 위기 사안 테스트 케이스 ===")
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. {case['name']}:")
        print(f"   이슈: {case['input']['issue']}")
        print(f"   기대 특징:")
        for key, value in case['expected_features'].items():
            print(f"     - {key}: {value}")
    
    return features, comparison, gaps, test_cases

if __name__ == "__main__":
    main()