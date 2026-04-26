import asyncio
import logging

from pyrogram import Client
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from config import settings
from database.connection import SessionLocal
from database.repositories import SessionRepository, UserRepository
from services import ProxyManager, decrypt_session
from userbot.auto_reply import auto_reply_engine


logger = logging.getLogger(__name__)


class UserbotSessionManager:
    def __init__(self) -> None:
        self.clients: dict[int, Client] = {}
        self.tasks: dict[int, asyncio.Task] = {}
        self.proxy_manager = ProxyManager()

    async def _run_single(self, user_id: int, session_string: str) -> None:
        proxy = self.proxy_manager.next_proxy()
        app = Client(
            name=f"user_{user_id}",
            api_id=2040,
            api_hash="b18441a1ff607e10a989891a5462e627",
            session_string=session_string,
            no_updates=False,
            proxy={"scheme": "socks5", "hostname": proxy.split(":")[0], "port": int(proxy.split(":")[1])}
            if proxy and ":" in proxy
            else None,
        )

        async def _handler(client: Client, message: Message) -> None:
            await auto_reply_engine.on_private_message(client, user_id, message)

        app.add_handler(MessageHandler(_handler))
        try:
            await app.start()
            self.clients[user_id] = app
            logger.info("Userbot connected for user_id=%s", user_id)
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.exception("Session crashed for %s: %s", user_id, exc)
        finally:
            self.clients.pop(user_id, None)
            try:
                await app.stop()
            except Exception:
                pass

    async def start_all(self) -> None:
        async with SessionLocal() as session:
            repo = SessionRepository(session)
            user_repo = UserRepository(session)
            rows = await repo.get_active()
            for row in rows:
                user = await user_repo.get(row.user_id)
                if not user:
                    continue
                if user.subscription_expires_at.timestamp() <= __import__("time").time():
                    await repo.deactivate(row.user_id)
                    continue
                if row.encrypted_session and row.user_id not in self.tasks:
                    decrypted = decrypt_session(row.encrypted_session)
                    uid = row.user_id
                    task = asyncio.create_task(self._run_single(row.user_id, decrypted))
                    task.add_done_callback(lambda _, user_id=uid: self.tasks.pop(user_id, None))
                    self.tasks[uid] = task

    async def stop_all(self) -> None:
        for task in self.tasks.values():
            task.cancel()
        for client in self.clients.values():
            try:
                await client.stop()
            except Exception:
                pass
        self.clients.clear()
        self.tasks.clear()


session_manager = UserbotSessionManager()
