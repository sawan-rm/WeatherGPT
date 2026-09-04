from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=hashed_password,
        preferred_language=user.preferred_language,
        location_lat=user.location_lat,
        location_lng=user.location_lng,
        user_type=user.user_type,
        crop_types=user.crop_types
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
