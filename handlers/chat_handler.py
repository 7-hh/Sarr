from aiogram import F, Router
from aiogram.types import Message

from database.connection import SessionLocal
from database.repositories import MemoryRepository

router = Router()


@router.message(F.text.startswith("/addmemory"))
async def add_memory_user(message: Message) -> None:
    payload = message.text.replace("/addmemory", "", 1).strip()
    parts = payload.split("|")
    if len(parts) != 2:
        await message.answer("استخدم: /addmemory trigger|response\nPowered by SAIR AI")
        return
    async with SessionLocal() as session:
        row = await MemoryRepository(session).add(message.from_user.id, parts[0].strip(), parts[1].strip())
    await message.answer(f"تمت إضافة القاعدة رقم {row.id}\nPowered by SAIR AI")


@router.message(F.text.startswith("/delmemory"))
async def del_memory_user(message: Message) -> None:
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("استخدم: /delmemory <id>\nPowered by SAIR AI")
        return
    async with SessionLocal() as session:
        ok = await MemoryRepository(session).remove(int(parts[1]), message.from_user.id)
    await message.answer("تم الحذف.\nPowered by SAIR AI" if ok else "العنصر غير موجود.\nPowered by SAIR AI")


@router.message(F.text == "/listmemory")
async def list_memory_user(message: Message) -> None:
    async with SessionLocal() as session:
        rows = await MemoryRepository(session).list_for_user(message.from_user.id)
    if not rows:
        await message.answer("لا توجد قواعد بعد.\nPowered by SAIR AI")
        return
    await message.answer("\n".join([f"{r.id}) {r.trigger} -> {r.response}" for r in rows[:20]]))
