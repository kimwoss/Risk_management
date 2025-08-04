import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # 프로젝트 경로 설정
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    
    # 인덱스 저장 경로
    INDEX_DIR = BASE_DIR / "data" / "index"
    FAISS_INDEX_PATH = INDEX_DIR / "faiss_index.bin"
    INDEX_MAPPING_PATH = INDEX_DIR / "index_mapping.pkl"
    
    # 데이터 파일 경로
    CSV_FILENAME = "최신 언론대응내역(GPT용).csv"
    CSV_FILE_PATH = DATA_DIR / CSV_FILENAME
    
    # OpenAI 설정
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEFAULT_MODEL = "gpt-3.5-turbo"
    DEFAULT_TEMPERATURE = 0.7
    
    # 임베딩 모델 설정
    EMBEDDING_MODEL_NAME = "jhgan/ko-sroberta-multitask"
    
    # 데이터 처리 설정
    REQUIRED_COLUMNS = ["발생 유형", "이슈 발생 보고"]
    QUERY_TYPES = ["기자문의", "기자 문의"]
    DISPLAY_COLUMNS = ["순번", "발생 일시", "발생 유형", "이슈 발생 보고"]
    
    # 검색 설정
    DEFAULT_TOP_K = 3
    DEFAULT_SEARCH_COUNT = 10
    DEFAULT_PREVIEW_COUNT = 10
    
    # 시스템 프롬프트
    SYSTEM_PROMPT = "너는 위기 대응 전문 전략가입니다. 이슈 맥락을 빠르게 파악해서 전문적인 조언을 제공해주세요."
    
    # 위기 단계 정의 (4단계 체계)
    CRISIS_STAGES = {
        '관심': {
            'level': 1,
            'description': '잠재적 이슈 모니터링 단계',
            'color': 'blue'
        },
        '주의': {
            'level': 2, 
            'description': '이슈 발생 및 초기 대응 단계',
            'color': 'yellow'
        },
        '위기': {
            'level': 3,
            'description': '심각한 이슈로 확산된 위기 대응 단계', 
            'color': 'orange'
        },
        '비상': {
            'level': 4,
            'description': '최고 수준의 비상 대응 단계',
            'color': 'red'
        }
    }
    
    # 파일 인코딩 설정
    PRIMARY_ENCODING = "cp949"
    FALLBACK_ENCODING = "utf-8-sig"
    
    # 날짜 형식 설정
    DATE_FORMATS = ["%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"]
    
    @classmethod
    def validate_settings(cls):
        """설정 검증"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        
        # 필요한 디렉토리 생성
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)
        cls.INDEX_DIR.mkdir(exist_ok=True)
        
        return True

settings = Settings()