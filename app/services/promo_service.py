from app.repositories import PromoRepo

# from app.models.pydantic_models import UserPM


class PromoService:
    def __init__(self, repo: PromoRepo) -> None:
        self.repo = repo

    # async def
