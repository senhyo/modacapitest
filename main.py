import asyncio
import base64
import os

from anthropic import AsyncAnthropic
from dotenv import load_dotenv
from fastapi import FastAPI, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI

load_dotenv()

CLAUDE_MODEL = "claude-opus-4-8"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
DEFAULT_PROMPT = "이 이미지를 자세히 설명해줘."

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
APP_PASSWORD = os.getenv("APP_PASSWORD")  # 설정되면 /interpret 호출에 비밀번호 필요

anthropic_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = FastAPI()


async def interpret_with_claude(image_b64: str, media_type: str, prompt: str, model: str) -> str:
    """Claude로 이미지를 해석한다. 실패 시 예외를 그대로 올린다."""
    if anthropic_client is None:
        raise RuntimeError("ANTHROPIC_API_KEY가 설정되지 않았습니다 (.env 확인).")

    response = await anthropic_client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    return "".join(block.text for block in response.content if block.type == "text")


async def interpret_with_openai(image_b64: str, media_type: str, prompt: str, model: str) -> str:
    """OpenAI로 이미지를 해석한다. 실패 시 예외를 그대로 올린다."""
    if openai_client is None:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다 (.env 확인).")

    response = await openai_client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{image_b64}"},
                    },
                ],
            }
        ],
    )
    return response.choices[0].message.content or ""


async def run_safely(coro):
    """코루틴을 실행하고 (text, error) 형태로 결과를 정규화한다."""
    try:
        return {"text": await coro, "error": None}
    except Exception as exc:  # 한쪽 실패가 다른 쪽을 막지 않도록 격리
        return {"text": None, "error": f"{type(exc).__name__}: {exc}"}


def check_password(password: str) -> bool:
    """APP_PASSWORD가 설정돼 있으면 일치해야 한다. 미설정이면 게이트 없음(로컬용)."""
    if not APP_PASSWORD:
        return True
    return password == APP_PASSWORD


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/config")
async def config():
    """프론트가 비밀번호 게이트가 켜져 있는지 알 수 있게 한다."""
    return {"auth_required": bool(APP_PASSWORD)}


@app.get("/openai-models")
async def openai_models():
    """이 계정에서 사용 가능한 OpenAI 모델 ID 목록을 반환한다."""
    if openai_client is None:
        return {"models": [], "error": "OPENAI_API_KEY가 설정되지 않았습니다."}
    try:
        resp = await openai_client.models.list()
        ids = sorted(m.id for m in resp.data)
        return {"models": ids}
    except Exception as exc:
        return {"models": [], "error": f"{type(exc).__name__}: {exc}"}


@app.post("/auth")
async def auth(password: str = Form("")):
    """비밀번호만 검증한다 (입장 화면용)."""
    if check_password(password):
        return {"ok": True}
    return JSONResponse(status_code=401, content={"ok": False, "detail": "비밀번호가 올바르지 않습니다."})


@app.post("/interpret")
async def interpret(
    image: UploadFile,
    prompt: str = Form(DEFAULT_PROMPT),
    claude_model: str = Form(CLAUDE_MODEL),
    openai_model: str = Form(OPENAI_MODEL),
    password: str = Form(""),
):
    if not check_password(password):
        return JSONResponse(status_code=401, content={"detail": "비밀번호가 올바르지 않습니다."})

    raw = await image.read()
    if not raw:
        return JSONResponse(status_code=400, content={"detail": "이미지가 비어 있습니다."})

    image_b64 = base64.standard_b64encode(raw).decode("utf-8")
    media_type = image.content_type or "image/png"
    prompt = (prompt or DEFAULT_PROMPT).strip()
    claude_model = (claude_model or CLAUDE_MODEL).strip()
    openai_model = (openai_model or OPENAI_MODEL).strip()

    claude_result, openai_result = await asyncio.gather(
        run_safely(interpret_with_claude(image_b64, media_type, prompt, claude_model)),
        run_safely(interpret_with_openai(image_b64, media_type, prompt, openai_model)),
    )

    return {
        "claude": {"model": claude_model, **claude_result},
        "openai": {"model": openai_model, **openai_result},
    }


app.mount("/static", StaticFiles(directory="static"), name="static")
