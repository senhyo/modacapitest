# 이미지 해석 비교 (Claude vs OpenAI)

사진 1장을 올리면 Claude와 OpenAI가 각각 어떻게 해석하는지 나란히 비교해 보여주는 localhost 프로토타입.

## 실행 방법

1. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

2. API 키 설정 — `.env.example`을 복사해 `.env`를 만들고 키를 채웁니다.
   ```bash
   cp .env.example .env
   # .env 를 열어 ANTHROPIC_API_KEY / OPENAI_API_KEY 입력
   ```

3. 서버 실행
   ```bash
   uvicorn main:app --reload
   ```

4. 브라우저에서 http://localhost:8000 접속 → 이미지 선택 → (필요 시 프롬프트 수정) → **해석하기**

## 메모
- 두 API는 병렬로 호출됩니다. 한쪽 키만 있어도 그쪽 결과는 나옵니다(없는 쪽 패널엔 안내 표시).
- Claude 모델: `claude-opus-4-8` (고정)
- OpenAI 모델: `.env`의 `OPENAI_MODEL` (기본 `gpt-4o`) — 계정에서 더 높은 모델이 열리면 이 값만 바꾸면 됩니다.
- 키는 백엔드(`.env`)에만 있고 브라우저에는 노출되지 않습니다.
