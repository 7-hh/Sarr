from datetime import datetime, timedelta
from secrets import token_hex

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import ChatException, MemoryRule, RoleEnum, SubscriptionKey, User, UserPreference, UserSession


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, telegram_id: int, username: str | None, full_name: str | None) -> User:
        user = await self.session.get(User, telegram_id)
        if user:
            user.username = username
            user.full_name = full_name
            await self.session.commit()
            return user

        role = RoleEnum.OWNER if telegram_id == settings.owner_id else RoleEnum.USER
        if telegram_id in settings.admin_ids and role != RoleEnum.OWNER:
            role = RoleEnum.ADMIN
        user = User(id=telegram_id, username=username, full_name=full_name, role=role)
        self.session.add(user)
        try:
            await self.session.commit()
        except IntegrityError:
            # Another concurrent update inserted the same user first.
            await self.session.rollback()
            user = await self.session.get(User, telegram_id)
            if not user:
                raise
            user.username = username
            user.full_name = full_name
            await self.session.commit()
            return user
        await self.session.refresh(user)
        return user

    async def get(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def list_all(self) -> list[User]:
        result = await self.session.execute(select(User))
        return list(result.scalars().all())


class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, user_id: int, encrypted_session: str, phone_number: str | None) -> UserSession:
        result = await self.session.execute(select(UserSession).where(UserSession.user_id == user_id))
        row = result.scalar_one_or_none()
        if row:
            row.encrypted_session = encrypted_session
            row.phone_number = phone_number
            row.is_active = True
        else:
            row = UserSession(
                user_id=user_id,
                encrypted_session=encrypted_session,
                phone_number=phone_number,
                is_active=True,
            )
            self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def deactivate(self, user_id: int) -> None:
        result = await self.session.execute(select(UserSession).where(UserSession.user_id == user_id))
        row = result.scalar_one_or_none()
        if row:
            row.is_active = False
            await self.session.commit()

    async def get_active(self) -> list[UserSession]:
        result = await self.session.execute(select(UserSession).where(UserSession.is_active.is_(True)))
        return list(result.scalars().all())

    async def get_by_user(self, user_id: int) -> UserSession | None:
        result = await self.session.execute(select(UserSession).where(UserSession.user_id == user_id))
        return result.scalar_one_or_none()


class MemoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, trigger: str, response: str) -> MemoryRule:
        row = MemoryRule(user_id=user_id, trigger=trigger, response=response)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def remove(self, memory_id: int, user_id: int) -> bool:
        stmt = delete(MemoryRule).where(MemoryRule.id == memory_id, MemoryRule.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def list_for_user(self, user_id: int) -> list[MemoryRule]:
        result = await self.session.execute(select(MemoryRule).where(MemoryRule.user_id == user_id))
        return list(result.scalars().all())


class KeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, days: int, count: int = 1) -> list[SubscriptionKey]:
        keys = []
        for _ in range(count):
            code = f"SAIR-{days}D-{token_hex(8).upper()}"
            key = SubscriptionKey(key=code, days=days)
            keys.append(key)
            self.session.add(key)
        await self.session.commit()
        return keys

    async def delete(self, key: str) -> bool:
        result = await self.session.execute(delete(SubscriptionKey).where(SubscriptionKey.key == key))
        await self.session.commit()
        return result.rowcount > 0

    async def activate(self, key: str, user: User) -> bool:
        result = await self.session.execute(select(SubscriptionKey).where(SubscriptionKey.key == key))
        row = result.scalar_one_or_none()
        if not row or row.is_used:
            return False
        row.is_used = True
        row.used_by = user.id
        row.used_at = datetime.utcnow()
        user.role = RoleEnum.VIP
        base = user.subscription_expires_at if user.subscription_expires_at > datetime.utcnow() else datetime.utcnow()
        user.subscription_expires_at = base + timedelta(days=row.days)
        await self.session.commit()
        return True


class ExceptionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, peer_id: int) -> ChatException:
        row = ChatException(user_id=user_id, peer_id=peer_id)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def list_for_user(self, user_id: int) -> list[ChatException]:
        result = await self.session.execute(select(ChatException).where(ChatException.user_id == user_id))
        return list(result.scalars().all())


class PreferenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int) -> UserPreference:
        row = await self.session.get(UserPreference, user_id)
        if row:
            return row
        row = UserPreference(user_id=user_id)
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def set_forward_group(self, user_id: int, group_id: int) -> None:
        row = await self.get_or_create(user_id)
        row.forward_group_id = group_id
        await self.session.commit()

    async def set_trigger_word(self, user_id: int, trigger_word: str) -> None:
        row = await self.get_or_create(user_id)
        row.trigger_word = trigger_word
        await self.session.commit()
