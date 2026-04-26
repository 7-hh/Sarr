from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ربط الحساب", callback_data="go_link")],
            [InlineKeyboardButton(text="تشغيل/إيقاف الرد", callback_data="toggle_reply")],
            [InlineKeyboardButton(text="وضع الرد", callback_data="show_modes")],
            [InlineKeyboardButton(text="تفعيل اشتراك", callback_data="go_activate")],
            [InlineKeyboardButton(text="إعدادات متقدمة", callback_data="show_advanced")],
        ]
    )


def mode_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="AI", callback_data="mode_ai"),
                InlineKeyboardButton(text="Fixed", callback_data="mode_fixed"),
                InlineKeyboardButton(text="Away", callback_data="mode_away"),
            ]
        ]
    )
