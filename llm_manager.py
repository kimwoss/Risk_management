"""
OpenAI API를 사용하는 LLM 클래스
"""
import os
from typing import List, Dict, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv

class LLMManager:
    """OpenAI API를 사용하는 LLM 관리 클래스"""
    
    def __init__(self, model: str = "gpt-4", data_folder: str = "data"):
        """
        LLM 매니저 초기화
        
        Args:
            model (str): 사용할 OpenAI 모델명 (기본: gpt-3.5-turbo)
            data_folder (str): 데이터 폴더 경로
        """
        load_dotenv()
        
        # OpenAI API 키 가져오기
        api_key = os.getenv('OPEN_API_KEY')
        if not api_key:
            raise ValueError("OPEN_API_KEY가 .env 파일에 설정되지 않았습니다.")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.data_folder = data_folder
        self.conversation_history: List[Dict[str, str]] = []
        
        # 총괄 프롬프트 로드
        self.master_prompt = self._load_master_prompt()
        
    def _load_master_prompt(self) -> str:
        """총괄 프롬프트 로드 (risk_report.txt)"""
        try:
            prompt_path = os.path.join(self.data_folder, "risk_report.txt")
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                return "포스코인터내셔널의 리스크 관리 및 언론대응 전문가로서 도움을 드리겠습니다."
        except Exception as e:
            print(f"총괄 프롬프트 로드 중 오류: {str(e)}")
            return "포스코인터내셔널의 리스크 관리 및 언론대응 전문가로서 도움을 드리겠습니다."
        
    def chat(self, message: str, system_prompt: Optional[str] = None, 
             temperature: float = 0.7, max_tokens: Optional[int] = None,
             template_vars: Optional[Dict[str, str]] = None) -> str:
        """
        단일 메시지로 채팅
        
        Args:
            message (str): 사용자 메시지
            system_prompt (str, optional): 시스템 프롬프트 (None이면 총괄 프롬프트 사용)
            temperature (float): 응답의 창의성 (0.0-2.0)
            max_tokens (int, optional): 최대 토큰 수
            template_vars (Dict[str, str], optional): 템플릿 변수 치환용 딕셔너리
            
        Returns:
            str: AI 응답
        """
        messages = []
        
        # 시스템 프롬프트가 없으면 총괄 프롬프트 사용
        if system_prompt is None:
            system_prompt = self.master_prompt
            
        # 템플릿 변수 치환
        if system_prompt and template_vars:
            system_prompt = self._substitute_template_vars(system_prompt, template_vars)
            
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg:
                return """
❌ OpenAI API 할당량 초과

현재 OpenAI API 크레딧이 부족합니다. 다음 방법을 시도해주세요:

1. 📊 **사용량 확인**: https://platform.openai.com/account/billing
2. 💳 **크레딧 추가**: OpenAI 계정에서 결제 정보 확인 및 크레딧 구매
3. 🔄 **나중에 재시도**: 월간 한도 리셋 대기

🆘 **즉시 도움이 필요한 경우**:
- 포스코인터내셔널 IT 지원팀에 문의
- 시스템 관리자에게 API 키 상태 확인 요청

임시로 기본 대응 가이드를 참조하시거나, 수동으로 이슈 발생 보고서를 작성해주세요.
                """.strip()
            elif "rate_limit" in error_msg:
                return "⏳ API 요청 한도 초과. 잠시 후 다시 시도해주세요."
            else:
                return f"❌ 시스템 오류가 발생했습니다: {error_msg}"
    
    def _substitute_template_vars(self, template: str, variables: Dict[str, str]) -> str:
        """
        템플릿 변수를 실제 값으로 치환
        
        Args:
            template (str): 변수가 포함된 템플릿 문자열
            variables (Dict[str, str]): 치환할 변수들
            
        Returns:
            str: 변수가 치환된 문자열
        """
        result = template
        for var_name, var_value in variables.items():
            # {{VAR_NAME}} 형태의 변수를 치환
            placeholder = f"{{{{{var_name}}}}}"
            result = result.replace(placeholder, var_value)
        return result
    
    def conversation_chat(self, message: str, system_prompt: Optional[str] = None,
                         temperature: float = 0.7, max_tokens: Optional[int] = None) -> str:
        """
        대화 기록을 유지하는 채팅
        
        Args:
            message (str): 사용자 메시지
            system_prompt (str, optional): 시스템 프롬프트 (첫 번째 메시지에만 적용, None이면 총괄 프롬프트 사용)
            temperature (float): 응답의 창의성 (0.0-2.0)
            max_tokens (int, optional): 최대 토큰 수
            
        Returns:
            str: AI 응답
        """
        # 첫 번째 메시지이고 시스템 프롬프트 처리
        if not self.conversation_history:
            if system_prompt is None:
                system_prompt = self.master_prompt
            if system_prompt:
                self.conversation_history.append({"role": "system", "content": system_prompt})
        
        # 사용자 메시지 추가
        self.conversation_history.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            ai_response = response.choices[0].message.content
            
            # AI 응답을 대화 기록에 추가
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response
        except Exception as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg:
                error_response = """
❌ OpenAI API 할당량 초과

현재 OpenAI API 크레딧이 부족합니다. 시스템 관리자에게 문의하거나 잠시 후 다시 시도해주세요.
                """.strip()
            elif "rate_limit" in error_msg:
                error_response = "⏳ API 요청 한도 초과. 잠시 후 다시 시도해주세요."
            else:
                error_response = f"❌ 시스템 오류: {error_msg}"
            
            # 에러 응답도 대화 기록에 추가
            self.conversation_history.append({"role": "assistant", "content": error_response})
            return error_response
    
    def clear_conversation(self):
        """대화 기록 초기화"""
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """대화 기록 반환"""
        return self.conversation_history.copy()
    
    def set_model(self, model: str):
        """사용할 모델 변경"""
        self.model = model
    
    def get_available_models(self) -> List[str]:
        """사용 가능한 모델 목록 반환"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data if 'gpt' in model.id]
        except Exception as e:
            print(f"모델 목록을 가져오는 중 오류 발생: {str(e)}")
            return ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
    
    def analyze_text(self, text: str, analysis_type: str = "sentiment") -> str:
        """
        텍스트 분석 (감정 분석, 요약 등)
        
        Args:
            text (str): 분석할 텍스트
            analysis_type (str): 분석 유형 ("sentiment", "summary", "keywords")
            
        Returns:
            str: 분석 결과
        """
        prompts = {
            "sentiment": f"다음 텍스트의 감정을 분석해주세요. 긍정적, 부정적, 중립적 중 하나로 분류하고 이유를 설명해주세요:\n\n{text}",
            "summary": f"다음 텍스트를 간결하게 요약해주세요:\n\n{text}",
            "keywords": f"다음 텍스트에서 주요 키워드들을 추출해주세요:\n\n{text}"
        }
        
        prompt = prompts.get(analysis_type, f"다음 텍스트를 분석해주세요:\n\n{text}")
        return self.chat(prompt)
    
    def translate_text(self, text: str, target_language: str = "English") -> str:
        """
        텍스트 번역
        
        Args:
            text (str): 번역할 텍스트
            target_language (str): 목표 언어
            
        Returns:
            str: 번역된 텍스트
        """
        prompt = f"다음 텍스트를 {target_language}로 번역해주세요:\n\n{text}"
        return self.chat(prompt)
    
    def generate_code(self, description: str, language: str = "Python") -> str:
        """
        코드 생성
        
        Args:
            description (str): 코드 설명
            language (str): 프로그래밍 언어
            
        Returns:
            str: 생성된 코드
        """
        prompt = f"{language}로 다음 기능을 구현하는 코드를 작성해주세요:\n\n{description}"
        return self.chat(prompt, system_prompt=f"당신은 {language} 프로그래밍 전문가입니다.")
    
    def analyze_credit_risk(self, company_info: str) -> str:
        """신용 리스크 분석"""
        prompt = f"""
        다음 회사 정보를 바탕으로 신용 리스크를 분석해주세요:
        
        회사 정보: {company_info}
        
        다음 항목들을 포함하여 분석해주세요:
        1. 재무 건전성 평가
        2. 시장 위험 요소
        3. 운영 리스크
        4. 유동성 위험
        5. 종합 리스크 등급 (AAA ~ D)
        6. 위험 완화 방안
        """
        
        return self.chat(prompt)
    
    def calculate_var_explanation(self, portfolio_data: str, confidence_level: str = "95%") -> str:
        """VaR 계산 방법론 설명"""
        prompt = f"""
        다음 포트폴리오에 대해 VaR({confidence_level}) 계산 방법을 설명해주세요:
        
        포트폴리오 정보: {portfolio_data}
        
        다음 내용을 포함해주세요:
        1. 적합한 VaR 모델 선택 (Historical Simulation, Parametric, Monte Carlo)
        2. 계산 단계별 설명
        3. 필요한 데이터 및 가정사항
        4. 백테스팅 방법
        5. 한계점 및 주의사항
        """
        
        return self.chat(prompt)
    
    def stress_test_scenario(self, scenario_description: str) -> str:
        """스트레스 테스트 시나리오 분석"""
        prompt = f"""
        다음 스트레스 시나리오에 대한 분석을 제공해주세요:
        
        시나리오: {scenario_description}
        
        분석 내용:
        1. 시나리오의 현실성 및 심각도 평가
        2. 주요 영향 받을 리스크 요인들
        3. 예상되는 금융기관별 영향
        4. 리스크 완화 전략
        5. 규제 당국 대응 방안
        """
        
        return self.chat(prompt)
