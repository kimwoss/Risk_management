# 🚀 배포 가이드

## 1️⃣ GitHub에 업로드

### 방법 1: 기존 저장소에 푸시
```bash
# 변경사항 확인
git status

# 필요한 파일 추가
git add .

# 커밋
git commit -m "위기관리커뮤니케이션 AI 시스템 업데이트"

# GitHub에 푸시
git push origin main
```

### 방법 2: 새 저장소 생성 (필요시)
1. GitHub에서 새 저장소 생성
2. 로컬에서 연결:
```bash
git remote add origin https://github.com/your-username/your-repo-name.git
git push -u origin main
```

## 2️⃣ Streamlit Cloud 배포 (무료)

### 단계별 가이드:

1. **Streamlit Cloud 접속**
   - https://share.streamlit.io/ 접속
   - GitHub 계정으로 로그인

2. **새 앱 배포**
   - "New app" 클릭
   - Repository: 방금 푸시한 저장소 선택
   - Branch: `main`
   - Main file path: `streamlit_app.py`

3. **환경변수 설정** (중요!)
   - "Advanced settings" 클릭
   - "Secrets" 섹션에 다음 내용 추가:
   ```toml
   OPEN_API_KEY = "your_openai_api_key"
   NAVER_CLIENT_ID = "your_naver_client_id"
   NAVER_CLIENT_SECRET = "your_naver_client_secret"

   # 텔레그램 알림 (선택사항)
   TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
   TELEGRAM_CHAT_ID = "your_telegram_chat_id"
   ```

   📱 **텔레그램 알림 설정 방법**은 `KAKAO_WEBHOOK_SETUP.md` 파일을 참조하세요!

4. **배포 완료**
   - "Deploy!" 클릭
   - 몇 분 후 공개 URL 생성됨 (예: `https://your-app.streamlit.app`)

## 3️⃣ 직원들과 공유

배포 완료 후 받게 되는 URL을 직원들에게 공유하면 됩니다!
- 예: `https://posco-crisis-management.streamlit.app`

### 접근 제한이 필요한 경우:
- Streamlit Cloud에서 "Settings" → "Sharing" → "Private" 설정
- 특정 이메일 주소만 접근 가능하도록 설정 가능

## 4️⃣ 주의사항

⚠️ **절대로 GitHub에 올리면 안 되는 것:**
- `.env` 파일 (API 키 포함)
- 개인정보가 포함된 실제 데이터
- 백업 파일들

✅ **반드시 확인:**
- `.env.example`은 업로드 OK (실제 값 없음)
- Streamlit Cloud의 Secrets에만 실제 API 키 입력
- data/ 폴더의 민감한 정보 확인

## 5️⃣ 업데이트 방법

코드 수정 후:
```bash
git add .
git commit -m "업데이트 내용"
git push origin main
```

→ Streamlit Cloud가 자동으로 재배포됩니다!
