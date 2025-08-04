import numpy as np
import pandas as pd
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from config.settings import settings
from src.utils.logger import Logger

class EmbeddingService:
    """임베딩 생성 및 FAISS 인덱스 관리 서비스"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.model = self._load_model()
    
    def _load_model(self) -> SentenceTransformer:
        """SentenceTransformer 모델 로드"""
        try:
            model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            self.logger.info(f"임베딩 모델 로드 완료: {settings.EMBEDDING_MODEL_NAME}")
            return model
        except Exception as e:
            error_msg = f"모델 로딩 실패: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """텍스트 리스트를 임베딩으로 변환"""
        if not texts:
            raise ValueError("텍스트 리스트가 비어있습니다.")
        
        self.logger.info(f"임베딩 생성 시작: {len(texts)}개 텍스트")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        self.logger.info("임베딩 생성 완료")
        return embeddings
    
    def build_faiss_index(self, embeddings: np.ndarray) -> faiss.Index:
        """FAISS 인덱스 생성"""
        if embeddings.size == 0:
            raise ValueError("임베딩이 비어있습니다.")
        
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        
        self.logger.info(f"FAISS 인덱스 생성 완료: {embeddings.shape[0]}개 벡터, {dimension}차원")
        return index
    
    def save_index(self, index: faiss.Index, mapping: List[dict]):
        """인덱스와 매핑 데이터 저장"""
        try:
            settings.INDEX_DIR.mkdir(parents=True, exist_ok=True)
            
            faiss.write_index(index, str(settings.FAISS_INDEX_PATH))
            
            with open(settings.INDEX_MAPPING_PATH, "wb") as f:
                pickle.dump(mapping, f)
            
            self.logger.info(f"인덱스 저장 완료: {settings.FAISS_INDEX_PATH}")
            
        except Exception as e:
            error_msg = f"인덱스 저장 실패: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def load_index(self) -> tuple[faiss.Index, List[dict]]:
        """저장된 인덱스와 매핑 데이터 로드"""
        try:
            index = faiss.read_index(str(settings.FAISS_INDEX_PATH))
            
            with open(settings.INDEX_MAPPING_PATH, "rb") as f:
                mapping = pickle.load(f)
            
            self.logger.info("인덱스 로드 완료")
            return index, mapping
            
        except FileNotFoundError:
            error_msg = "인덱스 파일이 없습니다. 먼저 인덱스를 생성해주세요."
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        except Exception as e:
            error_msg = f"인덱스 로드 실패: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def build_index_from_dataframe(self, df: pd.DataFrame) -> tuple[faiss.Index, List[dict]]:
        """DataFrame에서 인덱스 생성"""
        texts = df["이슈 발생 보고"].tolist()
        
        if not texts:
            raise ValueError("처리할 데이터가 없습니다.")
        
        # 임베딩 생성
        embeddings = self.create_embeddings(texts)
        
        # FAISS 인덱스 구축
        index = self.build_faiss_index(embeddings)
        
        # 매핑 데이터 생성
        mapping = df[["순번", "발생 일시", "이슈 발생 보고"]].to_dict(orient="records")
        
        # 저장
        self.save_index(index, mapping)
        
        return index, mapping