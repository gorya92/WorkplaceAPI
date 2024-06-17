
from fastapi import APIRouter, Depends

from firebase_admin import messaging
from sqlalchemy.ext.asyncio import AsyncSession
from ..auth.base_config import current_user
from ..database import get_async_session


router = APIRouter(prefix="/report")


images = []


@router.get("/token")
async def set_device_token(token: str, user=Depends(current_user), session: AsyncSession = Depends(get_async_session)):
    user.device_token = token
    async with session:
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return {
        "status": 200,
        "data": "Token has been changed",
        "details": None
    }


