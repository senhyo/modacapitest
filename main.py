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


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.post("/interpret")
async def interpret(
    image: UploadFile,
    prompt: str = Form(DEFAULT_PROMPT),
    claude_model: str = Form(CLAUDE_MODEL),
    openai_model: str = Form(OPENAI_MODEL),
):
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
