from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status

from app.firebase import get_firestore
from app.services.warranty_service import warranty_summary

PRODUCTS = "products"


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def serialize_product(product_id: str, data: dict) -> dict:
    purchase_date = _as_date(data["purchaseDate"])
    duration = int(data.get("warrantyDuration", 0))
    summary = warranty_summary(purchase_date, duration)
    result = {**data, **summary, "productId": product_id}
    result["purchaseDate"] = purchase_date
    if "purchasePrice" in result:
        result["purchasePrice"] = float(result["purchasePrice"])
    for key in ("createdAt", "updatedAt"):
        if isinstance(result.get(key), datetime):
            result[key] = result[key].isoformat()
    return result


def _expiry_timestamp(purchase_date: date, duration_months: int) -> datetime:
    expiry_date = warranty_summary(purchase_date, duration_months)["expiryDate"]
    return datetime.combine(expiry_date, datetime.min.time(), timezone.utc)


def _reference(product_id: str):
    return get_firestore().collection(PRODUCTS).document(product_id)


def get_product(user_id: str, product_id: str) -> dict:
    snapshot = _reference(product_id).get()
    if not snapshot.exists or snapshot.to_dict().get("userId") != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return serialize_product(snapshot.id, snapshot.to_dict())


def list_products(user_id: str, search: str | None = None, category: str | None = None) -> list[dict]:
    # User filtering is enforced server-side so Admin SDK access cannot cross account boundaries.
    snapshots = get_firestore().collection(PRODUCTS).where("userId", "==", user_id).stream()
    items = [serialize_product(snapshot.id, snapshot.to_dict()) for snapshot in snapshots]
    if search:
        query = search.casefold()
        items = [
            item for item in items
            if query in " ".join(str(item.get(key, "")) for key in (
                "productName", "brand", "category", "modelNumber", "serialNumber", "seller"
            )).casefold()
        ]
    if category:
        items = [item for item in items if item.get("category", "").casefold() == category.casefold()]
    return sorted(items, key=lambda item: item["expiryDate"])


def create_product(user_id: str, data: dict) -> dict:
    db = get_firestore()
    ref = db.collection(PRODUCTS).document()
    now = datetime.now(timezone.utc)
    payload = {
        **data,
        "productId": ref.id,
        "userId": user_id,
        "purchaseDate": datetime.combine(data["purchaseDate"], datetime.min.time(), timezone.utc),
        "expiryDate": _expiry_timestamp(data["purchaseDate"], data["warrantyDuration"]),
        "purchasePrice": float(Decimal(data["purchasePrice"])),
        "invoiceURL": None,
        "invoiceStoragePath": None,
        "qrCodeURL": f"/api/qr/{ref.id}/download",
        "createdAt": now,
        "updatedAt": now,
    }
    ref.set(payload)
    return serialize_product(ref.id, payload)


def update_product(user_id: str, product_id: str, data: dict) -> dict:
    ref = _reference(product_id)
    snapshot = ref.get()
    if not snapshot.exists or snapshot.to_dict().get("userId") != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    payload = {
        **data,
        "purchaseDate": datetime.combine(data["purchaseDate"], datetime.min.time(), timezone.utc),
        "expiryDate": _expiry_timestamp(data["purchaseDate"], data["warrantyDuration"]),
        "purchasePrice": float(Decimal(data["purchasePrice"])),
        "updatedAt": datetime.now(timezone.utc),
    }
    ref.update(payload)
    return serialize_product(product_id, {**snapshot.to_dict(), **payload})


def delete_product(user_id: str, product_id: str) -> None:
    ref = _reference(product_id)
    snapshot = ref.get()
    if not snapshot.exists or snapshot.to_dict().get("userId") != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    db = get_firestore()
    invoice_path = snapshot.to_dict().get("invoiceStoragePath")
    if invoice_path:
        from app.services.storage_service import delete_invoice

        delete_invoice(invoice_path, user_id, product_id)
    for collection in ("serviceRecords", "notifications"):
        for record in db.collection(collection).where("productId", "==", product_id).where("userId", "==", user_id).stream():
            record.reference.delete()
    for collection in ("claims", "maintenance"):
        for record in db.collection(collection).where("productId", "==", product_id).where("userId", "==", user_id).stream():
            record.reference.delete()
    ref.delete()
