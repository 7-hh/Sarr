from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy import BigInteger, Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RoleEnum(str, Enum):
    USER = "user"
    VIP = "vip"
    ADMIN = "admin"
    OWNER = "owner"


class ReplyModeEnum(str, Enum):
    AI = "ai"
    FIXED = "fixed"
    AWAY = "away"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(128))
    full_name: Mapped[str | None] = mapped_column(String(256))
    role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum), default=RoleEnum.USER)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_reply_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reply_mode: Mapped[ReplyModeEnum] = mapped_column(SAEnum(ReplyModeEnum), default=ReplyModeEnum.AI)
    persona_prompt: Mapped[str] = mapped_column(
        Text,
        default="سائر... أنا ظلّ فكرةٍ يتكلم حين يغيب صاحب الحساب.",
    )
    away_message: Mapped[str] = mapped_column(
        Text,
        default="سائر... أنا الآن بعيد قليلًا. سأعود عندما يهدأ الضجيج.",
    )
    exclude_groups: Mapped[bool] = mapped_column(Boolean, default=True)
    subscription_expires_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow() + timedelta(days=1)
    )
    daily_used_messages: Mapped[int] = mapped_column(Integer, default=0)
    daily_reset_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    session: Mapped["UserSession"] = relationship(back_populates="user", uselist=False)
    memories: Mapped[list["MemoryRule"]] = relationship(back_populates="user")
    exceptions: Mapped[list["ChatException"]] = relationship(back_populates="user")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(32))
    encrypted_session: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="session")


class SubscriptionKey(Base):
    __tablename__ = "subscription_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    days: Mapped[int] = mapped_column(Integer)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_by: Mapped[int | None] = mapped_column(BigInteger)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MemoryRule(Base):
    __tablename__ = "memory_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    trigger: Mapped[str] = mapped_column(String(256))
    response: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="memories")


class ChatException(Base):
    __tablename__ = "chat_exceptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    peer_id: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="exceptions")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    forward_group_id: Mapped[int | None] = mapped_column(BigInteger)
    trigger_word: Mapped[str] = mapped_column(String(128), default="رد")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
