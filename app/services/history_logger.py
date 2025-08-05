# app/services/history_logger.py

import pandas as pd
from datetime import datetime
import os
from pathlib import Path

# 프로젝트 루트 기준 경로 설정
project_root = Path(__file__).parent.parent.parent
HISTORY_PATH = project_root / "data" / "history.csv"

class HistoryLogger:
    """보고서 생성 이력 관리 클래스"""
    
    def __init__(self):
        """히스토리 로거 초기화"""
        self.history_path = HISTORY_PATH
        self._ensure_data_directory()
        self._ensure_csv_headers()
    
    def _ensure_data_directory(self):
        """data 디렉토리 존재 확인 및 생성"""
        self.history_path.parent.mkdir(exist_ok=True)
    
    def _ensure_csv_headers(self):
        """CSV 파일 헤더 확인 및 생성"""
        if not self.history_path.exists():
            headers = {
                "작성일시": [],
                "매체/기자": [],
                "문의내용": [],
                "외부기사URL": [],
                "대응결과": [],
                "위기단계": [],
                "담당부서": [],
                "생성보고서": []
            }
            df = pd.DataFrame(headers)
            df.to_csv(self.history_path, index=False, encoding="utf-8-sig")
    
    def save_history(self, input_data: dict, report_text: str, analysis_result: dict = None):
        """
        사용자 입력 데이터와 GPT 보고서를 받아, 이력을 CSV 파일로 저장합니다.
        
        Args:
            input_data: 사용자 입력 데이터 (input_form에서 반환)
            report_text: 생성된 보고서 텍스트
            analysis_result: 분석 결과 (위기단계, 담당부서 등)
        """
        # 저장 옵션 확인
        if not input_data.get("save_history", True):
            return False
        
        # 저장할 항목 구성
        entry = {
            "작성일시": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "매체/기자": input_data.get("media", ""),
            "문의내용": input_data.get("issue_content", ""),
            "외부기사URL": input_data.get("external_news_url", ""),
            "대응결과": input_data.get("response", ""),
            "위기단계": analysis_result.get("crisis_level", "") if analysis_result else "",
            "담당부서": analysis_result.get("department", "") if analysis_result else "",
            "생성보고서": report_text.replace('\n', '\\n')  # 줄바꿈 처리
        }

        try:
            # 기존 파일이 있으면 불러오기, 없으면 새로 만들기
            if self.history_path.exists():
                df = pd.read_csv(self.history_path, encoding="utf-8-sig")
                df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
            else:
                df = pd.DataFrame([entry])

            # 파일로 저장
            df.to_csv(self.history_path, index=False, encoding="utf-8-sig")
            return True
            
        except Exception as e:
            print(f"❌ 히스토리 저장 실패: {e}")
            return False
    
    def load_history(self) -> pd.DataFrame:
        """저장된 히스토리 데이터 로드"""
        try:
            if self.history_path.exists():
                df = pd.read_csv(self.history_path, encoding="utf-8-sig")
                # 줄바꿈 복원
                if "생성보고서" in df.columns:
                    df["생성보고서"] = df["생성보고서"].str.replace('\\n', '\n', regex=False)
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            print(f"❌ 히스토리 로드 실패: {e}")
            return pd.DataFrame()
    
    def get_statistics(self) -> dict:
        """히스토리 통계 정보 반환"""
        df = self.load_history()
        
        if df.empty:
            return {
                "total_reports": 0,
                "today_reports": 0,
                "most_common_media": "N/A",
                "most_common_crisis_level": "N/A"
            }
        
        today = datetime.now().strftime('%Y-%m-%d')
        today_reports = len(df[df['작성일시'].str.startswith(today)])
        
        return {
            "total_reports": len(df),
            "today_reports": today_reports,
            "most_common_media": df['매체/기자'].mode().iloc[0] if not df['매체/기자'].mode().empty else "N/A",
            "most_common_crisis_level": df['위기단계'].mode().iloc[0] if not df['위기단계'].mode().empty else "N/A"
        }
    
    def search_history(self, keyword: str) -> pd.DataFrame:
        """키워드로 히스토리 검색"""
        df = self.load_history()
        
        if df.empty or not keyword:
            return df
        
        # 여러 컬럼에서 키워드 검색
        mask = (
            df['매체/기자'].str.contains(keyword, case=False, na=False) |
            df['문의내용'].str.contains(keyword, case=False, na=False) |
            df['대응결과'].str.contains(keyword, case=False, na=False)
        )
        
        return df[mask]

# 하위 호환성을 위한 함수 (기존 코드와의 호환)
def save_history(data: dict, report_text: str):
    """
    기존 코드와의 하위 호환성을 위한 함수
    """
    logger = HistoryLogger()
    return logger.save_history(data, report_text)
