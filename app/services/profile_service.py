from app.repositories import UserRepo
from app.models.pydantic_models import UserPM


class ProfileService:
    def __init__(self, repo: UserRepo) -> None:
        self.repo = repo

    async def get_user(self, tg_id: int) -> UserPM | None:
        return await self.repo.get_user_info(tg_id)

    async def update_name(
        self, tg_id: int, tg_username: str, name: str
    ) -> UserPM | None:
        user = await self.repo.get_user_info(tg_id)
        if user and user.phone:
            updated = UserPM(
                tg_id=tg_id, tg_username=tg_username, name=name, phone=user.phone
            )
            await self.repo.update_user_info(updated)
            return await self.repo.get_user_info(tg_id)
        return None

    async def update_phone(
        self, tg_id: int, tg_username: str, phone: str
    ) -> UserPM | None:
        user = await self.repo.get_user_info(tg_id)
        if user and user.name:
            updated = UserPM(
                tg_id=tg_id, tg_username=tg_username, name=user.name, phone=phone
            )
            await self.repo.update_user_info(updated)
            return await self.repo.get_user_info(tg_id)
        return None

    async def create_user(
        self, tg_id: int, tg_username: str, name: str, phone: str
    ) -> UserPM | None:
        new_user = UserPM(tg_id=tg_id, tg_username=tg_username, name=name, phone=phone)
        await self.repo.post_user(new_user)
        return await self.repo.get_user_info(tg_id)

    async def is_profile_complete(self, user: UserPM | None) -> bool:
        return bool(user and user.name and user.phone)

    def render_profile(self, user: UserPM | None) -> str:
        return (
            f"<b>Ваш профиль:</b>\n"
            f"Имя: {user.name if user and user.name else '🟡 Заполните'}\n"
            f"Телефон: {user.phone if user and user.phone else '🟡 Заполните'}\n"
            f"Username: @{user.tg_username if user and user.tg_username else 'не установлен'}"
        )
