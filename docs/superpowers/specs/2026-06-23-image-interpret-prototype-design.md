# 이미지 해석 프로토타입 설계

## 목적
사진 1장을 업로드하면 Claude와 OpenAI가 각각 어떻게 해석하는지 나란히 비교해서 보여주는 localhost 프로토타입.

## 전체 구조
- FastAPI 앱 하나 (`main.py`), `uvicorn main:app`로 `localhost:8000` 실행.
- 역할 두 가지:
  1. `GET /` — 이미지 업로드 UI(HTML 한 장) 서빙
  2. `POST /interpret` — 이미지 + 프롬프트를 받아 Claude·OpenAI를 **동시에(병렬)** 호출하고 두 해석을 JSON으로 반환
- API 키는 코드가 아닌 `.env`에서 읽음. 키는 백엔드에만 머무르고 브라우저에는 노출되지 않음.

## 데이터 흐름
1. 브라우저에서 이미지 선택 + 프롬프트 입력 (기본 프롬프트가 미리 채워져 있고 수정 가능)
2. 이미지를 base64로 인코딩 + 프롬프트를 `POST /interpret`로 전송
3. 백엔드가 Claude(`claude-opus-4-8`)와 OpenAI(`OPENAI_MODEL`)에 같은 이미지·프롬프트를 병렬 호출 (`asyncio.gather`)
4. 두 응답 텍스트를 받아 화면에 좌우 패널로 나란히 표시

## 파일 구성
- `main.py` — FastAPI 앱 + 두 API 호출 로직 (async)
- `static/index.html` — 업로드 폼 + 결과 패널 (CSS/JS 인라인, 외부 의존성 없음)
- `requirements.txt` — fastapi, uvicorn, anthropic, openai, python-dotenv, python-multipart
- `.env.example` — 키 양식 (실제 `.env`는 사용자가 채움)
- `README.md` — 실행 방법

## 모델
- Claude: `claude-opus-4-8` 고정 (Anthropic 공식 SDK, base64 이미지 입력)
- OpenAI: `OPENAI_MODEL` 환경변수, 기본값 `gpt-4o` (비전 지원). 계정에서 더 높은 모델이 열리면 `.env`만 수정.

## 에러 처리
- 두 API 호출은 서로 독립. 한쪽이 실패해도 다른 쪽 결과는 정상 표시.
- 실패한 패널에는 에러 메시지 표시(키 누락, 호출 실패 등).
- 키가 아예 없으면 해당 패널에 "키가 설정되지 않음" 안내.

## 키 관리
- `python-dotenv`로 `.env` 로드.
- `.env`는 `.gitignore`에 포함(키 유출 방지), `.env.example`만 공유.
