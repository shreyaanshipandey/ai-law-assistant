import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import TokenError, safe_decode
from app.db.database import AsyncSessionLocal, get_db
from app.models.case import ChatSession
from app.models.user import User
from app.schemas.chat import ChatMessageIn, ChatMessageOut, ChatSessionOut
from app.services.ai_service import chat_reply

router = APIRouter(prefix="/chat", tags=["Legal AI Chatbot"])


async def _get_or_create_session(db: AsyncSession, user: User, session_id: uuid.UUID | None) -> ChatSession:
    if session_id:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found.")
        return session

    session = ChatSession(user_id=user.id, title="New conversation", messages=[])
    db.add(session)
    await db.flush()
    return session


@router.post("/message", response_model=ChatMessageOut)
async def send_message(
    payload: ChatMessageIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = await _get_or_create_session(db, current_user, payload.session_id)
    history = session.messages or []

    reply, referenced = await chat_reply(history, payload.message)

    now = datetime.now(timezone.utc).isoformat()
    updated_messages = history + [
        {"role": "user", "content": payload.message, "ts": now},
        {"role": "assistant", "content": reply, "ts": now},
    ]
    session.messages = updated_messages
    if session.title == "New conversation":
        session.title = payload.message[:60]

    await db.commit()
    await db.refresh(session)

    return ChatMessageOut(session_id=session.id, reply=reply, referenced_sections=referenced)


@router.get("/sessions", response_model=list[ChatSessionOut])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.user_id == current_user.id).order_by(ChatSession.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return session


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket, token: str):
    """
    WebSocket-based conversational endpoint.
    Client connects to: ws://<host>/api/v1/chat/ws?token=<JWT access token>
    Then sends JSON: {"session_id": "<uuid|null>", "message": "..."}
    Receives JSON: {"session_id": "...", "reply": "...", "referenced_sections": [...]}
    """
    try:
        payload = safe_decode(token)
        user_id = uuid.UUID(payload["sub"])
    except (TokenError, KeyError, ValueError):
        await websocket.close(code=4401)
        return

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message_text = data.get("message", "")
            session_id_raw = data.get("session_id")
            session_id = uuid.UUID(session_id_raw) if session_id_raw else None

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()
                if not user or not user.is_active:
                    await websocket.send_json({"error": "Unauthorized"})
                    continue

                session = await _get_or_create_session(db, user, session_id)
                history = session.messages or []
                reply, referenced = await chat_reply(history, message_text)

                now = datetime.now(timezone.utc).isoformat()
                session.messages = history + [
                    {"role": "user", "content": message_text, "ts": now},
                    {"role": "assistant", "content": reply, "ts": now},
                ]
                if session.title == "New conversation":
                    session.title = message_text[:60]
                await db.commit()
                await db.refresh(session)

            await websocket.send_json(
                {"session_id": str(session.id), "reply": reply, "referenced_sections": referenced}
            )
    except WebSocketDisconnect:
        pass
