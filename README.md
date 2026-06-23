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

## 무료 배포 (Render)

GitHub 레포가 연결돼 있으면 `render.yaml`로 거의 자동 배포됩니다.

1. https://render.com 가입 (GitHub 계정으로) → **New → Blueprint**
2. 이 레포(`modacapitest`)를 선택하면 `render.yaml`을 자동 인식합니다.
3. 환경변수 입력 (대시보드에서):
   - `ANTHROPIC_API_KEY` — Anthropic 키
   - `OPENAI_API_KEY` — OpenAI 키
   - `APP_PASSWORD` — 사이트 입장 비밀번호 (원하는 값)
   - `OPENAI_MODEL` — 기본 `gpt-4o` (그대로 두면 됨)
4. 배포 완료 후 `https://<서비스이름>.onrender.com` 으로 접속 → 비밀번호 입력 후 사용.

> 무료 플랜은 15분간 요청이 없으면 잠들고, 다음 접속 시 깨어나며 약 30초 정도 걸립니다.
> `APP_PASSWORD`를 설정하면 그 비밀번호를 아는 사람만 사용할 수 있어 API 키 악용을 막습니다.

## 메모
- 두 API는 병렬로 호출됩니다. 한쪽 키만 있어도 그쪽 결과는 나옵니다(없는 쪽 패널엔 안내 표시).
- Claude 모델: `claude-opus-4-8` (고정)
- OpenAI 모델: `.env`의 `OPENAI_MODEL` (기본 `gpt-4o`) — 계정에서 더 높은 모델이 열리면 이 값만 바꾸면 됩니다.
- 키는 백엔드(`.env`)에만 있고 브라우저에는 노출되지 않습니다.
