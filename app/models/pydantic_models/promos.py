from pydantic import BaseModel, Field, ConfigDict


class PromoGetPM(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    promocode: str = Field(..., description="promocode")
    amount_percentage: int = Field(..., description="promocode precentage")
