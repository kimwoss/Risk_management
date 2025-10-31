# 🔧 텔레그램 Chat ID 확인 및 수정 가이드

## 문제 상황
- ✅ 봇 연결 성공 메시지는 나옴
- ✅ 봇과 대화도 시작함
- ❌ 하지만 알림 메시지가 오지 않음

→ **Chat ID가 잘못되었을 가능성 99%**

---

## 🎯 Chat ID 올바르게 확인하기

### 방법 1: 브라우저에서 직접 확인 (추천)

1. **텔레그램 앱에서 봇에게 메시지 전송**
   - 아무 메시지나 전송 (예: "안녕" 또는 "/start")

2. **브라우저 주소창에 다음 URL 입력**
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   - `<YOUR_BOT_TOKEN>` 부분을 실제 봇 토큰으로 교체
   - 예: `https://api.telegram.org/bot123456789:ABCdefGHI.../getUpdates`

3. **결과에서 Chat ID 찾기**
   ```json
   {
     "ok": true,
     "result": [
       {
         "update_id": 123456789,
         "message": {
           "message_id": 1,
           "from": {
             "id": 1234567890,  ← 이게 Chat ID!
             "is_bot": false,
             "first_name": "Your Name"
           },
           "chat": {
             "id": 1234567890,  ← 이것도 Chat ID! (이 값 사용)
             "first_name": "Your Name",
             "type": "private"
           },
           "date": 1234567890,
           "text": "안녕"
         }
       }
     ]
   }
   ```

4. **`"chat": { "id": 1234567890 }` 부분의 숫자를 복사**
   - ⚠️ 따옴표 없이 **숫자만** 복사
   - ⚠️ **마이너스(-)** 기호가 있다면 반드시 포함

---

### 방법 2: 전용 봇 사용

1. **텔레그램에서 `@userinfobot` 검색**

2. **`/start` 입력**

3. **봇이 알려주는 `Id` 값이 Chat ID**
   ```
   Id: 1234567890
   ```

---

## 🔧 Streamlit Cloud에 올바른 Chat ID 설정

1. **Streamlit Cloud 대시보드 접속**
   - https://share.streamlit.io/

2. **앱 선택 → Settings → Secrets**

3. **기존 내용 수정**
   ```toml
   TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHI..."
   TELEGRAM_CHAT_ID = "1234567890"  ← 여기를 새로운 Chat ID로 수정
   ```

   ⚠️ **주의사항:**
   - Chat ID는 **따옴표 안에** 작성
   - **숫자만** 입력 (공백, 특수문자 없음)
   - 마이너스 기호가 있으면 반드시 포함

4. **Save 클릭 → 자동 재배포 (1-2분 소요)**

---

## ✅ 재배포 후 테스트

1. **뉴스 모니터링 페이지 새로고침**

2. **"📱 텔레그램 알림 설정 확인" 펼치기**

3. **"🧪 테스트 알림 보내기" 클릭**

4. **텔레그램 앱 확인** → 메시지 수신!

---

## 🆘 여전히 안 된다면

### 확인 사항 체크리스트:

- [ ] 봇과 대화를 시작했는가? (아무 메시지나 전송)
- [ ] Chat ID에 공백이나 따옴표가 잘못 들어가지 않았는가?
- [ ] Chat ID가 정확한가? (getUpdates로 재확인)
- [ ] Streamlit Cloud에서 Save 후 재배포가 완료되었는가?
- [ ] 봇이 차단되지 않았는가? (텔레그램에서 봇 프로필 확인)

---

## 💡 추가 팁

### Chat ID가 마이너스(-)로 시작하는 경우
- 그룹 채팅방에 봇을 추가한 경우
- 마이너스 기호 **반드시 포함**
- 예: `TELEGRAM_CHAT_ID = "-1234567890"`

### Private 채팅 (1:1 대화)
- Chat ID가 양수 (마이너스 없음)
- 예: `TELEGRAM_CHAT_ID = "1234567890"`
