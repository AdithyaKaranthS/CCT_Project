from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductInput(BaseModel):
    productName: str = Field(min_length=1, max_length=120)
    brand: str = Field(default="", max_length=100)
    category: str = Field(default="Other", max_length=60)
    modelNumber: str = Field(default="", max_length=100)
    serialNumber: str = Field(default="", max_length=100)
    purchaseDate: date
    warrantyDuration: int = Field(ge=0, le=600, description="Warranty duration in months")
    purchasePrice: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    seller: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=2000)

    @field_validator("productName")
    @classmethod
    def trim_product_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Product name cannot be blank.")
        return value


class ProductResponse(ProductInput):
    model_config = ConfigDict(extra="allow")

    productId: str
    userId: str
    expiryDate: date
    invoiceURL: str | None = None
    invoiceStoragePath: str | None = None
    warrantyDaysRemaining: int
    warrantyStatus: str
