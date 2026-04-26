from database.repositories import MemoryRepository


class MemoryEngine:
    async def maybe_reply(self, memory_repo: MemoryRepository, user_id: int, incoming: str) -> str | None:
        rules = await memory_repo.list_for_user(user_id)
        text = incoming.lower()
        for rule in rules:
            if rule.trigger.lower() in text:
                return rule.response
        return None


memory_engine = MemoryEngine()
