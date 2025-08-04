# 위기관리 커뮤니케이션 시스템 (Risk Management Communication System)

POSCO International의 위기 대응 커뮤니케이션을 위한 AI 기반 분석 시스템입니다.

## 🎯 주요 기능

- **GPT 기반 위기 대응 전략 제공**: OpenAI GPT를 활용한 전문적인 위기 대응 조언
- **유사 사례 검색**: FAISS 벡터 검색을 통한 과거 유사 이슈 분석
- **한국어 특화**: 한국어 텍스트 처리 및 임베딩 최적화
- **대화형 인터페이스**: 실시간 질의응답 및 분석 기능

## 🏗️ 시스템 아키텍처

```
ai_commsystem/
├── config/                 # 설정 파일
│   └── settings.py         # 중앙 집중식 설정 관리
├── src/                    # 소스 코드
│   ├── core/              # 핵심 비즈니스 로직
│   │   └── risk_analyzer.py
│   ├── services/          # 서비스 계층
│   │   ├── openai_service.py
│   │   ├── embedding_service.py
│   │   └── search_service.py
│   └── utils/             # 유틸리티 모듈
│       ├── data_loader.py
│       └── logger.py
├── data/                  # 데이터 파일
│   └── index/            # FAISS 인덱스 저장소
├── logs/                 # 로그 파일
└── main.py              # 메인 실행 파일
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 활성화 (Windows)
start_project.bat

# 또는 PowerShell
./activate_env.ps1
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일 생성:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. 시스템 실행

```bash
# 메인 분석 시스템 (대화형 모드 포함)
python main.py

# FAISS 인덱스 생성 (최초 1회)
python build_index.py

# 유사도 검색만 실행
python search.py
# 또는 특정 검색어로
python search.py "메탄 누출 대응 방안"
```

## 📋 주요 컴포넌트

### 🧠 RiskAnalyzer (핵심 분석 엔진)
- GPT 기반 위기 대응 전략 생성
- 유사 사례 검색 및 분석
- 대화형 모드 지원

### 🔍 SearchService (유사도 검색)
- FAISS 벡터 인덱스 기반 검색
- 날짜 기반 최신순 정렬
- 한국어 SentenceTransformer 활용

### 📊 EmbeddingService (임베딩 관리)
- 한국어 특화 모델: `jhgan/ko-sroberta-multitask`
- FAISS 인덱스 생성 및 관리
- 벡터 저장 및 로드

### 🤖 OpenAIService (GPT 연동)
- GPT-3.5-turbo 기반 대화
- 위기 대응 전문가 페르소나
- 에러 핸들링 및 로깅

## 📈 데이터 처리 파이프라인

1. **CSV 데이터 로드**: CP949/UTF-8 인코딩 자동 처리
2. **기자문의 필터링**: "기자문의", "기자 문의" 타입만 추출
3. **임베딩 생성**: 한국어 SentenceTransformer 활용
4. **FAISS 인덱스 구축**: L2 거리 기반 유사도 계산
5. **검색 및 분석**: 유사도 + 최신순 정렬

## 🔧 설정 옵션

주요 설정은 `config/settings.py`에서 관리:

- `DEFAULT_MODEL`: GPT 모델 (기본: gpt-3.5-turbo)
- `EMBEDDING_MODEL_NAME`: 임베딩 모델 (기본: jhgan/ko-sroberta-multitask)
- `DEFAULT_TOP_K`: 검색 결과 개수 (기본: 3)
- `SYSTEM_PROMPT`: GPT 시스템 프롬프트

## 📝 로깅

- **콘솔 로그**: INFO 레벨 이상
- **파일 로그**: `logs/` 디렉토리에 일별 저장
- **상세 로그**: DEBUG 레벨 함수/라인 정보 포함

## 🛠️ 개발 환경

- **Python**: 3.11+
- **주요 라이브러리**:
  - openai: GPT API 연동
  - sentence-transformers: 한국어 임베딩
  - faiss-cpu: 벡터 검색
  - pandas: 데이터 처리

## 📄 라이선스

이 프로젝트는 POSCO International 내부 사용을 위한 것입니다.

## 🤝 기여

내부 개발팀 전용 프로젝트입니다.