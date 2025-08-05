# app/services/report_generator.py

import openai
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 기존 시스템 임포트
from generate_report import ReportGenerator as BaseReportGenerator

def generate_prompt(data: dict) -> str:
    """사용자 입력을 기반으로 GPT 프롬프트 구성"""
    # 외부 기사 요약 포함 여부
    external_info = f"\n🌐 외부 기사 URL: {data.get('external_news_url')}" if data.get('external_news_url') else ""
    
    # 포스코인터내셔널 표준 포맷 활용
    prompt_data = {
        "발생_일시": datetime.now().strftime('%Y.%m.%d %H:%M'),
        "매체": data.get('media', ''),
        "기자": data.get('media', '').split(' ')[-1] if ' ' in data.get('media', '') else '',
        "주요내용": f"{data.get('issue_content', '')}{external_info}",
        "대응결과": data.get('response', '(입력 대기 중)')
    }
    
    return prompt_data

def generate_report(data: dict) -> str:
    """
    기존 완성된 ReportGenerator 시스템을 활용한 보고서 생성
    외부 뉴스 검증 기능이 완비된 시스템 연동
    """
    try:
        # 기존 완성된 시스템 활용
        generator = BaseReportGenerator()
        
        # 입력 데이터 변환
        input_data = generate_prompt(data)
        
        # 외부 뉴스 검증 기능이 완비된 보고서 생성
        result = generator.generate_report(input_data)
        
        if result['success']:
            return result['report_content']
        else:
            return f"❌ 보고서 생성 실패: {result.get('error', '알 수 없는 오류')}"
            
    except Exception as e:
        # 대체 간단 생성 로직
        return generate_simple_report(data)

def generate_simple_report(data: dict) -> str:
    """간단한 대체 보고서 생성 (완성된 시스템 미사용 시)"""
    current_time = datetime.now().strftime('%Y.%m.%d %H:%M')
    external_info = f"\n   - 외부 기사: {data.get('external_news_url')}" if data.get('external_news_url') else ""
    
    return f"""
<이슈 발생 보고>
1. 발생 일시: {current_time}
2. 대응 단계: 1단계 (관심)
3. 발생 내용: ({data.get('media', '미입력')})
   - {data.get('issue_content', '내용 미입력')}{external_info}
4. 유관 의견: (가안) 
   - 사실 확인: 현재 내용을 검토 중이며, 관련 부서와 협의하여 정확한 정보를 확인하고 있습니다.
   - 설명 논리: 외부 보도 내용에 대해 내부 검증을 진행하고, 필요시 추가 설명을 제공할 예정입니다.
5. 대응 방안: (가안) 관련 부서와 협의하여 사실관계를 확인한 후, 적절한 대응 방안을 마련하겠습니다.
6. 대응 결과: {data.get('response', '(입력 대기 중)')}

참고: Streamlit 자동화 시스템을 통한 보고서 생성
무엇을 더 도와드릴까요?
"""
