from datetime import datetime

from pyrogram import Client
from pyrogram.types import Message

from ai_engine import ai_engine
from database.connection import SessionLocal
from database.models import ReplyModeEnum
from database.repositories import ExceptionRepository, MemoryRepository, PreferenceRepository, UserRepository
from subscription import subscription_service


class AutoReplyEngine:
    async def build_reply(self, owner_id: int, incoming_text: str) -> str | None:
        async with SessionLocal() as session:
            user_repo = UserRepository(session)
            memory_repo = MemoryRepository(session)
            pref_repo = PreferenceRepository(session)
            owner = await user_repo.get(owner_id)
            if not owner or not owner.auto_reply_enabled or owner.is_banned:
                return None

            if not subscription_service.has_subscription(owner):
                return None

            if not subscription_service.can_send(owner):
                return "سائر... وصلت لحد الرسائل اليومي. Powered by SAIR AI"

            memory_hit = await memory_repo.list_for_user(owner_id)
            for rule in memory_hit:
                if rule.trigger.lower() in incoming_text.lower():
                    owner.daily_used_messages += 1
                    await session.commit()
                    return rule.response

            pref = await pref_repo.get_or_create(owner_id)
            trigger = (pref.trigger_word or "").strip().lower()
            if trigger and trigger not in incoming_text.lower():
                return None

            if owner.reply_mode == ReplyModeEnum.FIXED:
                owner.daily_used_messages += 1
                await session.commit()
                return owner.away_message

            if owner.reply_mode == ReplyModeEnum.AWAY:
                if datetime.utcnow().hour < 8:
                    owner.daily_used_messages += 1
                    await session.commit()
                    return owner.away_message
                return None

            owner.daily_used_messages += 1
            await session.commit()
            return await ai_engine.generate_reply(owner.persona_prompt, incoming_text)

    async def on_private_message(self, app: Client, owner_id: int, message: Message) -> None:
        if not message.text or message.outgoing or message.from_user is None:
            return
        if message.chat.id == owner_id:
            return
        if message.chat.type.value != "private":
            return

        async with SessionLocal() as session:
            exceptions_repo = ExceptionRepository(session)
            pref_repo = PreferenceRepository(session)
            blocked_peers = await exceptions_repo.list_for_user(owner_id)
            if any(exc.peer_id == message.chat.id for exc in blocked_peers):
                return
            pref = await pref_repo.get_or_create(owner_id)
            if pref.forward_group_id:
                try:
                    await app.forward_messages(pref.forward_group_id, message.chat.id, message.id)
                except Exception:
                    pass

        reply_text = await self.build_reply(owner_id, message.text)
        if reply_text:
            await message.reply(reply_text)


auto_reply_engine = AutoReplyEngine()
