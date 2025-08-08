import os
from dotenv import load_dotenv
from llm_manager import LLMManager
from data_based_llm import DataBasedLLM
from data_version_manager import DataVersionManager

def setup_check():
    """환경 설정 확인"""
    load_dotenv()
    
    print("=== NEW RISK MANAGEMENT SYSTEM ===")
    print("환경 설정 확인 중...")
    
    # 기본 환경 변수 확인
    db_host = os.getenv('DB_HOST', 'localhost')
    environment = os.getenv('ENVIRONMENT', 'development')
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    print(f"✓ 환경: {environment}")
    print(f"✓ 디버그 모드: {debug}")
    print(f"✓ DB 호스트: {db_host}")
    
    # OpenAI API 키 확인
    api_key = os.getenv('OPEN_API_KEY')
    if api_key:
        print(f"✓ OpenAI API 키 설정됨 (길이: {len(api_key)})")
        return True
    else:
        print("✗ OpenAI API 키가 설정되지 않았습니다")
        return False

def run_basic_tests():
    """기본 LLM 기능 테스트"""
    print("\n=== 기본 LLM 기능 테스트 ===")
    
    try:
        llm = LLMManager(model="gpt-4", data_folder="data")
        
        # 1. 간단한 채팅 테스트
        print("\n1. 기본 채팅 테스트")
        response = llm.chat("안녕하세요! 간단히 자기소개 해주세요.")
        print(f"AI: {response[:100]}..." if len(response) > 100 else f"AI: {response}")
        
        # 2. 코드 생성 테스트
        print("\n2. 코드 생성 테스트")
        code = llm.generate_code("리스트의 평균값을 계산하는 함수", "Python")
        print(f"생성된 코드:\n{code}")
        
        return True
        
    except Exception as e:
        print(f"✗ 기본 테스트 실패: {str(e)}")
        return False

def check_data_versions():
    """데이터 파일 버전 확인"""
    print("\n=== 데이터 버전 확인 ===")
    
    try:
        version_manager = DataVersionManager()
        
        # 데이터 무결성 검사
        integrity_results = version_manager.check_data_integrity()
        
        # 버전 정보 출력
        version_info = version_manager.list_all_versions()
        print(version_info)
        
        # 모든 파일이 정상인지 확인
        all_valid = all(integrity_results.values())
        
        if all_valid:
            print("✅ 모든 데이터 파일이 정상입니다.")
        else:
            print("⚠️ 일부 데이터 파일에 문제가 있습니다.")
            
        return all_valid
        
    except Exception as e:
        print(f"✗ 데이터 버전 확인 실패: {str(e)}")
        return False

def run_data_based_tests():
    """데이터 기반 답변 기능 테스트"""
    print("\n=== 데이터 기반 답변 테스트 ===")
    
    try:
        data_llm = DataBasedLLM()
        
        # 1. 부서 정보 기반 질의
        print("\n1. 부서 정보 기반 질의 테스트")
        query1 = "배당 관련 이슈 담당자를 알려주세요"
        response1 = data_llm.generate_data_based_response(query1)
        print(f"질문: {query1}")
        print(f"답변: {response1[:300]}..." if len(response1) > 300 else f"답변: {response1}")
        
        # 2. 언론대응 사례 기반 질의
        print("\n2. 언론대응 사례 기반 질의 테스트")
        query2 = "전기차 관련 보도에 대한 대응 방안"
        response2 = data_llm.generate_data_based_response(query2)
        print(f"질문: {query2}")
        print(f"답변: {response2[:300]}..." if len(response2) > 300 else f"답변: {response2}")
        
        return True
        
    except Exception as e:
        print(f"✗ 데이터 기반 테스트 실패: {str(e)}")
        return False

def interactive_chat():
    """대화형 채팅 모드"""
    print("\n=== 대화형 채팅 모드 ===")
    print("종료하려면 'quit', 'exit', '종료' 입력")
    print("리스크 분석 모드: '/risk [회사정보]'")
    print("VaR 계산 모드: '/var [포트폴리오정보]'")
    print("데이터 기반 답변: '/data [질문]'")
    print("대응 전략 추천: '/strategy [이슈설명]'")
    print("이슈 웹 검색 연구: '/research [발생이슈]'")
    print("강화된 사실검증 & 대응방안: '/enhanced [발생이슈]'")
    print("🚀 최적화된 고속 분석: '/fast [발생이슈]'")
    print("트렌드 분석: '/trend'")
    print("캐시 관리: '/cache clear' 또는 '/cache status'")
    print("버전 정보: '/version'")
    print("데이터 백업: '/backup [파일명] [설명] [변경유형]'")
    print("-" * 40)
    
    try:
        llm = LLMManager(model="gpt-4", data_folder="data")
        data_llm = DataBasedLLM()
        version_manager = DataVersionManager()
        
        while True:
            user_input = input("\n사용자: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '종료']:
                print("채팅을 종료합니다.")
                break
            
            if not user_input:
                continue
            
            # 특수 명령어 처리
            if user_input.startswith('/risk '):
                company_info = user_input[6:]
                response = llm.analyze_credit_risk(company_info)
            elif user_input.startswith('/var '):
                portfolio_info = user_input[5:]
                response = llm.calculate_var_explanation(portfolio_info)
            elif user_input.startswith('/data '):
                query = user_input[6:]
                response = data_llm.generate_data_based_response(query)
            elif user_input.startswith('/strategy '):
                issue = user_input[10:]
                response = data_llm.recommend_response_strategy(issue)
            elif user_input.startswith('/research '):
                issue = user_input[10:]
                print("🔍 웹 검색을 통한 이슈 연구를 시작합니다...")
                response = data_llm.research_issue_with_web_search(issue)
            elif user_input.startswith('/enhanced '):
                issue = user_input[11:]
                print("🔍 강화된 웹 검색 기반 사실검증 및 대응방안을 생성합니다...")
                response = data_llm.generate_enhanced_response_with_fact_check(issue)
            elif user_input.startswith('/fast '):
                issue = user_input[6:]
                print("🚀 최적화된 고속 웹 검색 기반 분석을 시작합니다...")
                response = data_llm.generate_optimized_response_with_fact_check(issue)
            elif user_input == '/cache clear':
                data_llm.clear_all_caches()
                response = "캐시가 초기화되었습니다."
            elif user_input == '/cache status':
                if hasattr(data_llm, 'optimized_research') and data_llm.optimized_research:
                    cache_status = data_llm.optimized_research._get_cache_status()
                    response = f"캐시 상태: 메모리 {cache_status.get('memory_cache_size', 0)}개 항목"
                else:
                    response = "캐시 시스템을 사용할 수 없습니다."
            elif user_input == '/trend':
                response = data_llm.analyze_issue_trends(30)
            elif user_input == '/version':
                response = version_manager.list_all_versions()
            elif user_input.startswith('/backup '):
                parts = user_input[8:].split(' ', 2)
                if len(parts) >= 1:
                    file_name = parts[0]
                    description = parts[1] if len(parts) > 1 else "수동 백업"
                    change_type = parts[2] if len(parts) > 2 else "patch"
                    
                    success = version_manager.create_backup(file_name, description, change_type)
                    response = f"백업 {'성공' if success else '실패'}: {file_name}"
                else:
                    response = "사용법: /backup [파일명] [설명] [변경유형]"
            else:
                # 일반 채팅
                response = llm.conversation_chat(user_input)
            
            print(f"AI: {response}")
    
    except KeyboardInterrupt:
        print("\n채팅이 중단되었습니다.")
    except Exception as e:
        print(f"채팅 중 오류 발생: {str(e)}")

def main():
    """메인 실행 함수"""
    # 1. 환경 설정 확인
    if not setup_check():
        print("\n환경 설정을 확인해주세요.")
        return
    
    # 2. 데이터 버전 및 무결성 확인
    if not check_data_versions():
        print("\n데이터 파일 확인이 필요합니다.")
        print("📋 자세한 내용은 DATA_UPDATE_GUIDE.md를 참조하세요.")
    
    # 3. 기본 기능 테스트
    if not run_basic_tests():
        print("\n기본 기능 테스트에 실패했습니다.")
        return
    
    # 4. 데이터 기반 답변 기능 테스트
    if not run_data_based_tests():
        print("\n데이터 기반 답변 기능 테스트에 실패했습니다.")
        return
    
    print("\n" + "=" * 50)
    print("✓ 모든 테스트가 성공적으로 완료되었습니다!")
    print("=" * 50)
    
    # 5. 대화형 모드 실행 여부 확인
    choice = input("\n대화형 채팅을 시작하시겠습니까? (y/n): ").lower()
    if choice in ['y', 'yes', '예', 'ㅇ']:
        interactive_chat()

if __name__ == "__main__":
    main()
