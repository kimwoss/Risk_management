from typing import Optional
from src.services import OpenAIService, SearchService
from src.utils import DataLoader, Logger

class RiskAnalyzer:
    """위기 대응 분석 메인 클래스"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.openai_service = OpenAIService()
        self.search_service = SearchService()
        self.data_loader = DataLoader()
    
    def analyze_query(self, query: str, include_similar_cases: bool = True) -> dict:
        """쿼리 분석 및 응답 생성"""
        self.logger.info(f"위기 분석 시작: {query}")
        
        result = {
            'query': query,
            'gpt_response': None,
            'similar_cases': [],
            'success': False
        }
        
        try:
            # GPT 응답 생성
            result['gpt_response'] = self.openai_service.ask_gpt(query)
            
            # 유사 사례 검색 (선택사항)
            if include_similar_cases:
                result['similar_cases'] = self.search_service.search_similar_issues(query)
            
            result['success'] = True
            self.logger.info("위기 분석 완료")
            
        except Exception as e:
            error_msg = f"위기 분석 중 오류: {str(e)}"
            self.logger.error(error_msg)
            result['error'] = error_msg
        
        return result
    
    def display_analysis_result(self, result: dict):
        """분석 결과 출력"""
        if not result['success']:
            print(f"❌ 분석 실패: {result.get('error', '알 수 없는 오류')}")
            return
        
        print(f"\n🔍 쿼리: {result['query']}")
        print(f"\n💡 GPT 응답:\n{result['gpt_response']}")
        
        if result['similar_cases']:
            print(f"\n📋 유사 사례 ({len(result['similar_cases'])}건):")
            self.search_service.display_search_results(
                result['similar_cases'], 
                result['query']
            )
    
    def run_interactive_mode(self):
        """대화형 모드 실행"""
        print("🎯 위기 대응 분석 시스템 - 대화형 모드")
        print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")
        
        while True:
            try:
                query = input("📝 질문을 입력하세요: ").strip()
                
                if query.lower() in ['quit', 'exit', '종료']:
                    print("👋 시스템을 종료합니다.")
                    break
                
                if not query:
                    print("⚠️ 질문을 입력해주세요.")
                    continue
                
                # 분석 실행
                result = self.analyze_query(query)
                self.display_analysis_result(result)
                print("\n" + "="*50 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 시스템을 종료합니다.")
                break
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
    
    def load_and_preview_data(self, preview_count: Optional[int] = None):
        """데이터 로드 및 미리보기"""
        try:
            df = self.data_loader.load_csv()
            print(f"✅ 총 {len(df)}건의 기자문의 데이터를 로드했습니다.")
            
            self.data_loader.preview_entries(df, preview_count)
            return df
            
        except Exception as e:
            error_msg = f"데이터 로드 실패: {str(e)}"
            self.logger.error(error_msg)
            print(f"❌ {error_msg}")
            return None