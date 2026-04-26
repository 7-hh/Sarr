from config import settings


def start_text() -> str:
    return (
        f"مرحبًا بك في {settings.bot_name}\n"
        "منصة SaaS لربط حسابك الشخصي في تيليجرام مع ردود ذكية تلقائية.\n\n"
        "الخطوات:\n"
        "1) اربط الحساب عبر /link\n"
        "2) فعّل الرد عبر /toggle ثم اختر النمط\n"
        "3) فعّل مفتاح VIP عبر /activate\n\n"
        f"{settings.bot_tagline}\n"
        "حقوق التطوير: @J2J_2"
    )
