from aiogram import F, Router
from aiogram.types import Message

from config import settings
from database.connection import SessionLocal
from database.models import ReplyModeEnum
from database.repositories import KeyRepository, MemoryRepository, SessionRepository, UserRepository
from services import runtime_settings

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(F.text == "/admin")
async def admin_panel(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "لوحة الإدارة:\n"
        "/stats\n/sessions\n/broadcast نص\n/addkey <days> [count]\n/delkey <key>\n"
        "/ban <id>\n/unban <id>\n/setmode <ai|fixed|away>\n/setchannel @channel\n/setlog -100...\n"
        "/boton\n/botoff\n"
        "/addmemory <user_id>|<trigger>|<response>\n/delmemory <memory_id> <user_id>\n/listmemory <user_id>"
    )


@router.message(F.text == "/stats")
async def stats_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    async with SessionLocal() as session:
        users = await UserRepository(session).list_all()
        active = [u for u in users if not u.is_banned]
        vip = [u for u in users if u.role.value == "vip"]
    await message.answer(f"Users: {len(users)}\nActive: {len(active)}\nVIP: {len(vip)}\n{settings.bot_tagline}")


@router.message(F.text == "/sessions")
async def sessions_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    async with SessionLocal() as session:
        rows = await SessionRepository(session).get_active()
    await message.answer(f"Active sessions: {len(rows)}\n{settings.bot_tagline}")


@router.message(F.text.startswith("/broadcast"))
async def broadcast_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    payload = message.text.replace("/broadcast", "", 1).strip()
    if not payload:
        await message.answer("استخدم: /broadcast نص الرسالة")
        return
    async with SessionLocal() as session:
        users = await UserRepository(session).list_all()
    delivered = 0
    for user in users:
        try:
            await message.bot.send_message(user.id, f"{payload}\n{settings.bot_tagline}")
            delivered += 1
        except Exception:
            continue
    await message.answer(f"Broadcast sent to {delivered}")


@router.message(F.text.startswith("/addkey"))
async def addkey_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("استخدم: /addkey <days> [count]")
        return
    days = int(parts[1])
    count = int(parts[2]) if len(parts) > 2 else 1
    async with SessionLocal() as session:
        keys = await KeyRepository(session).create(days, count)
    await message.answer("\n".join(key.key for key in keys))


@router.message(F.text.startswith("/delkey"))
async def delkey_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("استخدم: /delkey <key>")
        return
    async with SessionLocal() as session:
        ok = await KeyRepository(session).delete(parts[1])
    await message.answer("Deleted" if ok else "Not found")


@router.message(F.text.startswith("/ban"))
async def ban_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        return
    async with SessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get(int(parts[1]))
        if user:
            user.is_banned = True
            await session.commit()
    await message.answer("User banned.")


@router.message(F.text.startswith("/unban"))
async def unban_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        return
    async with SessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get(int(parts[1]))
        if user:
            user.is_banned = False
            await session.commit()
    await message.answer("User unbanned.")


@router.message(F.text.startswith("/setmode"))
async def setmode_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        return
    mode = parts[1].lower()
    if mode not in {"ai", "fixed", "away"}:
        return
    async with SessionLocal() as session:
        users = await UserRepository(session).list_all()
        for user in users:
            user.reply_mode = ReplyModeEnum(mode)
        await session.commit()
    await message.answer(f"Global mode set to {mode}")


@router.message(F.text.startswith("/setchannel"))
async def setchannel_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("استخدم: /setchannel @channel_username")
        return
    await runtime_settings.set_force_channel(parts[1].strip())
    await message.answer(f"تم تعيين قناة الاشتراك الإجباري إلى {parts[1].strip()}\nحقوق التطوير: @J2J_2")


@router.message(F.text == "/boton")
async def boton_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    await runtime_settings.set_system_enabled(True)
    await message.answer("تم تشغيل النظام بالكامل.\nحقوق التطوير: @J2J_2")


@router.message(F.text == "/botoff")
async def botoff_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    await runtime_settings.set_system_enabled(False)
    await message.answer("تم إيقاف النظام بالكامل.\nحقوق التطوير: @J2J_2")


@router.message(F.text.startswith("/setlog"))
async def setlog_cmd(message: Message) -> None:
    if _is_admin(message.from_user.id):
        await message.answer("عدّل LOG_GROUP_ID داخل .env ثم أعد تشغيل الخدمة.")


@router.message(F.text.startswith("/addmemory"))
async def addmemory_admin_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    payload = message.text.replace("/addmemory", "", 1).strip()
    parts = payload.split("|")
    if len(parts) != 3:
        await message.answer("استخدم: /addmemory <user_id>|<trigger>|<response>")
        return
    user_id, trigger, response = int(parts[0]), parts[1].strip(), parts[2].strip()
    async with SessionLocal() as session:
        row = await MemoryRepository(session).add(user_id, trigger, response)
    await message.answer(f"Memory added: {row.id}")


@router.message(F.text.startswith("/delmemory"))
async def delmemory_admin_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("استخدم: /delmemory <memory_id> <user_id>")
        return
    async with SessionLocal() as session:
        ok = await MemoryRepository(session).remove(int(parts[1]), int(parts[2]))
    await message.answer("Deleted" if ok else "Not found")


@router.message(F.text.startswith("/listmemory"))
async def listmemory_admin_cmd(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        return
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("استخدم: /listmemory <user_id>")
        return
    async with SessionLocal() as session:
        rows = await MemoryRepository(session).list_for_user(int(parts[1]))
    if not rows:
        await message.answer("No memory rules.")
        return
    lines = [f"{row.id}) {row.trigger} -> {row.response}" for row in rows]
    await message.answer("\n".join(lines[:30]))
