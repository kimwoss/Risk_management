#!/usr/bin/env python3
"""
OpenAI API 상태 체크 유틸리티
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

def check_api_status():
    """OpenAI API 상태 확인"""
    load_dotenv()
    
    api_key = os.getenv('OPEN_API_KEY')
    if not api_key:
        return {
            "status": "error",
            "message": "API 키가 설정되지 않았습니다.",
            "suggestions": ["환경 변수 OPEN_API_KEY를 확인하세요."]
        }
    
    client = OpenAI(api_key=api_key)
    
    try:
        # 간단한 테스트 요청
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "안녕하세요"}],
            max_tokens=10
        )
        
        return {
            "status": "success",
            "message": "API가 정상적으로 작동합니다.",
            "model": "gpt-4",
            "response_length": len(response.choices[0].message.content)
        }
        
    except Exception as e:
        error_msg = str(e)
        
        if "insufficient_quota" in error_msg:
            return {
                "status": "quota_exceeded",
                "message": "API 할당량이 초과되었습니다.",
                "suggestions": [
                    "https://platform.openai.com/account/billing에서 사용량 확인",
                    "크레딧 추가 구매 필요",
                    "월간 한도 리셋 대기"
                ]
            }
        elif "rate_limit" in error_msg:
            return {
                "status": "rate_limited",
                "message": "요청 한도에 도달했습니다.",
                "suggestions": ["잠시 후 다시 시도해주세요."]
            }
        else:
            return {
                "status": "error",
                "message": f"API 오류: {error_msg}",
                "suggestions": ["API 키와 인터넷 연결을 확인하세요."]
            }

if __name__ == "__main__":
    result = check_api_status()
    print(f"상태: {result['status']}")
    print(f"메시지: {result['message']}")
    if 'suggestions' in result:
        print("해결방법:")
        for suggestion in result['suggestions']:
            print(f"  - {suggestion}")
