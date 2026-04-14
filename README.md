# P-IRIS — 포스코인터내셔널 언론대응 인텔리전스 시스템

**P**osco International **I**ntelligent **R**isk & **I**ssue **S**ystem

> 언론홍보 담당자가 실시간 뉴스 모니터링부터 이슈 보고서 생성까지 원스톱으로 처리할 수 있는 Streamlit 기반 웹 애플리케이션

- **배포 주소**: https://poscointlwh.streamlit.app/
- **모델**: GPT-4.1 (`gpt-4.1-2025-04-14`) + 네이버 검색 API + 데이터랩 API

---

## 주요 기능

| 메뉴 | 설명 |
|---|---|
| **뉴스 모니터링** | 포스코인터내셔널 관련 키워드 자동 수집·분류, 실시간 감지 |
| **키워드 인사이트** | 임의 키워드 입력 → AI 브리핑 자동 생성 (API 3회 이내) |
| **이슈보고 생성** | 이슈 정보 입력 → 임원 보고용 문서 자동 작성 |
| **언론사 정보** | 주요 언론사 담당기자 및 연락처 검색 |
| **담당자 정보** | 내부 부서별 PR 담당자 정보 조회 |
| **대응이력 검색** | 과거 언론대응 사례 키워드 검색 |

---

## 프로젝트 구조

```
P-IRIS/
├── streamlit_app.py          # 메인 Streamlit 앱 (진입점)
├── news_collector.py         # 네이버·Google 뉴스 수집 공통 모듈
├── standalone_monitor.py     # GitHub Actions 자동 모니터링 스크립트
├── recover_missing_notifications.py  # 누락 알림 복구 유틸리티
├── data_based_llm.py         # 이슈보고 생성 LLM 로직
├── llm_manager.py            # LLM 관리 클래스
├── naver_search.py           # 네이버 검색 API 래퍼
├── enhanced_research_service.py  # 리서치 서비스
├── logger.py                 # 로거
│
├── components/               # Streamlit 화면 컴포넌트
│   ├── news_dashboard.py     # 뉴스 모니터링 대시보드
│   ├── publisher_dashboard.py  # 언론사 정보 대시보드
│   └── status_dashboard.py   # 시스템 상태 대시보드
│
├── pages/
│   └── keyword_insight.py    # 키워드 인사이트 페이지
│
├── modules/                  # 키워드 인사이트 전용 모듈
│   ├── naver_news.py         # 네이버 뉴스 API (1회 호출, 최대 100건)
│   ├── naver_datalab.py      # 네이버 데이터랩 API (트렌드)
│   ├── insight_generator.py  # GPT 단일 호출 (call_gpt_once)
│   ├── ui_components.py      # UI 렌더링 컴포넌트
│   ├── response_history.py   # 대응이력 조회
│   ├── journalist_db.py      # 기자 DB 조회
│   └── media_utils.py        # 매체명 파싱 유틸리티
│
├── data/                     # 운영 데이터
│   ├── news_monitor.csv      # 뉴스 DB (자동 갱신)
│   ├── master_data.json      # 부서·담당자 마스터
│   ├── 언론대응내역.csv       # 과거 대응이력
│   ├── 출입기자_리스트.csv    # 출입기자 목록
│   ├── sent_articles_cache.json  # 알림 중복 방지 캐시
│   └── system_status.json    # 시스템 상태
│
├── .github/workflows/        # GitHub Actions
│   ├── news_monitor.yml      # 뉴스 자동 수집 (매시간)
│   ├── keep_alive.yml        # Streamlit Cloud 슬립 방지
│   └── health_check.yml      # 시스템 상태 점검 (1일 2회)
│
├── requirements.txt
├── .env.example
└── STREAMLIT_CLOUD_SETUP.md  # 배포 설정 가이드
```

---

## 환경 변수 설정

`.env` 파일 (로컬) 또는 Streamlit Cloud Secrets에 아래 키를 설정합니다.

```env
# OpenAI
OPEN_API_KEY=sk-...

# 네이버 검색 API (https://developers.naver.com)
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...

# 텔레그램 알림 (선택)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
```

`.env.example` 파일을 복사해 사용하세요.

```bash
cp .env.example .env
```

---

## 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 앱 실행
streamlit run streamlit_app.py
```

Python 3.11 이상 필요 (`.python-version` 참고).

---

## 키워드 인사이트 — API 호출 원칙

검색 1회당 외부 API 호출을 최소화합니다.

| API | 호출 횟수 | 용도 |
|---|---|---|
| 네이버 뉴스 검색 | 1회 (최대 100건) | 기사 수집 |
| 네이버 데이터랩 | 1회 (30일 트렌드) | 검색 관심도 |
| GPT-4.1 | 1회 | 요약·이슈·리스크·액션 전체 생성 |

동일 키워드는 **1시간 이내 재검색 시 `session_state` 캐시** 우선 사용합니다.

---

## GitHub Actions 자동화

| 워크플로 | 주기 | 역할 |
|---|---|---|
| `news_monitor.yml` | 매시간 | 뉴스 수집 → `data/news_monitor.csv` 갱신 |
| `keep_alive.yml` | 12시간마다 | Streamlit Cloud 슬립 방지 |
| `health_check.yml` | 1일 2회 | DB 갱신 여부·캐시 상태 점검 |

---

## 배포

Streamlit Cloud 초기 설정은 [STREAMLIT_CLOUD_SETUP.md](./STREAMLIT_CLOUD_SETUP.md)를 참고하세요.

**Main file path**: `streamlit_app.py`

GitHub `main` 브랜치에 push하면 Streamlit Cloud가 자동으로 재배포합니다.
재배포가 반영되지 않을 경우 **Manage app → Reboot app** 으로 수동 재시작하세요.
