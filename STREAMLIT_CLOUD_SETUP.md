# Streamlit Cloud GPT-4o 설정 가이드

## 🚀 GPT-4o 모델 적용하기

웹 앱(https://poscointlwh.streamlit.app/)에서 GPT-4o를 사용하려면 Streamlit Cloud의 Secrets를 업데이트해야 합니다.

### 📋 단계별 설정 방법

#### 1. Streamlit Cloud 대시보드 접속
```
https://share.streamlit.io/
```

#### 2. 앱 선택
- 왼쪽 메뉴에서 "Your apps" 클릭
- "poscointlwh" 앱 찾기
- 앱 오른쪽의 "⋮" (점 3개) 메뉴 클릭
- **"Settings"** 선택

#### 3. Secrets 탭 이동
- Settings 화면에서 **"Secrets"** 탭 클릭

#### 4. GPT 모델 설정 추가

기존 secrets에 다음 줄을 추가:

```toml
OPENAI_GPT_MODEL = "gpt-4o"
```

**전체 예시:**
```toml
# 기존 설정들...
OPEN_API_KEY = "your-openai-api-key"
NAVER_CLIENT_ID = "your-naver-client-id"
NAVER_CLIENT_SECRET = "your-naver-client-secret"

# GPT 모델 설정 (새로 추가)
OPENAI_GPT_MODEL = "gpt-4o"

# 텔레그램 설정들...
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
TELEGRAM_CHAT_ID = "your-telegram-chat-id"
```

#### 5. 저장 및 재시작
- 화면 하단 **"Save"** 버튼 클릭
- 앱이 자동으로 재시작됩니다 (약 1~2분 소요)

#### 6. 확인
- 앱이 재시작되면 https://poscointlwh.streamlit.app/ 새로고침
- "이슈발생보고 생성" 기능 테스트
- 더 상세하고 정확한 분석 결과 확인

---

## 📊 모델 비교

### GPT-4o-mini (기존)
- 속도: 빠름
- 비용: 저렴
- 성능: 기본적인 작업에 적합

### GPT-4o (업그레이드 후)
- 속도: 매우 빠름 ⚡
- 성능: 최고 수준 🎯
- 이해력: 향상된 컨텍스트 이해
- 추론: 더 정확한 분석
- 비용: 약간 상승 (하지만 성능 대비 합리적)

**비용:**
- 입력: $2.50 / 1M 토큰
- 출력: $10.00 / 1M 토큰
- 일반적인 이슈 보고서 1건: 약 $0.05~0.10

---

## 🎯 개선되는 기능

### 1. 이슈발생보고 생성
- ✅ 더 심층적인 리스크 분석
- ✅ 더 구체적인 대응 전략
- ✅ 더 자연스러운 문장 구성

### 2. 언론 대응 제안
- ✅ 더 세련된 언론 대응 문구
- ✅ 상황별 맞춤 전략
- ✅ 더 정확한 톤앤매너

### 3. 카카오톡 메시지
- ✅ 더 간결하고 명확한 표현
- ✅ 핵심 정보 강조
- ✅ 긴급도에 따른 적절한 문구

---

## ⚠️ 주의사항

1. **API 키 확인**: OpenAI API 키에 충분한 크레딧이 있는지 확인
2. **비용 모니터링**: https://platform.openai.com/usage 에서 사용량 확인
3. **테스트 후 적용**: 먼저 로컬에서 테스트한 후 프로덕션 적용 권장

---

## 🔧 트러블슈팅

### "insufficient_quota" 에러
→ OpenAI API 크레딧이 부족합니다. 결제 정보를 확인하세요.

### "rate_limit" 에러
→ API 요청 한도 초과. 잠시 후 다시 시도하세요.

### 앱이 재시작되지 않음
→ Settings 페이지에서 "Reboot app" 버튼을 수동으로 클릭하세요.

---

## 📞 문의

문제가 발생하면:
1. Streamlit Cloud 로그 확인 (Settings > Logs)
2. OpenAI API 사용량 확인
3. IT 지원팀 문의
