from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.chat import ChatSession, Message
from app.schemas.chat import MessageCreate

async def create_chat_session(db: AsyncSession, user_id: int):
    session = ChatSession(user_id=user_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session

async def add_message(db: AsyncSession, session_id: int, message: MessageCreate):
    db_msg = Message(
        session_id=session_id,
        role=message.role,
        content=message.content,
        metadata_json=message.metadata_json
    )
    db.add(db_msg)
    await db.commit()
    await db.refresh(db_msg)
    return db_msg

async def get_session_messages(db: AsyncSession, session_id: int):
    result = await db.execute(
        select(Message).filter(Message.session_id == session_id).order_by(Message.timestamp)
    )
    return result.scalars().all()
