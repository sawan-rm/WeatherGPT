from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class MessageCreate(BaseModel):
    role: str
    content: str
    metadata_json: Optional[Any] = None

class MessageResponse(MessageCreate):
    id: int
    session_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    started_at: datetime
    messages: list[MessageResponse] = []

    class Config:
        from_attributes = True
