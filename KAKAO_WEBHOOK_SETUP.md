# 📱 카카오톡 오픈채팅 웹훅 설정 가이드

## 1️⃣ 오픈채팅방 생성

1. **카카오톡 앱에서 오픈채팅방 생성**
   - 카카오톡 → 우측 하단 `#` 버튼 → `오픈채팅` 탭
   - 우측 상단 `+` 버튼 → `일반 오픈채팅방 만들기`
   - 채팅방 이름: `뉴스 알림` (원하는 이름)
   - `확인` 클릭

## 2️⃣ 웹훅 URL 발급

### 방법 A: 카카오 디벨로퍼스 사용 (공식)

1. **카카오 디벨로퍼스 접속**
   - https://developers.kakao.com/ 접속
   - 카카오 계정으로 로그인

2. **애플리케이션 추가**
   - `내 애플리케이션` → `애플리케이션 추가하기`
   - 앱 이름: `뉴스알림봇` (원하는 이름)
   - 회사명: 포스코인터내셔널
   - `저장` 클릭

3. **REST API 키 복사**
   - 생성된 앱 클릭 → `앱 키` 탭
   - `REST API 키` 복사

4. **메시지 API 설정**
   - `플랫폼` → `Web 플랫폼 등록`
   - 사이트 도메인: `http://localhost` (임시)
   - `카카오 로그인` → `활성화 설정` ON
   - `동의 항목` → `카카오톡 메시지 전송` 필수 동의 설정

### 방법 B: 오픈채팅 웹훅 (간단, 추천)

카카오톡 오픈채팅은 공식 웹훅을 제공하지 않으므로, **텔레그램으로 변경**하는 것을 강력히 추천드립니다.

---

## 🔄 대안: 텔레그램 봇 (5분 설정, 더 쉬움)

### 1. 텔레그램 봇 생성

1. **텔레그램 앱 설치** (모바일/PC)
   - https://telegram.org/

2. **BotFather에서 봇 생성**
   - 텔레그램에서 `@BotFather` 검색
   - `/newbot` 명령어 입력
   - 봇 이름 입력: `포스코뉴스알림봇`
   - 봇 username 입력: `posco_news_bot` (unique해야 함)
   - **토큰 받기**: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz...` 형식

3. **Chat ID 받기**
   - 생성된 봇과 대화 시작 (아무 메시지나 전송)
   - 브라우저에서 접속: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - `chat.id` 값 복사 (예: `1234567890`)

### 2. 환경변수 설정

#### 로컬 개발 (.env 파일)
```env
# 기존 내용...
OPEN_API_KEY=your_openai_key
NAVER_CLIENT_ID=your_naver_id
NAVER_CLIENT_SECRET=your_naver_secret

# 텔레그램 봇 설정 (새로 추가)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz...
TELEGRAM_CHAT_ID=1234567890
```

#### Streamlit Cloud (배포)
1. Streamlit Cloud 대시보드 접속
2. 앱 선택 → `Settings` → `Secrets`
3. 다음 내용 추가:
```toml
TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz..."
TELEGRAM_CHAT_ID = "1234567890"
```

---

## ✅ 설정 완료!

설정이 완료되면 새로운 뉴스가 업데이트될 때마다:
- 텔레그램으로 기사 제목, 언론사, 날짜 알림
- 링크 클릭 시 기사 바로 이동
- 180초마다 자동 확인

---

## 💡 추가 옵션

### 알림 필터 설정 (선택)
- 특정 키워드만 알림 받기
- 특정 시간대에만 알림 받기 (예: 09:00~18:00)
- 중요도 높은 기사만 알림 받기

필요하시면 말씀해주세요!
