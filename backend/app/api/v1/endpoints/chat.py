"""Chat endpoints with issue-specific Q&A."""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel

from app.db.base import get_db
from app.api.deps import get_current_citizen

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


@router.post("/issue/{issue_id}")
def chat_about_issue(
    issue_id: UUID,
    body: ChatRequest,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Answer citizen question about a specific issue.
    
    Uses stored narrative summary + timeline as context.
    """
    from app.agents.narrative_agent import answer_issue_query
    
    result = answer_issue_query(issue_id, body.question)
    
    if "error" in result and result["error"]:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return {
        "answer": result["answer"],
        "issue_id": result["issue_id"],
        "context_used": result["context_used"],
    }


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass


@router.get("/")
def chat_placeholder():
    """Chat API info."""
    return {
        "message": "Chat endpoints available",
        "issue_chat": "POST /api/v1/chat/issue/{issue_id}",
        "websocket": "WS /api/v1/chat/ws",
    }
