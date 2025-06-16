from pydantic import BaseModel, Field, ConfigDict


class UserPM(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    tg_id: int = Field(..., description="telegram ID")
    tg_username: str | None = Field(..., description="telegram username")
    name: str = Field(..., description="name of the user")
    phone: str = Field(..., description="user phone number")
