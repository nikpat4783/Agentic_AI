import json

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse

from app.agent.orchestrator import run_agentic_rag
from app.domains.config import get_domain
from app.models import User
from app.schemas import ResearchRequest
from app.security import get_current_user

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/stream")
async def research_stream(
    payload: ResearchRequest,
    x_groq_key: str = Header(..., alias="X-Groq-Key"),
    _current_user: User = Depends(get_current_user),
):
    if get_domain(payload.domain_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown domain")
    if not x_groq_key.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Groq API key")

    async def event_stream():
        async for event in run_agentic_rag(
            question=payload.question,
            domain_id=payload.domain_id,
            model=payload.model,
            api_key=x_groq_key,
            session_id=payload.session_id,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
