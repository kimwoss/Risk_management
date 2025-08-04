# CLAUDE.md

이 파일은 이 저장소에서 코드를 다룰 때 Claude Code (claude.ai/code)에 대한 가이드를 제공합니다.

## 프로젝트 개요 (Project Overview)

이 프로젝트는 POSCO International을 위한 **위기 커뮤니케이션 대응 시스템**으로, AI를 활용하여 위기 대응 데이터를 분석합니다. 시스템 구성은 다음과 같습니다:

1. **위기 대응 분석**: GPT를 활용하여 기자 문의를 처리하고 전략적 조언 제공
2. **의미 기반 검색 (Semantic Search)**: FAISS와 한국어 문장 임베딩 모델을 사용하여 유사 사례 검색
3. **데이터 처리**: 한국어 CSV 데이터를 적절한 인코딩으로 처리하여 위기 대응 사례 분석

## 개발 환경 설정 (Environment Setup)

이 프로젝트는 Python 3.11+ 기반이며, 가상환경은 `.venv/` 폴더에 구성되어 있습니다.

**가상환경 활성화 방법:**
- Windows: `start_project.bat` 실행 또는 `.venv\Scripts\activate` 입력
- PowerShell: `activate_env.ps1` 실행

**필수 환경 변수 파일 (.env):**
- `.env` 파일 내 `OPENAI_API_KEY=your_api_key_here` 항목 필요

## 주요 의존 패키지 (Key Dependencies)

가상환경 내 다음 패키지를 설치하세요:

- `pandas`: CSV 데이터 처리용
- `openai`: GPT API 연동
- `python-dotenv`: 환경 변수 관리
- `sentence-transformers`: 한국어 텍스트 임베딩 모델 (`jhgan/ko-sroberta-multitask`)
- `faiss-cpu`: 벡터 유사도 검색
- `pickle`: 데이터 직렬화용

## 핵심 아키텍처 (Core Architecture)

### 데이터 계층 (`data/`)

- `최신 언론대응내역(GPT용).csv`: 주요 위기 커뮤니케이션 데이터셋
- 주요 컬럼: `순번`, `발생 일시`, `발생 유형`, `이슈 발생 보고`
- `기자문의`, `기자 문의` 유형만 필터링

### 애플리케이션 계층 (`app/`)

**main.py** – GPT 기반 데이터 분석 및 응답 생성
- CP949 인코딩(또는 fallback으로 UTF-8-sig)으로 CSV 데이터 로드
- 기자 문의 유형 데이터 필터링
- GPT를 활용한 대응 문구 생성
- 실행 명령어: `python app/main.py`

**embedding.py** – FAISS 인덱스 생성
- 한국어 문장 임베딩 모델을 사용해 임베딩 생성
- FAISS L2 거리 인덱스 구축
- 인덱스 및 매핑 결과는 `app/index/`에 저장
- 실행 명령어: `python app/embedding.py`

**faiss_search.py** – 의미 유사도 검색
- 미리 구축한 FAISS 인덱스 로드
- 날짜 기반 랭킹 포함 유사도 검색 수행
- 가장 유사한 최근 사례 Top-K 반환
- 실행 명령어: `python app/faiss_search.py`

### 인덱스 저장소 (`app/index/`)
- `faiss_index.bin`: FAISS 벡터 인덱스 파일
- `index_mapping.pkl`: 벡터와 원본 데이터 간 매핑 파일

## 일반 개발 워크플로우 (Common Development Workflows)

### 시스템 실행 순서
1. 가상환경 활성화: `start_project.bat`
2. 환경 테스트: `python test_env.py`
3. **분석 시스템 실행**: `python main.py`
4. **FAISS 인덱스 구축**: `python build_index.py`
5. **검색 기능 실행**: `python search.py` 또는 `python search.py "검색어"`

### 프로젝트 디렉토리 구조
