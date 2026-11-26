from pydantic import BaseModel, Field, field_validator


class ClaimInput(BaseModel):
    productId: str = Field(min_length=1, max_length=200)
    problemDescription: str = Field(min_length=1, max_length=4000)
    claimDate: str | None = None
    claimStatus: str = Field(default="Draft", max_length=40)
    serviceCenter: str = Field(default="", max_length=200)
    resolutionNotes: str = Field(default="", max_length=4000)

    @field_validator("claimStatus")
    @classmethod
    def validate_status(cls, value: str) -> str:
        allowed = {"Draft", "Submitted", "Under Review", "Approved", "Rejected", "Resolved"}
        if value not in allowed:
            raise ValueError(f"Claim status must be one of: {', '.join(sorted(allowed))}")
        return value
