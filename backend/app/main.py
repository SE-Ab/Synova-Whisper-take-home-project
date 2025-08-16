import httpx
import json
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings
from app.audit import AuditLogger
from app.crypto import sha256_hash

class Settings(BaseSettings):
    SIGNER_ID: str
    SIGNING_KEY_PATH: str
    OPENAI_API_URL: str

    GROQ_API_KEY: str = "not_set" 
    AUDIT_LOG_FILE: str = "/app/audit_data/audit.jsonl"

settings = Settings()
app = FastAPI()

origins = ["http://localhost", "http://localhost:8080"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

audit_logger = AuditLogger(
    log_file=settings.AUDIT_LOG_FILE,
    key_path=settings.SIGNING_KEY_PATH,
    signer_id=settings.SIGNER_ID
)

@app.get("/api/key")
async def get_api_key():
    """Provides the pre-configured API key to the frontend."""
    return JSONResponse(content={"apiKey": settings.GROQ_API_KEY})

async def stream_generator(request: Request, request_body: dict, request_id: str):
    full_response_content = b""
    is_success = False
    async with httpx.AsyncClient(timeout=300) as client:
        headers = {"Authorization": request.headers.get("Authorization"), "Content-Type": "application/json"}
        try:
            async with client.stream("POST", settings.OPENAI_API_URL, json=request_body, headers=headers) as response:
                if response.status_code != 200:
                    error_content = await response.aread()
                    error_data = json.loads(error_content.decode())
                    error_event = {"event": "error", "data": error_data}
                    yield f"data: {json.dumps(error_event)}\n\n".encode()
                    is_success = False
                else:
                    is_success = True
                    async for chunk in response.aiter_bytes():
                        yield chunk
                        full_response_content += chunk
                        if b'data: ' in chunk and not chunk.strip().endswith(b"data: [DONE]"):
                            chunk_hash = sha256_hash(chunk)
                            rem_chunk_event = {"event": "rem.chunk", "data": {"sha256": chunk_hash}}
                            yield f"data: {json.dumps(rem_chunk_event)}\n\n".encode()
        except httpx.RequestError as e:
            error_event = {"event": "error", "data": {"error": {"message": f"Connection error to upstream API: {e}"}}}
            yield f"data: {json.dumps(error_event)}\n\n".encode()
            is_success = False
    if is_success:
        final_hash = sha256_hash(full_response_content)
        rem_manifest = {"event": "rem.manifest", "data": {"final_sha256": final_hash, "signer_id": settings.SIGNER_ID}}
        yield f"data: {json.dumps(rem_manifest)}\n\n".encode()
        audit_logger.log(request_id, request_body, full_response_content)

@app.post("/proxy/openai/v1/chat/completions")
async def proxy_openai(request: Request):
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    try:
        request_body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    if request_body.get("stream", False):
        return StreamingResponse(stream_generator(request, request_body, request_id), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient(timeout=120) as client:
            headers = {"Authorization": request.headers.get("Authorization"), "Content-Type": "application/json"}
            response = await client.post(settings.OPENAI_API_URL, json=request_body, headers=headers)
            response_body = await response.aread()
            if response.status_code == 200:
                audit_logger.log(request_id, request_body, response_body)
            return StreamingResponse(iter([response_body]), status_code=response.status_code, media_type=response.headers.get("content-type"))