from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter
from fastapi import Query

from app.dependencies import CurrentUser
from app.services.product_service import list_products
from app.firebase import get_firestore
from google.cloud.firestore_v1 import FieldFilter

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
def get_analytics(
    user: CurrentUser,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
):
    products = list_products(user["uid"])
    if start_date or end_date:
        products = [
            item for item in products
            if (not start_date or item["purchaseDate"] >= start_date)
            and (not end_date or item["purchaseDate"] <= end_date)
        ]
    categories = defaultdict(lambda: {"count": 0, "spend": 0.0})
    monthly = defaultdict(float)
    expiry_windows = {"30": 0, "60": 0, "90": 0}
    today = date.today()
    for product in products:
        category = product.get("category") or "Other"
        categories[category]["count"] += 1
        categories[category]["spend"] += float(product.get("purchasePrice", 0))
        purchase = product["purchaseDate"]
        monthly[purchase.strftime("%Y-%m")] += float(product.get("purchasePrice", 0))
        remaining = product["warrantyDaysRemaining"]
        if 0 <= remaining <= 30:
            expiry_windows["30"] += 1
        if 0 <= remaining <= 60:
            expiry_windows["60"] += 1
        if 0 <= remaining <= 90:
            expiry_windows["90"] += 1
    maintenance_records = get_firestore().collection("maintenance").where(filter=FieldFilter("userId", "==", user["uid"])).stream()
    maintenance_monthly = defaultdict(float)
    maintenance_total = 0.0
    maintenance_status = {"Upcoming": 0, "Overdue": 0, "Completed": 0}
    for snapshot in maintenance_records:
        record = snapshot.to_dict()
        cost = float(record.get("cost", 0) or 0)
        maintenance_total += cost
        record_status = record.get("status", "Scheduled")
        scheduled = record.get("scheduledDate")
        if isinstance(scheduled, datetime):
            scheduled_date = scheduled.date()
        else:
            scheduled_date = date.fromisoformat(str(scheduled)) if scheduled else today
        if record_status == "Completed":
            maintenance_status["Completed"] += 1
            month = scheduled.strftime("%Y-%m") if isinstance(scheduled, datetime) else scheduled_date.strftime("%Y-%m")
            maintenance_monthly[month] += cost
        elif scheduled_date < today:
            maintenance_status["Overdue"] += 1
        else:
            maintenance_status["Upcoming"] += 1
    return {
        "totalProducts": len(products),
        "activeWarranties": sum(item["warrantyStatus"] == "active" for item in products),
        "expiringWarranties": sum(0 <= item["warrantyDaysRemaining"] <= 30 for item in products),
        "expiredWarranties": sum(item["warrantyStatus"] == "expired" for item in products),
        "totalPurchaseSpending": round(sum(float(item.get("purchasePrice", 0)) for item in products), 2),
        "totalMaintenanceSpending": round(maintenance_total, 2),
        "categories": [
            {"category": category, "count": values["count"], "spend": round(values["spend"], 2)}
            for category, values in sorted(categories.items())
        ],
        "warrantyStatusDistribution": [
            {"status": "Active", "count": sum(item["warrantyStatus"] == "active" for item in products)},
            {"status": "Expiring Soon", "count": sum(0 <= item["warrantyDaysRemaining"] <= 30 for item in products)},
            {"status": "Expired", "count": sum(item["warrantyStatus"] == "expired" for item in products)},
        ],
        "monthlyPurchaseSpending": [{"month": month, "spend": round(amount, 2)} for month, amount in sorted(monthly.items())],
        "maintenanceMonthlySpending": [{"month": month, "spend": round(amount, 2)} for month, amount in sorted(maintenance_monthly.items())],
        "maintenanceStatus": maintenance_status,
        "expiryWindows": expiry_windows,
    }
