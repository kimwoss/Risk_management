import logging
import sys
from pathlib import Path
from datetime import datetime
from config.settings import settings

class Logger:
    """로깅 설정 및 관리"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str = "risk_management") -> logging.Logger:
        """로거 인스턴스 반환"""
        if name not in cls._loggers:
            cls._loggers[name] = cls._setup_logger(name)
        return cls._loggers[name]
    
    @classmethod
    def _setup_logger(cls, name: str) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        
        # 핸들러가 이미 있으면 제거
        if logger.handlers:
            logger.handlers.clear()
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 파일 핸들러
        log_file = settings.LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger