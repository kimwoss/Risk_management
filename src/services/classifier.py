import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder
import joblib
from pathlib import Path
import re

from config.settings import settings
from src.utils.robust_data_loader import RobustDataLoader
from src.utils.logger import Logger

class CrisisStageClassifier:
    """위기 단계 분류기 (관심 → 주의 → 위기 → 비상)"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.data_loader = RobustDataLoader()
        
        # 모델 및 전처리기
        self.vectorizer = None
        self.label_encoder = None
        self.model = None
        self.model_type = 'naive_bayes'  # 기본 모델
        
        # 모델 저장 경로
        self.model_dir = settings.BASE_DIR / "models"
        self.model_dir.mkdir(exist_ok=True)
        
        # 위기 단계 표준화 매핑 (관심 → 주의 → 위기 → 비상)
        self.stage_mapping = {
            # 한국어 표준
            '관심': '관심',
            '주의': '주의', 
            '위기': '위기',
            '비상': '비상',
            
            # 단계가 포함된 표현
            '관심단계': '관심',
            '주의단계': '주의',
            '위기단계': '위기', 
            '비상단계': '비상',
            
            # 기존 용어들 (매핑)
            '경계': '위기',          # 경계 → 위기
            '심각': '비상',          # 심각 → 비상
            '경계단계': '위기',
            '심각단계': '비상',
            
            # 영어 표현
            'attention': '관심',
            'caution': '주의',
            'alert': '위기',
            'crisis': '위기',
            'emergency': '비상',
            'serious': '비상',
            'critical': '비상',
            
            # 기타 가능한 표현
            '1단계': '관심',
            '2단계': '주의',
            '3단계': '위기',
            '4단계': '비상',
            'level1': '관심',
            'level2': '주의', 
            'level3': '위기',
            'level4': '비상'
        }
        
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # 기본 정리
        text = str(text).strip()
        
        # 특수 문자 정리 (한글, 영문, 숫자, 공백만 유지)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def standardize_stage(self, stage: str) -> str:
        """위기 단계 표준화"""
        if pd.isna(stage):
            return ""
        
        stage_clean = str(stage).strip().lower()
        
        # 매핑 적용
        for key, value in self.stage_mapping.items():
            if key.lower() in stage_clean:
                return value
        
        # 매핑되지 않은 경우 원본 반환 (첫 글자 대문자)
        return str(stage).strip().title()
    
    def load_and_prepare_data(self, file_path: Optional[str] = None) -> Tuple[pd.DataFrame, Dict]:
        """데이터 로드 및 전처리"""
        self.logger.info("위기단계 학습 데이터 로드 시작")
        
        # 데이터 로드
        df = self.data_loader.load_crisis_training_data(file_path)
        
        # 데이터 정보 출력
        info = self.data_loader.get_column_info(df)
        self.logger.info(f"로드된 데이터 정보: {info}")
        
        # 필수 열 확인
        if 'content' not in df.columns or 'stage' not in df.columns:
            available_cols = df.columns.tolist()
            raise ValueError(f"필수 열(content, stage)이 없습니다. 사용 가능한 열: {available_cols}")
        
        # 텍스트 전처리
        df['content_clean'] = df['content'].apply(self.preprocess_text)
        
        # 위기 단계 표준화  
        df['stage_clean'] = df['stage'].apply(self.standardize_stage)
        
        # 빈 데이터 제거
        df = df[
            (df['content_clean'].str.len() > 0) & 
            (df['stage_clean'].str.len() > 0)
        ].reset_index(drop=True)
        
        stage_distribution = df['stage_clean'].value_counts().to_dict()
        self.logger.info(f"전처리 완료: {len(df)}행")
        self.logger.info(f"위기 단계 분포: {stage_distribution}")
        
        # 4단계 체계 확인
        expected_stages = ['관심', '주의', '위기', '비상']
        found_stages = list(stage_distribution.keys())
        self.logger.info(f"발견된 단계: {found_stages}")
        self.logger.info(f"표준 4단계: {expected_stages}")
        
        return df, info
    
    def train_model(self, df: pd.DataFrame, model_type: str = 'naive_bayes', test_size: float = 0.2) -> Dict:
        """모델 학습"""
        self.logger.info(f"모델 학습 시작: {model_type}")
        self.model_type = model_type
        
        # 데이터 분할
        X = df['content_clean']
        y = df['stage_clean']
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # 텍스트 벡터화
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            stop_words=None  # 한국어는 별도 불용어 사전 필요
        )
        
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # 레이블 인코딩
        self.label_encoder = LabelEncoder()
        y_train_encoded = self.label_encoder.fit_transform(y_train)
        y_test_encoded = self.label_encoder.transform(y_test)
        
        # 모델 선택 및 학습
        if model_type == 'naive_bayes':
            self.model = MultinomialNB(alpha=1.0)
        elif model_type == 'svm':
            self.model = SVC(kernel='linear', probability=True, random_state=42)
        elif model_type == 'random_forest':
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"지원하지 않는 모델 타입: {model_type}")
        
        self.model.fit(X_train_vec, y_train_encoded)
        
        # 예측 및 평가
        y_pred = self.model.predict(X_test_vec)
        y_pred_labels = self.label_encoder.inverse_transform(y_pred)
        
        # 평가 결과
        accuracy = accuracy_score(y_test, y_pred_labels)
        report = classification_report(y_test, y_pred_labels, output_dict=True)
        
        results = {
            'model_type': model_type,
            'accuracy': accuracy,
            'classification_report': report,
            'train_size': len(X_train),
            'test_size': len(X_test),
            'classes': self.label_encoder.classes_.tolist()
        }
        
        self.logger.info(f"모델 학습 완료 - 정확도: {accuracy:.3f}")
        
        return results
    
    def predict(self, text: str) -> Dict:
        """단일 텍스트 예측"""
        if not self.model or not self.vectorizer or not self.label_encoder:
            raise ValueError("모델이 학습되지 않았습니다. train_model()을 먼저 실행하세요.")
        
        # 전처리
        text_clean = self.preprocess_text(text)
        
        if not text_clean:
            return {'stage': 'unknown', 'confidence': 0.0, 'probabilities': {}}
        
        # 벡터화
        text_vec = self.vectorizer.transform([text_clean])
        
        # 예측
        pred_encoded = self.model.predict(text_vec)[0]
        pred_stage = self.label_encoder.inverse_transform([pred_encoded])[0]
        
        # 확률 계산
        if hasattr(self.model, 'predict_proba'):
            probas = self.model.predict_proba(text_vec)[0]
            confidence = max(probas)
            
            # 각 클래스별 확률
            prob_dict = {}
            for i, prob in enumerate(probas):
                class_name = self.label_encoder.inverse_transform([i])[0]
                prob_dict[class_name] = float(prob)
        else:
            confidence = 1.0  # SVM 등에서 확률 미지원시
            prob_dict = {pred_stage: 1.0}
        
        # 단계 레벨 정보 추가
        stage_info = self._get_stage_info(pred_stage)
        
        return {
            'stage': pred_stage,
            'confidence': float(confidence),
            'probabilities': prob_dict,
            'stage_info': stage_info
        }
    
    def _get_stage_info(self, stage: str) -> Dict:
        """위기 단계 정보 반환"""
        from config.settings import settings
        
        if hasattr(settings, 'CRISIS_STAGES') and stage in settings.CRISIS_STAGES:
            return settings.CRISIS_STAGES[stage]
        
        # 기본 정보
        stage_levels = {
            '관심': {'level': 1, 'description': '잠재적 이슈 모니터링 단계', 'color': 'blue'},
            '주의': {'level': 2, 'description': '이슈 발생 및 초기 대응 단계', 'color': 'yellow'},
            '위기': {'level': 3, 'description': '심각한 이슈로 확산된 위기 대응 단계', 'color': 'orange'},
            '비상': {'level': 4, 'description': '최고 수준의 비상 대응 단계', 'color': 'red'}
        }
        
        return stage_levels.get(stage, {'level': 0, 'description': '알 수 없는 단계', 'color': 'gray'})
    
    def predict_batch(self, texts: List[str]) -> List[Dict]:
        """배치 예측"""
        return [self.predict(text) for text in texts]
    
    def save_model(self, model_name: str = "crisis_classifier"):
        """모델 저장"""
        if not self.model:
            raise ValueError("저장할 모델이 없습니다.")
        
        model_path = self.model_dir / f"{model_name}.joblib"
        vectorizer_path = self.model_dir / f"{model_name}_vectorizer.joblib"
        encoder_path = self.model_dir / f"{model_name}_encoder.joblib"
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.vectorizer, vectorizer_path)
        joblib.dump(self.label_encoder, encoder_path)
        
        # 메타데이터 저장
        metadata = {
            'model_type': self.model_type,
            'classes': self.label_encoder.classes_.tolist() if self.label_encoder else [],
            'feature_count': len(self.vectorizer.get_feature_names_out()) if self.vectorizer else 0
        }
        
        import json
        metadata_path = self.model_dir / f"{model_name}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"모델 저장 완료: {model_path}")
    
    def load_model(self, model_name: str = "crisis_classifier"):
        """모델 로드"""
        model_path = self.model_dir / f"{model_name}.joblib"
        vectorizer_path = self.model_dir / f"{model_name}_vectorizer.joblib"
        encoder_path = self.model_dir / f"{model_name}_encoder.joblib"
        
        if not all(p.exists() for p in [model_path, vectorizer_path, encoder_path]):
            raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_name}")
        
        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)
        self.label_encoder = joblib.load(encoder_path)
        
        self.logger.info(f"모델 로드 완료: {model_name}")
    
    def evaluate_model(self, df: pd.DataFrame, sample_size: int = 100) -> Dict:
        """모델 평가"""
        if not self.model:
            raise ValueError("평가할 모델이 없습니다.")
        
        # 샘플 데이터로 평가
        if len(df) > sample_size:
            df_sample = df.sample(n=sample_size, random_state=42)
        else:
            df_sample = df
        
        predictions = []
        true_labels = []
        
        for idx, row in df_sample.iterrows():
            pred = self.predict(row['content_clean'])
            predictions.append(pred['stage'])
            true_labels.append(row['stage_clean'])
        
        accuracy = accuracy_score(true_labels, predictions)
        report = classification_report(true_labels, predictions, output_dict=True)
        
        return {
            'accuracy': accuracy,
            'classification_report': report,
            'sample_size': len(df_sample),
            'predictions_sample': list(zip(true_labels[:5], predictions[:5]))
        }