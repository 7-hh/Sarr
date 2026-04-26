from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.connection import SessionLocal
from database.repositories import UserRepository


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        aiogram_user = data.get("event_from_user")
        if aiogram_user:
            async with SessionLocal() as session:
                repo = UserRepository(session)
                db_user = await repo.get_or_create(
                    telegram_id=aiogram_user.id,
                    username=aiogram_user.username,
                    full_name=aiogram_user.full_name,
                )
                data["db_user"] = db_user
        return await handler(event, data)
