# NEW RISK MANAGEMENT SYSTEM

OpenAI API를 활용한 데이터 기반 리스크 관리 및 언론대응 시스템

## 🚀 주요 기능

### 1. 기본 LLM 기능
- OpenAI GPT 모델을 활용한 대화형 AI
- 코드 생성, 텍스트 분석, 번역 등 다양한 기능
- 리스크 관리 특화 분석 (신용리스크, VaR 계산, 스트레스 테스트)

### 2. 데이터 기반 답변 생성
- **master_data.json**: 부서별 담당자 정보 및 담당 이슈
- **언론대응내역.csv**: 과거 언론대응 사례 데이터
- 질의에 따른 관련 부서 자동 매칭
- 유사 사례 기반 대응 전략 추천

### 3. 데이터 버전 관리 시스템
- **자동 백업**: 데이터 파일 변경 시 자동 버전 관리
- **무결성 검사**: 데이터 구조 및 필수 필드 자동 검증
- **복원 기능**: 이전 버전으로 롤백 가능
- **변경 추적**: 모든 데이터 변경 이력 추적

### 4. 대화형 명령어 시스템
```
/data [질문]        - 데이터 기반 답변
/strategy [이슈]    - 대응 전략 추천
/trend              - 이슈 트렌드 분석
/risk [회사정보]    - 신용 리스크 분석
/var [포트폴리오]   - VaR 계산 방법론
/version            - 데이터 버전 정보
/backup [파일] [설명] [유형] - 수동 백업 생성
```

## 📁 프로젝트 구조

```
NEW_RISK_MANAGEMENT/
├── main.py                 # 메인 실행 파일
├── llm_manager.py          # LLM 관리 클래스
├── data_based_llm.py       # 데이터 기반 답변 생성
├── data_version_manager.py # 데이터 버전 관리 시스템
├── .env                    # 환경 변수 (API 키 등)
├── .env.example            # 환경 변수 템플릿
├── pyproject.toml          # 프로젝트 설정
├── DATA_UPDATE_GUIDE.md    # 데이터 업데이트 가이드
└── data/
    ├── master_data.json    # 부서/담당자 마스터 데이터
    ├── 언론대응내역.csv     # 언론대응 사례 데이터
    ├── version_history.json # 버전 관리 히스토리
    └── backups/            # 자동 백업 파일들
```

## 🛠️ 설치 및 설정

### 1. 필수 요구사항
- Python 3.11+
- UV 패키지 매니저
- OpenAI API 키

### 2. 설치 과정

```bash
# 1. UV 설치 (Windows PowerShell)
powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"

# 2. 프로젝트 의존성 설치
uv add openai python-dotenv pandas

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일에 OpenAI API 키 설정
```

### 3. 환경 변수 설정

`.env` 파일에 다음 설정:

```env
# OpenAI API 설정
OPEN_API_KEY=your_openai_api_key_here

# GPT 모델 설정 (선택사항, 기본값: gpt-4o-mini)
OPENAI_GPT_MODEL=gpt-4o  # 최신 고성능 모델로 업그레이드

# 기본 환경 설정
ENVIRONMENT=development
DEBUG=True
DB_HOST=localhost
DB_PORT=5432
```

**GPT 모델 옵션:**
- `gpt-4o`: 최신 고성능 모델 (추천)
- `gpt-4o-mini`: 경량 모델 (기본값)
- `gpt-4-turbo`: 긴 컨텍스트용
- `o1-preview`: 복잡한 추론용

### 4. Streamlit Cloud 배포 설정

웹 앱(https://poscointlwh.streamlit.app/)에 배포 시:

1. Streamlit Cloud Secrets에 동일한 환경 변수 설정
2. **상세 가이드**: [STREAMLIT_CLOUD_SETUP.md](./STREAMLIT_CLOUD_SETUP.md) 참조
3. GPT-4o 적용 시 더 정확한 분석과 보고서 생성

## 🎯 사용법

### 1. 기본 실행

```bash
python main.py
```

실행하면 다음 단계로 진행됩니다:
1. 환경 설정 확인
2. 데이터 버전 및 무결성 확인  
3. 기본 LLM 기능 테스트
4. 데이터 기반 답변 기능 테스트
5. 대화형 채팅 모드 선택

### 2. 대화형 모드 사용 예시

```
사용자: /data 배당 관련 이슈 담당자 알려주세요
AI: IR그룹의 유근석 담당자에게 연락하세요 (02-3457-8114, gs.yu@posco-inc.com)

사용자: /strategy 전기차 관련 부정적 보도 발생
AI: [과거 사례 기반 대응 전략 제시]

사용자: /trend
AI: [최근 30건 이슈 트렌드 분석]
```

## 📊 데이터 버전 관리

### 자동 백업 시스템
- 모든 데이터 파일 변경 시 자동 백업 생성
- Semantic Versioning (Major.Minor.Patch) 적용
- 최근 10개 버전 자동 보관
- 파일 해시를 통한 중복 백업 방지

### 수동 백업 생성
```python
from data_version_manager import DataVersionManager

version_manager = DataVersionManager()

# 주요 변경 (Major): 조직 개편, 시스템 대폭 개선
version_manager.create_backup("master_data.json", "조직 개편 반영", "major")

# 일반 변경 (Minor): 부서 추가, 기능 개선
version_manager.create_backup("master_data.json", "신규 부서 추가", "minor")

# 경미한 수정 (Patch): 연락처 수정, 오타 수정
version_manager.create_backup("master_data.json", "연락처 업데이트", "patch")
```

### 버전 복원
```python
# 특정 버전으로 복원
version_manager.restore_version("master_data.json", "1.2.0")
```

### 데이터 무결성 검사
```python
# 전체 데이터 구조 검증
integrity_results = version_manager.check_data_integrity()
```

## 📊 데이터 구조

### master_data.json 구조
```json
{
  "departments": {
    "부서명": {
      "담당자": "이름",
      "연락처": "전화번호",
      "이메일": "이메일주소",
      "담당이슈": ["키워드1", "키워드2"],
      "우선순위": 1,
      "활성상태": true
    }
  }
}
```

### 언론대응내역.csv 구조
```csv
순번,발생 일시,발생 유형,현업 부서,단계,이슈 발생 보고,대응 결과
```

## 🔧 주요 기능

### 1. 부서별 자동 매칭
- 질의 내용 분석하여 관련 키워드 추출
- 부서별 담당이슈와 매칭하여 관련도 점수 계산
- 우선순위와 관련도 기반으로 담당 부서 추천

### 2. 유사 사례 검색
- 질의 내용과 과거 사례의 유사도 분석
- 텍스트 매칭 기반 관련 사례 추출
- 대응 결과 및 방법론 참조

### 3. 트렌드 분석
- 발생 유형별, 단계별 집계 분석
- 최근 사례 패턴 분석
- 리스크 레벨 및 대응 우선순위 제시

## 🚨 주의사항

### 보안
- `.env` 파일은 절대 Git에 커밋하지 마세요
- OpenAI API 키는 안전하게 관리하세요
- 민감한 데이터는 별도 보안 조치 필요

### 데이터 관리
- 정기적인 데이터 백업 필요
- 부서 정보 변경 시 master_data.json 업데이트
- 언론대응 사례는 지속적으로 추가 관리

---

**최종 업데이트**: 2025년 8월 6일
