import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatMessageIn(BaseModel):
    session_id: uuid.UUID | None = None
    message: str


class ChatMessageOut(BaseModel):
    session_id: uuid.UUID
    reply: str
    referenced_sections: list[str] = []


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    messages: list[dict]
    created_at: datetime
    updated_at: datetime
