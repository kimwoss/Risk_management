# GitHub Actions 뉴스 모니터링 설정 가이드

## 📋 개요

이 가이드는 GitHub Actions를 사용하여 **3분마다 자동으로 뉴스를 수집하고 텔레그램 알림을 전송**하는 시스템을 설정하는 방법을 설명합니다.

**장점:**
- ✅ 완전 무료
- ✅ 3분마다 정확히 실행
- ✅ Streamlit 앱 슬립 모드와 무관하게 독립적으로 작동
- ✅ GitHub에서 실행 로그 확인 가능

---

## 🚀 설정 단계

### 1단계: GitHub Repository에 코드 푸시

먼저 다음 파일들이 저장소에 있는지 확인하세요:

```
NEW_RISK_MANAGEMENT/
├── .github/
│   └── workflows/
│       └── news_monitor.yml          # ✅ 새로 생성됨
├── standalone_monitor.py             # ✅ 새로 생성됨
├── requirements.txt
├── data/
│   └── news_monitor.csv              # (자동 생성됨)
└── ...
```

**푸시 명령:**
```bash
git add .github/workflows/news_monitor.yml standalone_monitor.py
git commit -m "Add GitHub Actions news monitoring"
git push origin main
```

---

### 2단계: GitHub Secrets 설정

GitHub Actions가 환경변수에 접근할 수 있도록 Secrets를 설정합니다.

#### 📍 Secrets 설정 방법

1. **GitHub 저장소 페이지**로 이동
   - 예: `https://github.com/YOUR_USERNAME/NEW_RISK_MANAGEMENT`

2. **Settings** 탭 클릭

3. 왼쪽 사이드바에서 **Secrets and variables** → **Actions** 클릭

4. **New repository secret** 버튼 클릭

5. 다음 4개의 Secrets를 추가:

| Secret 이름 | 값 | 설명 |
|-------------|-----|------|
| `TELEGRAM_BOT_TOKEN` | `7895445...` | 텔레그램 봇 토큰 (BotFather에서 발급) |
| `TELEGRAM_CHAT_ID` | `123456789` | 텔레그램 채팅 ID |
| `NAVER_CLIENT_ID` | `abcd1234...` | 네이버 API 클라이언트 ID |
| `NAVER_CLIENT_SECRET` | `xyz789...` | 네이버 API 클라이언트 시크릿 |

#### 🔑 Secrets 값 찾는 방법

**Streamlit Cloud에 이미 설정되어 있다면:**

1. [Streamlit Cloud](https://share.streamlit.io/) 로그인
2. 앱 선택 → **Settings** → **Secrets**
3. 값을 복사하여 GitHub Secrets에 추가

**또는 로컬 `.env` 파일에서:**

```bash
# .env 파일 내용 확인
cat .env
```

---

### 3단계: GitHub Actions 활성화

#### ✅ Actions 권한 확인

1. GitHub 저장소 → **Settings** → **Actions** → **General**
2. **Actions permissions** 섹션에서:
   - ✅ "Allow all actions and reusable workflows" 선택
3. **Workflow permissions** 섹션에서:
   - ✅ "Read and write permissions" 선택
4. **Save** 클릭

---

### 4단계: 수동 테스트 실행

푸시 후 바로 작동하는지 확인해봅시다.

1. GitHub 저장소 → **Actions** 탭 클릭
2. 왼쪽에서 **"News Monitor"** 워크플로우 선택
3. **Run workflow** 버튼 클릭 → **Run workflow** 확인
4. 실행 로그 확인:
   - ✅ 뉴스 수집 로그
   - ✅ 텔레그램 알림 전송 로그
   - ✅ DB 저장 로그

---

## 📊 작동 확인

### ✅ 정상 작동 시나리오

1. **3분마다 자동 실행**
   - GitHub Actions → News Monitor 워크플로우에서 주기적인 실행 기록 확인
   - 예: `Update news database - 2025-11-06 12:03:00 UTC`

2. **신규 기사 발견 시**
   - 텔레그램 알림 수신:
     ```
     🚨 새 뉴스

     [연합뉴스] 포스코인터내셔널, 새로운 프로젝트 착수
     🕐 2025-11-06 21:00
     🔗 https://...
     ```

3. **DB 자동 업데이트**
   - `data/news_monitor.csv` 파일이 자동으로 커밋됨
   - 커밋 메시지: `"Update news database - YYYY-MM-DD HH:MM:SS UTC"`

---

## 🔧 문제 해결

### ❌ 워크플로우가 실행되지 않음

**원인:** GitHub Actions가 비활성화되어 있거나 권한이 없음

**해결:**
1. Settings → Actions → General
2. "Allow all actions" 활성화
3. "Read and write permissions" 활성화

---

### ❌ API 키 오류 (Missing API keys)

**로그 예시:**
```
[DEBUG] Missing API keys, returning empty result
```

**원인:** GitHub Secrets가 제대로 설정되지 않음

**해결:**
1. Settings → Secrets and variables → Actions
2. 4개의 Secrets가 모두 설정되어 있는지 확인:
   - TELEGRAM_BOT_TOKEN
   - TELEGRAM_CHAT_ID
   - NAVER_CLIENT_ID
   - NAVER_CLIENT_SECRET
3. Secret 이름의 철자가 정확한지 확인 (대소문자 구분!)

---

### ❌ 텔레그램 알림이 오지 않음

**로그 예시:**
```
[DEBUG] ⚠️ 텔레그램 설정 없음 - 알림 스킵
```

**원인 1:** TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 잘못됨

**해결:**
1. BotFather에서 `/mybots` → 봇 선택 → API Token 확인
2. 텔레그램 채팅방에서 `/start` 메시지 전송
3. Chat ID 확인: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`

**원인 2:** 첫 실행 (스팸 방지)

**로그 예시:**
```
[MONITOR] ⏭️ 신규 기사 5건 감지 - 첫 실행이므로 알림 스킵
```

**정상:** 첫 실행 시에는 알림이 전송되지 않습니다. 다음 실행(3분 후)부터 알림이 작동합니다.

---

### ❌ API 할당량 초과 (429 Error)

**로그 예시:**
```
[ERROR] API 할당량 초과 (429): API quota exceeded
```

**원인:** 네이버 API 일일 할당량(25,000건) 초과

**해결:**
1. **대기:** 매일 자정(KST) 이후 할당량 재설정
2. **새 API 키 발급:**
   - [네이버 개발자 센터](https://developers.naver.com/apps/#/register)
   - 새 애플리케이션 등록
   - GitHub Secrets 업데이트

---

## 📈 모니터링 및 로그 확인

### GitHub Actions 로그 보기

1. GitHub 저장소 → **Actions** 탭
2. 워크플로우 실행 기록 클릭
3. **monitor** job 클릭
4. 각 단계의 로그 확인:
   - **Install dependencies**: 패키지 설치 로그
   - **Run news monitor**: 뉴스 수집 및 알림 로그
   - **Commit and push updated database**: DB 업데이트 로그

### 로그 예시

**정상 실행 로그:**
```
================================================================================
[MONITOR] 뉴스 수집 시작: 2025-11-06 12:00:00
================================================================================
[MONITOR] 기존 DB 로드 완료: 150건
[MONITOR] 키워드 '포스코인터내셔널' 검색 중...
[DEBUG] API Response items count: 5
[MONITOR] '포스코인터내셔널': 5건 수집
...
[DEBUG] 신규 기사 감지: 포스코인터내셔널, 새로운 프로젝트... (0.5시간 전)
[MONITOR] ✅ 신규 기사 3건 감지 - 텔레그램 알림 전송
[DEBUG] ✅ 메시지 전송 성공: 포스코인터내셔널, 새로운...
[MONITOR] ✅ DB 저장 완료: 총 153건
[MONITOR] ✅ 뉴스 수집 완료
================================================================================
[MONITOR] 작업 종료: 2025-11-06 12:00:45
================================================================================
```

---

## ⚙️ 커스터마이징

### 실행 주기 변경

`.github/workflows/news_monitor.yml` 파일 수정:

```yaml
on:
  schedule:
    # 5분마다 실행
    - cron: '*/5 * * * *'

    # 10분마다 실행
    - cron: '*/10 * * * *'

    # 매시간 정각에 실행
    - cron: '0 * * * *'
```

### 키워드 변경

`standalone_monitor.py` 파일의 `keywords` 리스트 수정:

```python
keywords = [
    "포스코인터내셔널",
    "새로운 키워드",
    # ...
]
```

변경 후 커밋 및 푸시:
```bash
git add standalone_monitor.py
git commit -m "Update keywords"
git push
```

---

## 🎯 완료!

설정이 완료되었습니다. 이제:

1. ✅ GitHub Actions가 **3분마다** 자동으로 뉴스를 수집합니다
2. ✅ 신규 기사 발견 시 **텔레그램 알림**이 전송됩니다
3. ✅ **Streamlit 앱이 슬립 모드**여도 알림이 정상 작동합니다
4. ✅ **완전 무료**로 운영됩니다

---

## 📞 문제가 계속 발생하면?

1. **GitHub Actions 로그** 전체 복사
2. **오류 메시지** 확인
3. 위의 "문제 해결" 섹션 참고

---

**작성일:** 2025-11-06
**버전:** 1.0
