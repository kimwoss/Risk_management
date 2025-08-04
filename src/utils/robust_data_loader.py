import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import re
from config.settings import settings
from src.utils.logger import Logger

class RobustDataLoader:
    """강력한 CSV 데이터 로딩 클래스 - 인코딩 및 열 이름 문제 자동 해결"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        
        # 가능한 인코딩 목록 (우선순위)
        self.encodings = ['utf-8-sig', 'cp949', 'euc-kr', 'utf-8', 'latin-1']
        
        # 열 이름 매핑 (다양한 표현을 표준화)
        self.column_mapping = {
            # 이슈 내용 관련
            '이슈 발생 보고': 'content',
            '이슈발생보고': 'content',
            '발생보고': 'content',
            '내용': 'content',
            '보고내용': 'content',
            '이슈내용': 'content',
            '이슈 내용': 'content',
            
            # 위기 단계 관련
            '단계': 'stage',
            '위기단계': 'stage',
            '위기 단계': 'stage',
            '대응단계': 'stage',
            '대응 단계': 'stage',
            '레벨': 'stage',
            'level': 'stage',
            'stage': 'stage',
            
            # 기타 가능한 컬럼들
            '순번': 'id',
            'id': 'id',
            '번호': 'id',
            '발생일시': 'date',
            '발생 일시': 'date',
            '날짜': 'date',
            'date': 'date'
        }
    
    def detect_encoding(self, file_path: Path) -> str:
        """파일의 인코딩을 자동 감지"""
        for encoding in self.encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1000)  # 처음 1000자 읽어보기
                self.logger.info(f"인코딩 감지 성공: {encoding}")
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        self.logger.warning("모든 인코딩 실패, utf-8로 강제 설정")
        return 'utf-8'
    
    def find_header_row(self, file_path: Path, encoding: str) -> int:
        """헤더가 있는 행을 자동으로 찾기"""
        try:
            # 처음 10줄 읽어서 헤더 위치 찾기
            with open(file_path, 'r', encoding=encoding) as f:
                lines = [f.readline().strip() for _ in range(10)]
            
            for i, line in enumerate(lines):
                # BOM 제거
                line = line.lstrip('\ufeff').strip()
                
                # 빈 줄이 아니고, 쉼표가 있고, 숫자로만 구성되지 않은 경우
                if line and ',' in line and not line.replace(',', '').replace(' ', '').isdigit():
                    # 한글이나 영문이 포함된 경우 (헤더일 가능성)
                    if re.search(r'[가-힣a-zA-Z]', line):
                        self.logger.info(f"헤더 행 발견: {i}번째 줄")
                        return i
            
            self.logger.warning("헤더 행을 찾지 못했습니다. 0번째 줄을 헤더로 가정합니다.")
            return 0
            
        except Exception as e:
            self.logger.error(f"헤더 행 찾기 실패: {e}")
            return 0
    
    def clean_column_names(self, columns: List[str]) -> List[str]:
        """열 이름 정리 및 표준화"""
        cleaned = []
        for col in columns:
            # BOM, 공백, 특수문자 제거
            col = str(col).strip().lstrip('\ufeff').strip()
            
            # 빈 열 이름 처리
            if not col or col == 'nan' or pd.isna(col):
                col = f'unnamed_column_{len(cleaned)}'
            
            cleaned.append(col)
        
        return cleaned
    
    def map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """열 이름을 표준 이름으로 매핑"""
        df_mapped = df.copy()
        current_columns = df_mapped.columns.tolist()
        
        # 매핑 적용
        rename_dict = {}
        for col in current_columns:
            col_clean = str(col).strip().lstrip('\ufeff')
            if col_clean in self.column_mapping:
                rename_dict[col] = self.column_mapping[col_clean]
        
        if rename_dict:
            df_mapped = df_mapped.rename(columns=rename_dict)
            self.logger.info(f"열 이름 매핑 완료: {rename_dict}")
        
        return df_mapped
    
    def load_crisis_training_data(self, file_path: Optional[str] = None) -> pd.DataFrame:
        """위기단계 학습 데이터 로드"""
        if file_path is None:
            file_path = settings.DATA_DIR / "위기단계_학습셋.csv"
        
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        self.logger.info(f"위기단계 데이터 로드 시작: {file_path}")
        
        # 1. 인코딩 감지
        encoding = self.detect_encoding(file_path)
        
        # 2. 헤더 행 찾기
        header_row = self.find_header_row(file_path, encoding)
        
        # 3. DataFrame 로드
        try:
            df = pd.read_csv(
                file_path, 
                encoding=encoding, 
                header=header_row,
                skip_blank_lines=True
            )
            
            self.logger.info(f"원본 데이터 로드 완료: {df.shape}")
            
        except Exception as e:
            self.logger.error(f"DataFrame 로드 실패: {e}")
            # 다른 방법으로 시도
            try:
                df = pd.read_csv(file_path, encoding=encoding, header=None)
                # 첫 번째 행을 헤더로 사용
                df.columns = df.iloc[0]
                df = df.drop(df.index[0]).reset_index(drop=True)
                self.logger.info("헤더 없는 방식으로 로드 성공")
            except Exception as e2:
                raise RuntimeError(f"모든 로드 방법 실패: {e2}")
        
        # 4. 열 이름 정리
        df.columns = self.clean_column_names(df.columns.tolist())
        
        # 5. 열 이름 매핑
        df = self.map_columns(df)
        
        # 6. 데이터 정리
        df = self.clean_data(df)
        
        self.logger.info(f"최종 데이터: {df.shape}, 열: {df.columns.tolist()}")
        return df
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터 정리"""
        df_clean = df.copy()
        
        # 빈 행 제거
        df_clean = df_clean.dropna(how='all')
        
        # content와 stage 열이 있는지 확인
        required_cols = ['content', 'stage']
        missing_cols = [col for col in required_cols if col not in df_clean.columns]
        
        if missing_cols:
            self.logger.warning(f"필수 열이 없습니다: {missing_cols}")
            self.logger.info(f"사용 가능한 열: {df_clean.columns.tolist()}")
            
            # 대안 열 찾기
            if 'content' not in df_clean.columns:
                content_candidates = [col for col in df_clean.columns 
                                    if any(word in str(col).lower() for word in ['내용', '보고', '이슈', 'content'])]
                if content_candidates:
                    df_clean = df_clean.rename(columns={content_candidates[0]: 'content'})
                    self.logger.info(f"내용 열을 {content_candidates[0]}로 매핑")
            
            if 'stage' not in df_clean.columns:
                stage_candidates = [col for col in df_clean.columns 
                                  if any(word in str(col).lower() for word in ['단계', '레벨', 'stage', 'level'])]
                if stage_candidates:
                    df_clean = df_clean.rename(columns={stage_candidates[0]: 'stage'})
                    self.logger.info(f"단계 열을 {stage_candidates[0]}로 매핑")
        
        # 필수 열의 결측값 제거
        if 'content' in df_clean.columns and 'stage' in df_clean.columns:
            df_clean = df_clean.dropna(subset=['content', 'stage'])
            
            # 빈 문자열 제거
            df_clean = df_clean[
                (df_clean['content'].str.strip() != '') & 
                (df_clean['stage'].str.strip() != '')
            ]
        
        df_clean = df_clean.reset_index(drop=True)
        
        self.logger.info(f"데이터 정리 완료: {len(df_clean)}행")
        return df_clean
    
    def get_column_info(self, df: pd.DataFrame) -> Dict:
        """데이터프레임 정보 반환"""
        info = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'dtypes': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'sample_data': df.head(3).to_dict() if len(df) > 0 else {}
        }
        
        if 'stage' in df.columns:
            info['stage_distribution'] = df['stage'].value_counts().to_dict()
        
        return info