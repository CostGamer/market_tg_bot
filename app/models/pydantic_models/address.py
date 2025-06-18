from pydantic import BaseModel, Field, ConfigDict


class AddressPM(BaseModel):
    model_config = ConfigDict(from_attributes=True, strict=True)

    address: str = Field(..., description="full user's address")
    city: str = Field(..., description="city")
    name: str = Field(..., description="name of the shipping method")
    index: int = Field(..., description="address index")


class AddressPMGet(AddressPM):
    model_config = ConfigDict(from_attributes=True, strict=True)

    id: int = Field(..., description="address ID in DB")
