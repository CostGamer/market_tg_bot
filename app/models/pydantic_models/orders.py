from pydantic import BaseModel, Field, ConfigDict


class OrderPMGet(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    description: str = Field(..., description="order description")
    product_url: str = Field(..., description="order URL")
    final_price: float = Field(..., description="price * count")
    status: str = Field(..., description="status order")


class OrderPMPost(OrderPMGet):
    model_config = ConfigDict(from_attributes=True, strict=True)

    id: int | None = Field(None, description="order ID")
    quantity: int = Field(..., description="quantity")
    unit_price: float = Field(..., description="price per unit")
    photo_url: str = Field(..., description="telegram URL photo")
    track_cn: str = Field(..., description="CNY track number")
    track_ru: str = Field(..., description="RU track number")
    address_id: int = Field(..., description="adress ID")
    user_id: int = Field(..., description="user ID")
