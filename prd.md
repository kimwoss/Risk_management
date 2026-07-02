# PRD — P-IRIS 제품 요구사항 문서

**P**osco International **I**ntelligent **R**isk & **I**ssue **S**ystem  
문서 버전: 1.0 | 작성일: 2026-06-30

---

## 1. 제품 개요

P-IRIS는 Python 3.11 + Streamlit 기반의 단일 페이지 웹 애플리케이션이다.  
역할 기반 인증(PR 담당자 / 유관 부서)을 통해 접근하며, 6개 메뉴로 구성된 언론대응 워크플로를 제공한다.

### 1.1 기술 스택

| 레이어 | 기술 |
|--------|------|
| **언어 / 런타임** | Python 3.11 |
| **UI 프레임워크** | Streamlit |
| **LLM** | OpenAI GPT-4.1 (`gpt-4.1-2025-04-14`) |
| **외부 뉴스 API** | 네이버 검색 API, Google News RSS |
| **트렌드 API** | 네이버 데이터랩 API |
| **알림** | Telegram Bot API |
| **데이터 저장** | CSV 파일 + JSON 파일 (파일 기반, DB 없음) |
| **자동화** | GitHub Actions (YAML 워크플로) |
| **배포** | Streamlit Cloud |

### 1.2 시스템 아키텍처

```
[GitHub Actions]
  heartbeat.yml (3분 루프)  ──┐
  news_monitor.yml (15분)    ──┤──→ standalone_monitor.py
  keep_alive.yml (1일 2회)   ──┤       ├── news_collector.py (네이버/Google 수집)
  health_check.yml (1일 2회) ──┘       ├── data/news_monitor.csv (뉴스 DB 갱신)
                                        └── Telegram 알림 발송

[사용자 브라우저]
    │
    ▼
streamlit_app.py (진입점 · 인증 · 라우팅)
    ├── components/news_dashboard.py      ← 뉴스 모니터링
    ├── pages/keyword_insight.py          ← 키워드 인사이트
    │     └── modules/ (naver_news, naver_datalab, insight_generator, ...)
    ├── data_based_llm.py                 ← 이슈보고 생성
    ├── components/publisher_dashboard.py ← 언론사 정보
    ├── (담당자 정보 — master_data.json)  ← 담당자 정보
    └── modules/response_history.py       ← 대응이력 검색
```

---

## 2. 인증 시스템

### 2.1 역할 정의

| 역할 코드 | 사용자 유형 | 접근 범위 |
|-----------|------------|----------|
| `pr` | PR 담당자 | 전 기능 (읽기 + 쓰기) |
| `general` | 유관 부서 담당자 | 뉴스 현황 조회, 키워드 인사이트 |

### 2.2 인증 흐름

1. 로그인 페이지에서 역할별 패스워드 입력
2. 서버에서 `SHA-256(password + secret_salt)` 해시 생성 → 브라우저 쿠키 저장
3. 이후 방문 시 쿠키 검증 → 자동 로그인 (URL `?auto_login={role}` 파라미터 경유)
4. 세션 상태(`st.session_state.authenticated`) 유지

**패스워드 설정**: Streamlit Cloud Secrets에 `PASSWORD_PR`, `PASSWORD_GENERAL` 키로 저장.

---

## 3. 기능 상세 요구사항

### 3.1 뉴스 모니터링

**목적**: 포스코인터내셔널 관련 키워드 기사를 자동 수집·분류하고 실시간으로 알림 발송

#### 수집 파이프라인

| 단계 | 모듈 | 상세 |
|------|------|------|
| 트리거 | GitHub Actions `heartbeat.yml` | cron `0,30 * * * *` + 내부 `sleep 180` 루프 → 실질 3분 케이던스 |
| 뉴스 수집 | `news_collector.py` | 네이버 검색 API + Google News RSS 병렬 수집 |
| 키워드 필터 | `KEYWORDS` / `EXCLUDE_KEYWORDS` | 포함 키워드 매칭, 제외 키워드 탈락 |
| 감성 분석 | `get_article_sentiment()` | 긍정 / 중립 / 부정 3단계 분류 |
| 중복 방지 | `sent_articles_cache.json` | 발송 완료 기사 URL 캐시로 재발송 차단 |
| DB 저장 | `data/news_monitor.csv` | 수집 기사 누적 저장 (자동 갱신) |
| 알림 발송 | Telegram Bot | 신규 기사 감지 시 즉시 발송 |

#### 대시보드 (components/news_dashboard.py)

- 당일 기사 총 건수 · 해시태그 카테고리별 통계 실시간 표시
- 기사 목록: 제목 · 언론사 · 발행시각 · 감성 레이블 · 원문 링크
- `streamlit-autorefresh`로 자동 갱신 (사용자 개입 불필요)

#### GitHub Actions 워크플로 구성

| 워크플로 | 주기 | 역할 |
|----------|------|------|
| `heartbeat.yml` | 3분 (내부 루프) | 주 백본. Streamlit 슬립과 무관하게 수집·발송 |
| `news_monitor.yml` | 15분 | 하트비트 장애 대비 백업 안전망 |
| `keep_alive.yml` | 1일 2회 | GitHub Actions 60일 비활성 자동중지 방지 |
| `health_check.yml` | 1일 2회 | DB 갱신 여부 · 캐시 상태 점검 |

> **설계 이유**: GitHub cron은 3분 단위를 보장하지 못함. `heartbeat.yml`은 단일 잡을 길게 유지하며 내부 `sleep 180` 루프로 3분 케이던스를 만들고, `concurrency` 그룹으로 루프를 끊김 없이 이어달린다.

---

### 3.2 키워드 인사이트

**목적**: 임의 키워드 입력 시 뉴스 수집 + 트렌드 + AI 분석을 단일 브리핑으로 제공

#### API 호출 원칙 (비용 최소화)

| API | 호출 횟수/검색 | 용도 |
|-----|--------------|------|
| 네이버 뉴스 검색 | 1회 (최대 100건) | 기사 수집 |
| 네이버 데이터랩 | 1회 (30일 트렌드) | 검색 관심도 추이 |
| GPT-4.1 | 1회 (`call_gpt_once`) | 전체 분석 결과 단일 생성 |

- 동일 키워드 1시간 이내 재검색: `session_state` 캐시 우선 사용 (캐시 키: `ki_raw_v2_{keyword}`)

#### GPT 출력 스키마 (JSON)

```json
{
  "summary": "2~3줄 핵심 요약",
  "trend": "급증 | 증가 | 보합 | 감소 | 급감",
  "crisis_level": "관심 | 주의 | 경계 | 심각",
  "sentiment": { "positive": 0, "neutral": 0, "negative": 0 },
  "top_media": ["매체1", "매체2", "매체3", "매체4", "매체5"],
  "issues": [{ "title": "이슈 제목", "description": "1줄 설명" }],
  "competitors": [{ "name": "기관명", "count": 0, "trend": "1줄 동향" }],
  "risks": ["리스크 항목 (3개 이내)"],
  "opportunities": ["기회 항목 (3개 이내)"],
  "actions": ["액션 제안 (3개 이내)"]
}
```

#### UI 렌더링 순서 (modules/ui_components.py)

1. 키워드 입력 폼
2. KPI 바 — 당일 기사 수 / 7일 기사 수 / 트렌드 / 관심도 / 위기 등급
3. 어조 분포 바 (긍정/중립/부정 %)
4. 뉴스 볼륨 차트 (30일 추이)
5. 주요 매체 차트
6. 이슈 클러스터 (3개)
7. 경쟁사/기관 동향 테이블
8. 과거 대응이력 연계
9. 리스크 시그널 / 액션 리스트

---

### 3.3 이슈보고 생성

**목적**: 담당자가 이슈 기본 정보를 입력하면 임원 보고용 문서를 AI가 자동 생성

- 모듈: `data_based_llm.py` (`DataBasedLLM` 클래스)
- 입력 항목: 이슈 제목, 발생 일시, 관련 기사 URL 또는 내용, 현업 부서, 위기 단계
- 출력: 구조화된 이슈 보고서 (배경 → 현황 → 리스크 → 대응 방향 형식)
- LLM: GPT-4.1, 시스템 프롬프트에 포스코인터내셔널 언론홍보 컨텍스트 주입

---

### 3.4 언론사 정보

**목적**: 주요 출입기자 및 언론사별 연락처를 플랫폼 내에서 즉시 검색

- 데이터 소스: `data/출입기자_리스트.csv`
- 검색 기준: 언론사명 · 기자명 · 담당 분야
- 컴포넌트: `components/publisher_dashboard.py`
- 업데이트 방식: CSV 파일 직접 수정 후 앱 자동 반영

---

### 3.5 담당자 정보

**목적**: 내부 부서별 PR 담당자 정보를 조회해 신속한 내부 협업 지원

- 데이터 소스: `data/master_data.json`
- 구조: `{ "부서명": { "담당자": "이름", "연락처": "...", ... } }`
- 업데이트 방식: JSON 파일 직접 수정

---

### 3.6 대응이력 검색

**목적**: 과거 언론대응 사례를 키워드·단계별로 검색해 유사 이슈 대응 참고

- 데이터 소스: `data/언론대응내역.csv`
- 필수 컬럼: `순번 / 발생 일시 / 발생 유형 / 현업 부서 / 단계 / 이슈 발생 보고 / 대응 결과`
- 필터: 키워드 전문 검색 + 단계(관심/주의/위기/비상) + 유형 필터
- 인코딩 요구사항: UTF-8 (EUC-KR 미지원)

---

## 4. 데이터 모델

### 4.1 파일 기반 데이터 구조

| 파일 | 형식 | 역할 | 갱신 주체 |
|------|------|------|----------|
| `news_monitor.csv` | CSV | 수집 뉴스 DB | GitHub Actions 자동 |
| `sent_articles_cache.json` | JSON | 알림 발송 완료 URL 캐시 | GitHub Actions 자동 |
| `system_status.json` | JSON | 시스템 상태 (마지막 수집 시각 등) | GitHub Actions 자동 |
| `언론대응내역.csv` | CSV | 과거 대응이력 (7컬럼) | 담당자 수동 |
| `출입기자_리스트.csv` | CSV | 출입기자 DB | 담당자 수동 |
| `master_data.json` | JSON | 내부 담당자 정보 | 담당자 수동 |
| `api_usage.json` | JSON | API 호출 횟수 추적 | 앱 자동 |

### 4.2 뉴스 기사 레코드 필드

| 필드 | 설명 |
|------|------|
| `title` | 기사 제목 (HTML 태그 제거) |
| `link` | 원문 URL |
| `publisher` | 언론사명 |
| `pub_date` | 발행 일시 (ISO 8601) |
| `sentiment` | `positive` / `neutral` / `negative` |
| `keywords` | 매칭된 키워드 목록 |
| `is_today` | 당일 발행 여부 (boolean) |
| `is_within_7d` | 7일 이내 발행 여부 (boolean) |

---

## 5. 비기능 요구사항

### 5.1 성능

| 항목 | 요구사항 |
|------|---------|
| 뉴스 수집 주기 | 최대 3분 (heartbeat 루프 기준) |
| 키워드 인사이트 응답 | GPT 응답 대기 포함 30초 이내 |
| 캐시 TTL | 1시간 (`session_state` 기반) |
| 뉴스 대시보드 갱신 | `streamlit-autorefresh` 자동 |

### 5.2 보안

| 항목 | 방식 |
|------|------|
| 인증 | SHA-256 해시 쿠키 + Streamlit `st.secrets` |
| API 키 관리 | `.env` (로컬) / Streamlit Cloud Secrets (운영) |
| 민감 데이터 | `.gitignore`에 `.env`, `data/*.csv`, `data/*.json` 포함 |
| 봇 차단 | 로그인 페이지 `<meta name="robots" content="noindex, nofollow">` |

### 5.3 가용성

- Streamlit Cloud 슬립 방지: `keep_alive.yml` (1일 2회 ping)
- 하트비트 장애 대비 백업: `news_monitor.yml` (15분 주기)
- 중복 발송 방지: `sent_articles_cache.json` + `scripts/merge_cache.py` (워크플로 병렬 실행 시 union 병합)

### 5.4 유지보수성

- 키워드 추가/제거: `news_collector.py`의 `KEYWORDS` / `EXCLUDE_KEYWORDS` 리스트 수정
- 언론사·기자 정보 갱신: CSV 파일 직접 수정 (UTF-8 필수)
- 대응이력 추가: `언론대응내역.csv` 행 추가 (`언론대응내역_업데이트가이드.md` 참조)

---

## 6. 외부 API 연동 명세

### 6.1 네이버 검색 API

| 항목 | 값 |
|------|-----|
| 엔드포인트 | `https://openapi.naver.com/v1/search/news.json` |
| 인증 헤더 | `X-Naver-Client-Id`, `X-Naver-Client-Secret` |
| 파라미터 | `query`, `display` (최대 100), `sort` (date) |
| 호출 원칙 | 키워드 인사이트 검색 1회당 1회 |

### 6.2 네이버 데이터랩 API

| 항목 | 값 |
|------|-----|
| 엔드포인트 | `https://openapi.naver.com/v1/datalab/search` |
| 기간 | 최근 30일 |
| 호출 원칙 | 키워드 인사이트 검색 1회당 1회 |

### 6.3 OpenAI API

| 항목 | 값 |
|------|-----|
| 모델 | `gpt-4.1-2025-04-14` |
| 시스템 프롬프트 | 한국 기업 언론홍보 전문가 역할 설정 |
| 출력 형식 | JSON only (JSON 외 텍스트 출력 금지 명시) |
| 호출 원칙 | 키워드 인사이트 1회, 이슈보고 생성 1회 |
| API 키 환경변수 | `OPEN_API_KEY` 또는 `OPENAI_API_KEY` |

### 6.4 Telegram Bot API

| 항목 | 값 |
|------|-----|
| 용도 | 신규 기사 감지 시 실시간 알림 |
| 환경변수 | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| 트리거 | GitHub Actions heartbeat 루프 |

---

## 7. 환경 변수

```env
# OpenAI
OPEN_API_KEY=sk-...

# 네이버 검색 API
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...

# Telegram 알림 (선택)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# 접근 코드 (레거시, st.secrets 권장)
ACCESS_CODE=...
```

로컬 실행: `.env` 파일 사용 (`python-dotenv` 자동 로드)  
운영 배포: Streamlit Cloud → App Settings → Secrets 에 동일 키 입력

---

## 8. 배포 구성

```
GitHub main 브랜치 push
    │
    ├── Streamlit Cloud 자동 재배포
    │       Main file: streamlit_app.py
    │       Python: 3.11 (.python-version)
    │
    └── GitHub Actions 워크플로 트리거
            heartbeat.yml / news_monitor.yml / keep_alive.yml / health_check.yml
```

수동 재시작 필요 시: Streamlit Cloud → Manage app → Reboot app
