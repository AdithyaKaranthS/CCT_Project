from datetime import date

from pydantic import BaseModel, Field


class ServiceInput(BaseModel):
    serviceDate: date
    provider: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=1000)
    cost: float = Field(default=0, ge=0)
    notes: str = Field(default="", max_length=1000)


class ServiceResponse(ServiceInput):
    serviceId: str
    productId: str
    userId: str
