#!/usr/bin/env python3
"""
위기관리 커뮤니케이션 시스템 메인 실행 파일
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.core import RiskAnalyzer
from src.utils import Logger

def main():
    """메인 실행 함수"""
    logger = Logger.get_logger("main")
    
    try:
        print("📋 위기관리 커뮤니케이션 시스템 시작...")
        
        # RiskAnalyzer 초기화
        analyzer = RiskAnalyzer()
        
        # 데이터 로드 및 미리보기
        df = analyzer.load_and_preview_data()
        if df is None:
            return
        
        # GPT 테스트
        print("\n💡 GPT 응답 테스트:")
        sample_question = "주의 단계 이슈의 핵심 대응 전략은 무엇인가요?"
        
        result = analyzer.analyze_query(sample_question)
        analyzer.display_analysis_result(result)
        
        # 대화형 모드 옵션
        print("\n" + "="*50)
        continue_interactive = input("대화형 모드를 시작하시겠습니까? (y/n): ").strip().lower()
        
        if continue_interactive in ['y', 'yes', '예']:
            analyzer.run_interactive_mode()
        
    except Exception as e:
        logger.error(f"메인 실행 중 오류: {e}")
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()