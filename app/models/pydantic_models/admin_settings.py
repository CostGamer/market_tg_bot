from pydantic import BaseModel, Field, ConfigDict


class AdminSettingsPMUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    commision_rate: float = Field(..., description="Commission rate for transactions")
    kilo_delivery: float = Field(..., description="Delivery cost per kilogram")
    cny_rate_syrcharge: float = Field(..., description="CNY surcharge rate")
    user_tg_id: int = Field(..., description="Telegram user ID of the admin")
    additional_control: int = Field(
        ..., description="additional control on shipping company side"
    )


class AdminSettingsPM(AdminSettingsPMUpdate):
    model_config = ConfigDict(from_attributes=True, strict=True)

    faq: str = Field(..., description="Frequent asked questions")
