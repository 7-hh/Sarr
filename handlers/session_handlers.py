from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from pyrogram import Client
from pyrogram.errors import FloodWait, PhoneCodeInvalid, PhoneNumberInvalid, SessionPasswordNeeded

from database.connection import SessionLocal
from database.repositories import SessionRepository
from services import encrypt_session
from userbot import session_manager

router = Router()
pending_auth: dict[int, Client] = {}


class LinkStates(StatesGroup):
    waiting_phone = State()
    waiting_code = State()
    waiting_password = State()


@router.message(F.text == "/link")
async def link_start(message: Message, state: FSMContext) -> None:
    await state.set_state(LinkStates.waiting_phone)
    await message.answer("أرسل رقم الهاتف بصيغة دولية مثل +201000000000")


@router.message(LinkStates.waiting_phone)
async def link_phone(message: Message, state: FSMContext) -> None:
    phone = message.text.strip()
    app = Client("auth_tmp", api_id=2040, api_hash="b18441a1ff607e10a989891a5462e627", in_memory=True)
    await app.connect()
    try:
        sent = await app.send_code(phone)
    except PhoneNumberInvalid:
        await app.disconnect()
        await message.answer("رقم غير صحيح، أعد المحاولة.")
        return
    except FloodWait as exc:
        await app.disconnect()
        wait_minutes = max(int(exc.value // 60), 1)
        await message.answer(
            f"تيليجرام فرض انتظارًا مؤقتًا بسبب كثرة طلبات OTP. أعد المحاولة بعد {wait_minutes} دقيقة."
        )
        return
    except Exception:
        await app.disconnect()
        await message.answer("تعذر إرسال OTP الآن. حاول لاحقًا.")
        return
    await state.update_data(phone=phone, phone_code_hash=sent.phone_code_hash)
    await state.set_state(LinkStates.waiting_code)
    pending_auth[message.from_user.id] = app
    await message.answer("أرسل كود OTP الذي وصلك. مثال: 1 2 3 4 5")


@router.message(LinkStates.waiting_code)
async def link_code(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    app = pending_auth.get(message.from_user.id)
    if not app:
        await state.clear()
        await message.answer("انتهت جلسة الربط. أعد /link")
        return
    code = message.text.replace(" ", "")
    try:
        await app.sign_in(phone_number=data["phone"], phone_code_hash=data["phone_code_hash"], phone_code=code)
    except SessionPasswordNeeded:
        await state.set_state(LinkStates.waiting_password)
        await message.answer("هذا الحساب محمي بكلمة سر 2FA. أرسل كلمة السر.")
        return
    except PhoneCodeInvalid:
        await message.answer("OTP غير صحيح، حاول مرة أخرى.")
        return
    except FloodWait as exc:
        wait_minutes = max(int(exc.value // 60), 1)
        await message.answer(f"انتظار إجباري من تيليجرام. أعد المحاولة بعد {wait_minutes} دقيقة.")
        return

    session_string = await app.export_session_string()
    await app.disconnect()
    async with SessionLocal() as session:
        await SessionRepository(session).upsert(
            user_id=message.from_user.id,
            encrypted_session=encrypt_session(session_string),
            phone_number=data["phone"],
        )
    await session_manager.start_all()
    pending_auth.pop(message.from_user.id, None)
    await state.clear()
    await message.answer("تم ربط حسابك بنجاح. Powered by SAIR AI")


@router.message(LinkStates.waiting_password)
async def link_password(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    app = pending_auth.get(message.from_user.id)
    if not app:
        await state.clear()
        await message.answer("انتهت جلسة الربط. أعد /link")
        return
    try:
        await app.check_password(message.text.strip())
    except FloodWait as exc:
        wait_minutes = max(int(exc.value // 60), 1)
        await message.answer(f"انتظار إجباري من تيليجرام. أعد المحاولة بعد {wait_minutes} دقيقة.")
        return
    session_string = await app.export_session_string()
    await app.disconnect()
    async with SessionLocal() as session:
        await SessionRepository(session).upsert(
            user_id=message.from_user.id,
            encrypted_session=encrypt_session(session_string),
            phone_number=data["phone"],
        )
    await session_manager.start_all()
    pending_auth.pop(message.from_user.id, None)
    await state.clear()
    await message.answer("تم ربط الحساب (2FA) بنجاح. Powered by SAIR AI")
