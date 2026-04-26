from services.cache import redis_client


class RuntimeSettingsService:
    async def is_system_enabled(self) -> bool:
        value = await redis_client.get("system:enabled")
        return value != "0"

    async def set_system_enabled(self, enabled: bool) -> None:
        await redis_client.set("system:enabled", "1" if enabled else "0")

    async def get_force_channel(self, default_channel: str) -> str:
        return await redis_client.get("system:force_channel") or default_channel

    async def set_force_channel(self, channel: str) -> None:
        await redis_client.set("system:force_channel", channel)


runtime_settings = RuntimeSettingsService()
