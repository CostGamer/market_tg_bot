from pydantic import BaseModel, Field, ConfigDict


class OrderPMGet(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    id: int | None = Field(None, description="order ID")
    description: str = Field(..., description="order description")
    product_url: str = Field(..., description="order URL")
    final_price: float = Field(..., description="final price in rubles")
    status: str = Field(..., description="status order")
    quantity: int = Field(..., description="quantity")
    unit_price_rmb: float = Field(..., description="price per unit in yuan")
    unit_price_rub: float = Field(..., description="price per unit in rubles")
    photo_url: str | None = Field(None, description="telegram URL photo")


class OrderPMPost(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    id: int | None = Field(None, description="order ID")
    description: str = Field(..., description="order description")
    product_url: str = Field(..., description="order URL")
    final_price: float = Field(..., description="final price in rubles")
    status: str = Field(..., description="status order")
    quantity: int = Field(..., description="quantity")
    unit_price_rmb: float = Field(..., description="price per unit in yuan")
    unit_price_rub: float = Field(..., description="price per unit in rubles")
    photo_url: str | None = Field(None, description="telegram URL photo")
    address_id: int = Field(..., description="address ID")
    user_id: int = Field(..., description="user ID")


class OrderPMUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    status: str | None = Field(None, description="status order")
    track_cn: str | None = Field(None, description="CNY track number")
    track_ru: str | None = Field(None, description="RU track number")
