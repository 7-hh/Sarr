from collections import defaultdict, deque
from time import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from config import settings


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.user_hits: dict[int, deque[float]] = defaultdict(deque)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        now = time()
        queue = self.user_hits[user_id]
        while queue and now - queue[0] > settings.rate_limit_seconds:
            queue.popleft()

        if len(queue) >= settings.rate_limit_messages:
            return await event.answer("تم تقييدك مؤقتًا بسبب كثافة الرسائل. Powered by SAIR AI")

        queue.append(now)
        return await handler(event, data)
