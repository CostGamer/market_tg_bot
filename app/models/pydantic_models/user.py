from pydantic import BaseModel, Field, ConfigDict


class UserPM(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    tg_id: int = Field(..., description="telegram ID")
    tg_username: str | None = Field(None, description="telegram username")
    name: str | None = Field(None, description="name of the user")
    phone: str | None = Field(None, description="user phone number")
