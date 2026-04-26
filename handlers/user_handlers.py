from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from config import settings
from database.connection import SessionLocal
from database.models import ReplyModeEnum
from database.repositories import ExceptionRepository, PreferenceRepository, UserRepository
from services import runtime_settings
from subscription import subscription_service
from utils import main_menu, mode_menu, start_text

router = Router()


async def _check_force_subscribe(message: Message) -> bool:
    force_channel = await runtime_settings.get_force_channel(settings.force_subscribe_channel)
    try:
        member = await message.bot.get_chat_member(force_channel, message.from_user.id)
        return member.status in {"member", "administrator", "creator"}
    except Exception:
        return False


@router.message(F.text == "/start")
async def start_cmd(message: Message) -> None:
    if not await runtime_settings.is_system_enabled():
        await message.answer("النظام متوقف مؤقتًا من الإدارة.\nحقوق التطوير: @J2J_2")
        return
    force_channel = await runtime_settings.get_force_channel(settings.force_subscribe_channel)
    if not await _check_force_subscribe(message):
        await message.answer(f"اشترك أولًا في {force_channel} ثم أعد المحاولة.\n{settings.bot_tagline}\n@J2J_2")
        return
    await message.answer(start_text(), reply_markup=main_menu())


@router.callback_query(F.data == "go_link")
async def cb_link(call: CallbackQuery) -> None:
    await call.message.answer("ابدأ الربط عبر الأمر /link")
    await call.answer()


@router.callback_query(F.data == "go_activate")
async def cb_activate(call: CallbackQuery) -> None:
    await call.message.answer("فعّل مفتاحك عبر: /activate YOUR_KEY")
    await call.answer()


@router.callback_query(F.data == "toggle_reply")
async def cb_toggle(call: CallbackQuery) -> None:
    async with SessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get(call.from_user.id)
        user.auto_reply_enabled = not user.auto_reply_enabled
        await session.commit()
        text = f"الرد التلقائي: {'مفعل' if user.auto_reply_enabled else 'متوقف'}\nحقوق التطوير: @J2J_2"
    await call.message.answer(text)
    await call.answer()


@router.callback_query(F.data == "show_modes")
async def cb_modes(call: CallbackQuery) -> None:
    await call.message.answer("اختر وضع الرد:", reply_markup=mode_menu())
    await call.answer()


@router.callback_query(F.data.startswith("mode_"))
async def cb_mode_set(call: CallbackQuery) -> None:
    mode = call.data.replace("mode_", "")
    async with SessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get(call.from_user.id)
        user.reply_mode = ReplyModeEnum(mode)
        await session.commit()
    await call.message.answer(f"تم التبديل إلى وضع: {mode.upper()}\nحقوق التطوير: @J2J_2")
    await call.answer()


@router.callback_query(F.data == "show_advanced")
async def cb_advanced(call: CallbackQuery) -> None:
    await call.message.answer(
        "إعدادات متقدمة للمشتري:\n"
        "/settrigger <word> لتحديد كلمة تشغيل الرد\n"
        "/setgroup <chat_id> لتحديد كروب تحويل الرسائل\n"
        "/toggle لتشغيل/إيقاف الرد\n"
        "حقوق التطوير: @J2J_2"
    )
    await call.answer()


@router.message(F.text.startswith("/mode"))
async def mode_cmd(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("استخدم: /mode ai|fixed|away\nPowered by SAIR AI")
        return
    mode = parts[1].strip().lower()
    if mode not in {"ai", "fixed", "away"}:
        await message.answer("الوضع غير صالح.\nPowered by SAIR AI")
        return
    async with SessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get(message.from_user.id)
        if not user:
            return
        user.reply_mode = ReplyModeEnum(mode)
        await session.commit()
    await message.answer(f"تم تحديث الوضع إلى: {mode}\nPowered by SAIR AI")


@router.message(F.text.startswith("/activate"))
async def activate_cmd(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("استخدم: /activate KEY\nPowered by SAIR AI")
        return
    async with SessionLocal() as session:
        from database.repositories import KeyRepository

        user_repo = UserRepository(session)
        key_repo = KeyRepository(session)
        user = await user_repo.get(message.from_user.id)
        ok = await key_repo.activate(parts[1].strip(), user)
    await message.answer("تم تفعيل المفتاح بنجاح.\nPowered by SAIR AI" if ok else "المفتاح غير صالح.\nPowered by SAIR AI")


@router.message(F.text.startswith("/persona"))
async def persona_cmd(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("استخدم: /persona وصف الشخصية\nPowered by SAIR AI")
        return
    async with SessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get(message.from_user.id)
        user.persona_prompt = f"سائر... {parts[1].strip()}"
        await session.commit()
    await message.answer("تم تحديث شخصية الرد.\nPowered by SAIR AI")


@router.message(F.text.startswith("/settrigger"))
async def set_trigger_cmd(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("استخدم: /settrigger <word>\nحقوق التطوير: @J2J_2")
        return
    trigger = parts[1].strip()
    async with SessionLocal() as session:
        await PreferenceRepository(session).set_trigger_word(message.from_user.id, trigger)
    await message.answer(f"تم تعيين كلمة التشغيل إلى: {trigger}\nحقوق التطوير: @J2J_2")


@router.message(F.text.startswith("/setgroup"))
async def set_group_cmd(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.answer("استخدم: /setgroup <group_chat_id>\nحقوق التطوير: @J2J_2")
        return
    async with SessionLocal() as session:
        await PreferenceRepository(session).set_forward_group(message.from_user.id, int(parts[1]))
    await message.answer("تم حفظ كروب التحويل بنجاح.\nحقوق التطوير: @J2J_2")


@router.message(F.text == "/me")
async def me_cmd(message: Message) -> None:
    async with SessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get(message.from_user.id)
        if not user:
            return
        subscription_ok = subscription_service.has_subscription(user)
        limit = subscription_service.daily_limit(user)
        days_left = max((user.subscription_expires_at - datetime.utcnow()).days, 0)
        await message.answer(
            f"ID: {user.id}\n"
            f"Role: {user.role.value}\n"
            f"Subscription: {'active' if subscription_ok else 'expired'} ({days_left} days)\n"
            f"Daily: {user.daily_used_messages}/{limit}\n"
            f"Mode: {user.reply_mode.value}\n"
            f"{settings.bot_tagline}\n"
            "حقوق التطوير: @J2J_2"
        )


@router.message(F.text.startswith("/away"))
async def away_cmd(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("استخدم: /away رسالة الغياب\nPowered by SAIR AI")
        return
    async with SessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get(message.from_user.id)
        user.away_message = parts[1]
        await session.commit()
    await message.answer("تم تحديث رسالة الغياب.\nPowered by SAIR AI")


@router.message(F.text.startswith("/toggle"))
async def toggle_cmd(message: Message) -> None:
    async with SessionLocal() as session:
        repo = UserRepository(session)
        user = await repo.get(message.from_user.id)
        user.auto_reply_enabled = not user.auto_reply_enabled
        await session.commit()
        await message.answer(
            f"الرد التلقائي: {'مفعل' if user.auto_reply_enabled else 'متوقف'}\nPowered by SAIR AI"
        )


@router.message(F.text.startswith("/exclude"))
async def exclude_cmd(message: Message) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].lstrip("-").isdigit():
        await message.answer("استخدم: /exclude <peer_id>\nPowered by SAIR AI")
        return
    async with SessionLocal() as session:
        repo = ExceptionRepository(session)
        await repo.add(message.from_user.id, int(parts[1]))
    await message.answer("تمت إضافة الاستثناء.\nPowered by SAIR AI")
