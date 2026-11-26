from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class MaintenanceInput(BaseModel):
    productId: str = Field(min_length=1, max_length=200)
    maintenanceTitle: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    scheduledDate: date
    frequency: str = Field(default="Custom", max_length=40)
    status: str = Field(default="Scheduled", max_length=40)
    completionDate: date | None = None
    cost: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)

    @field_validator("maintenanceTitle")
    @classmethod
    def trim_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Maintenance title cannot be blank.")
        return value
