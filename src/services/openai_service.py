from openai import OpenAI
from typing import Optional
from config.settings import settings
from src.utils.logger import Logger

class OpenAIService:
    """OpenAI API 서비스 관리"""
    
    def __init__(self):
        self.logger = Logger.get_logger(__name__)
        self.client = self._setup_client()
    
    def _setup_client(self) -> OpenAI:
        """OpenAI 클라이언트 설정"""
        settings.validate_settings()
        self.logger.info("OpenAI 클라이언트 초기화 완료")
        return OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def ask_gpt(
        self, 
        message: str, 
        model: Optional[str] = None, 
        temperature: Optional[float] = None
    ) -> str:
        """GPT에게 질문하고 응답 받기"""
        if model is None:
            model = settings.DEFAULT_MODEL
        if temperature is None:
            temperature = settings.DEFAULT_TEMPERATURE
            
        try:
            self.logger.info(f"GPT 호출 시작 - 모델: {model}, 온도: {temperature}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": settings.SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ],
                temperature=temperature,
            )
            
            content = response.choices[0].message.content
            result = content if content is not None else "응답을 받지 못했습니다."
            
            self.logger.info("GPT 응답 성공")
            return result
            
        except Exception as e:
            error_msg = f"GPT 호출 중 오류 발생: {str(e)}"
            self.logger.error(error_msg)
            return error_msg