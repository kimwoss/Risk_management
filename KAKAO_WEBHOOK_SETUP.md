# 📱 텔레그램 알림 설정 가이드 (개인/그룹)

뉴스 알림을 **개인 메시지** 또는 **그룹 채팅방**으로 받는 방법입니다.

---

## 🎯 선택하기: 개인 vs 그룹

| 옵션 | 개인 메시지 | 그룹 채팅 |
|------|-----------|---------|
| **알림 대상** | 나만 | 팀원 모두 |
| **공유** | 불가능 | 가능 |
| **토론** | 불가능 | 가능 |
| **Chat ID** | 양수 (예: 7032432112) | 음수 (예: -1001234567890) |
| **설정 난이도** | 쉬움 ⭐ | 보통 ⭐⭐ |

---

## 📋 공통: 텔레그램 봇 생성

### **1단계: 텔레그램 앱 설치**
- 모바일/PC: https://telegram.org/

### **2단계: BotFather에서 봇 생성**
1. 텔레그램에서 `@BotFather` 검색
2. `/newbot` 명령어 입력
3. 봇 이름: `포스코뉴스알림봇`
4. 봇 username: `posco_news_bot` (unique해야 함)
5. **봇 토큰 받기**: `123456789:ABCdefGHI...` 형식

✅ 봇 토큰 복사해두기!

---

## 🔷 방법 A: 개인 메시지로 받기

### **1단계: 봇과 대화 시작**
1. 생성한 봇 검색 (예: `@posco_news_bot`)
2. 봇과 대화 시작
3. 아무 메시지나 전송 (예: `/start` 또는 "안녕")

### **2단계: Chat ID 확인**

#### **방법 1: 브라우저 사용**
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
```
- `<YOUR_BOT_TOKEN>`을 실제 봇 토큰으로 교체
- `"chat":{"id":7032432112}` 부분의 숫자 복사

#### **방법 2: 전용 봇 사용**
1. `@userinfobot` 검색
2. `/start` 입력
3. 표시되는 `Id` 값 복사

#### **방법 3: 웹페이지에서 자동 확인** (가장 쉬움!)
1. 뉴스 모니터링 페이지 접속
2. "📱 텔레그램 알림 설정 확인" 펼치기
3. "🔎 Chat ID 확인하기" 클릭
4. 자동으로 Chat ID 표시!

### **3단계: Streamlit Cloud 설정**
```toml
TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHI..."
TELEGRAM_CHAT_ID = "7032432112"  ← 개인 Chat ID (양수)
```

---

## 🔷 방법 B: 그룹 채팅방으로 받기

자세한 가이드: `TELEGRAM_GROUP_SETUP.md` 파일 참조

### **간단 요약:**

1. **그룹 생성**
   - 텔레그램에서 새 그룹 만들기
   - 그룹명: "포스코 뉴스 모니터링"

2. **봇 추가**
   - 그룹에 봇 추가
   - 그룹에서 아무 메시지나 전송

3. **그룹 Chat ID 확인**
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   - `"chat":{"id":-1001234567890}` 부분의 숫자 복사
   - ⚠️ 마이너스(-) 기호 포함!

4. **Streamlit Cloud 설정**
   ```toml
   TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHI..."
   TELEGRAM_CHAT_ID = "-1001234567890"  ← 그룹 Chat ID (음수)
   ```

---

## 🚀 Streamlit Cloud 환경변수 설정

1. **Streamlit Cloud 접속**
   - https://share.streamlit.io/

2. **앱 선택 → Settings → Secrets**

3. **다음 내용 추가/수정**
   ```toml
   OPEN_API_KEY = "your_openai_key"
   NAVER_CLIENT_ID = "your_naver_id"
   NAVER_CLIENT_SECRET = "your_naver_secret"

   # 텔레그램 설정
   TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHI..."
   TELEGRAM_CHAT_ID = "7032432112"  ← 또는 "-1001234567890" (그룹)
   ```

4. **Save 클릭**
   - 자동 재배포 (1-2분)

---

## 🧪 테스트

재배포 완료 후:

1. 뉴스 모니터링 페이지 접속
2. "📱 텔레그램 알림 설정 확인" 펼치기
3. "📤 테스트 알림 보내기" 클릭
4. 텔레그램에서 메시지 확인! 🎉

---

## 💡 로컬 개발 (.env 파일)

로컬에서 테스트하려면:

```env
OPEN_API_KEY=your_openai_key
NAVER_CLIENT_ID=your_naver_id
NAVER_CLIENT_SECRET=your_naver_secret

# 텔레그램 봇 설정
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHI...
TELEGRAM_CHAT_ID=7032432112
```

---

## 🆘 문제 해결

### ❌ "Chat not found"
- **개인**: 봇과 대화를 시작했는지 확인
- **그룹**: 봇이 그룹에 추가되었는지 확인

### ❌ "Bot was kicked"
- 봇이 그룹에서 강퇴됨
- 봇을 다시 그룹에 추가

### ❌ Chat ID가 작동하지 않음
- 웹페이지의 "🔎 Chat ID 확인하기" 사용
- getUpdates로 정확한 Chat ID 재확인

### ❌ 그룹에서 마이너스가 없음
- 그룹이 supergroup이 아님
- 멤버 100명 이상 추가하거나
- 그룹 히스토리 설정 변경

---

## ✅ 완료!

이제 텔레그램으로 뉴스 알림을 받을 수 있습니다! 📱

- **180초마다** 자동 확인
- **신규 기사만** 알림
- **개별 메시지**로 깔끔하게
- **최근 6시간** 이내 기사만

---

## 📚 추가 문서

- **그룹 설정 상세 가이드**: `TELEGRAM_GROUP_SETUP.md`
- **Chat ID 수정 가이드**: `TELEGRAM_CHATID_FIX.md`
- **배포 가이드**: `DEPLOYMENT_GUIDE.md`
