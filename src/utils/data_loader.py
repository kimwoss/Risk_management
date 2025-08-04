import pandas as pd
from pathlib import Path
from typing import Optional
from config.settings import settings

class DataLoader:
    """CSV 데이터 로딩 및 처리 유틸리티"""
    
    @staticmethod
    def load_csv(file_path: Optional[str] = None) -> pd.DataFrame:
        """CSV 파일 로드하고 '기자문의' 관련 데이터만 필터링"""
        if file_path is None:
            file_path = settings.CSV_FILE_PATH
        
        file_path = Path(file_path)
        
        # 파일 존재 여부 확인
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        try:
            # 한글 파일이므로 cp949 인코딩 시도
            df = pd.read_csv(file_path, encoding=settings.PRIMARY_ENCODING, header=1)
        except UnicodeDecodeError:
            try:
                # cp949로 안되면 utf-8-sig 시도
                df = pd.read_csv(file_path, encoding=settings.FALLBACK_ENCODING, header=1)
            except UnicodeDecodeError as e:
                raise ValueError(f"파일 인코딩 오류: {e}")
            except pd.errors.EmptyDataError as e:
                raise ValueError(f"빈 파일이거나 데이터가 없습니다: {e}")
            except pd.errors.ParserError as e:
                raise ValueError(f"CSV 파싱 오류: {e}")
        
        # 필수 컬럼 확인
        missing_columns = [col for col in settings.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise ValueError(f"필수 컬럼이 없습니다: {missing_columns}")
        
        return DataLoader._filter_query_data(df)
    
    @staticmethod
    def _filter_query_data(df: pd.DataFrame) -> pd.DataFrame:
        """기자문의 데이터 필터링"""
        # '기자문의' 또는 '기자 문의' 모두 포함
        query_df = df[df["발생 유형"].isin(settings.QUERY_TYPES)].copy()
        
        # 결측값 제거
        query_df = query_df.dropna(subset=["이슈 발생 보고"]).reset_index(drop=True)
        
        if query_df.empty:
            print("⚠️ 기자문의 관련 데이터가 없습니다.")
        
        return query_df
    
    @staticmethod
    def preview_entries(df: pd.DataFrame, n: Optional[int] = None):
        """상위 n개 데이터 출력"""
        if n is None:
            n = settings.DEFAULT_PREVIEW_COUNT
            
        if df.empty:
            print("⚠️ 표시할 데이터가 없습니다.")
            return
        
        print(f"\n📌 '기자문의' 관련 상위 {min(n, len(df))}건의 내용:\n")
        available_columns = [col for col in settings.DISPLAY_COLUMNS if col in df.columns]
        print(df[available_columns].head(n))