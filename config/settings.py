from functools import cached_property
from typing import List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    owner_id: int = Field(alias="OWNER_ID")
    bot_username: str = Field(alias="BOT_USERNAME")
    admin_ids_raw: str = Field(alias="ADMIN_IDS")
    force_subscribe_channel: str = Field(alias="FORCE_SUBSCRIBE_CHANNEL")
    log_group_id: int = Field(alias="LOG_GROUP_ID")
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    ai_model: str = Field(alias="AI_MODEL")
    bot_mode: str = Field(alias="BOT_MODE")

    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    database_url: str = Field(alias="DATABASE_URL")
    redis_password: str = Field(alias="REDIS_PASSWORD")
    redis_url: str = Field(alias="REDIS_URL")

    rate_limit_messages: int = Field(alias="RATE_LIMIT_MESSAGES")
    rate_limit_seconds: int = Field(alias="RATE_LIMIT_SECONDS")
    flood_ban_threshold: int = Field(alias="FLOOD_BAN_THRESHOLD")
    flood_ban_duration: int = Field(alias="FLOOD_BAN_DURATION")

    bot_name: str = Field(alias="BOT_NAME")
    bot_tagline: str = Field(alias="BOT_TAGLINE")
    free_daily_limit: int = Field(alias="FREE_DAILY_LIMIT")
    vip_daily_limit: int = Field(alias="VIP_DAILY_LIMIT")

    session_secret_key: str = "SAIR_SESSION_SECRET_32BYTE_KEY_CHANGE_ME"

    @computed_field
    @property
    def admin_ids(self) -> List[int]:
        ids = [int(item.strip()) for item in self.admin_ids_raw.split(",") if item.strip()]
        if self.owner_id not in ids:
            ids.append(self.owner_id)
        return ids

    @cached_property
    def is_ai_mode(self) -> bool:
        return self.bot_mode.lower() == "ai"


settings = Settings()
