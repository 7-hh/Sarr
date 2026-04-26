from datetime import datetime, timedelta

from config import settings
from database.models import RoleEnum, User


class SubscriptionService:
    def daily_limit(self, user: User) -> int:
        return settings.vip_daily_limit if user.role in {RoleEnum.VIP, RoleEnum.ADMIN, RoleEnum.OWNER} else settings.free_daily_limit

    def has_subscription(self, user: User) -> bool:
        if user.role in {RoleEnum.ADMIN, RoleEnum.OWNER}:
            return True
        return user.subscription_expires_at > datetime.utcnow()

    def ensure_daily_reset(self, user: User) -> None:
        if datetime.utcnow() - user.daily_reset_at >= timedelta(days=1):
            user.daily_used_messages = 0
            user.daily_reset_at = datetime.utcnow()

    def can_send(self, user: User) -> bool:
        self.ensure_daily_reset(user)
        return user.daily_used_messages < self.daily_limit(user)


subscription_service = SubscriptionService()
