from aiogram import Bot

from config import settings


async def send_log(bot: Bot, text: str) -> None:
    try:
        await bot.send_message(settings.log_group_id, text)
    except Exception:
        pass
