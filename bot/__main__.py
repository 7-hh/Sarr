import asyncio
import logging
from datetime import datetime

import uvloop
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from config import settings
from database.connection import SessionLocal, engine
from database.models import Base
from database.repositories import SessionRepository, UserRepository
from handlers import admin_router, chat_router, session_router, user_router
from middlewares import UserMiddleware
from security import RateLimitMiddleware
from services.cache import redis_client
from userbot import session_manager


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def subscription_watcher() -> None:
    while True:
        await asyncio.sleep(60)
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            sess_repo = SessionRepository(session)
            users = await user_repo.list_all()
            for user in users:
                if user.role.value in {"admin", "owner"}:
                    continue
                if user.subscription_expires_at <= datetime.utcnow():
                    await sess_repo.deactivate(user.id)


async def main() -> None:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    await create_tables()
    await session_manager.start_all()

    storage = RedisStorage(redis=redis_client)
    dp = Dispatcher(storage=storage)
    dp.message.middleware(UserMiddleware())
    dp.message.middleware(RateLimitMiddleware())

    dp.include_router(user_router)
    dp.include_router(session_router)
    dp.include_router(chat_router)
    dp.include_router(admin_router)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    watcher = asyncio.create_task(subscription_watcher())
    try:
        logger.info("Bot started.")
        await dp.start_polling(bot)
    finally:
        watcher.cancel()
        await session_manager.stop_all()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
