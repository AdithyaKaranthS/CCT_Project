from fastapi import APIRouter

from app.dependencies import CurrentUser
from app.services.product_service import list_products

router = APIRouter(prefix="/api/warranties", tags=["warranties"])


@router.get("/expiring")
def expiring_warranties(user: CurrentUser):
    products = list_products(user["uid"])
    return {"items": [item for item in products if item["warrantyDaysRemaining"] >= 0 and item["warrantyDaysRemaining"] <= 30]}
