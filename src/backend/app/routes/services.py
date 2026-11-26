from datetime import datetime, time, timezone

from fastapi import APIRouter, HTTPException, Response, status

from app.dependencies import CurrentUser
from google.cloud.firestore_v1 import FieldFilter
from app.firebase import get_firestore
from app.schemas.service import ServiceInput
from app.services.product_service import get_product

router = APIRouter(prefix="/api/products/{product_id}/services", tags=["service history"])
global_router = APIRouter(prefix="/api/services", tags=["service history"])


def _service_dict(snapshot):
    data = snapshot.to_dict()
    for key in ("serviceDate", "createdAt", "updatedAt"):
        value = data.get(key)
        if hasattr(value, "isoformat"):
            data[key] = value.date().isoformat() if key == "serviceDate" else value.isoformat()
    return data


def _service_reference(user_id: str, service_id: str):
    snapshot = get_firestore().collection("serviceRecords").document(service_id).get()
    if not snapshot.exists or snapshot.to_dict().get("userId") != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service record not found.")
    return snapshot.reference, snapshot.to_dict()


@global_router.get("")
def list_all_service_records(user: CurrentUser):
    db = get_firestore()
    records = db.collection("serviceRecords").where("userId", "==", user["uid"]).stream()
    products = {
        snapshot.id: snapshot.to_dict().get("productName", "Product")
        for snapshot in db.collection("products").where("userId", "==", user["uid"]).stream()
    }
    items = [_service_dict(record) for record in records]
    for item in items:
        item["productName"] = products.get(item["productId"], "Product")
    return {"items": sorted(items, key=lambda row: row["serviceDate"], reverse=True)}


@router.get("")
def list_service_records(product_id: str, user: CurrentUser):
    get_product(user["uid"], product_id)
    records = get_firestore().collection("serviceRecords").where("userId", "==", user["uid"]).where("productId", "==", product_id).stream()
    items = [_service_dict(record) for record in records]
    return {"items": sorted(items, key=lambda row: row["serviceDate"], reverse=True)}


@router.post("", status_code=status.HTTP_201_CREATED)
def add_service_record(product_id: str, payload: ServiceInput, user: CurrentUser):
    get_product(user["uid"], product_id)
    db = get_firestore()
    ref = db.collection("serviceRecords").document()
    data = payload.model_dump()
    data["serviceDate"] = datetime.combine(data["serviceDate"], time.min, timezone.utc)
    data.update({
        "serviceId": ref.id,
        "productId": product_id,
        "userId": user["uid"],
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
    })
    ref.set(data)
    return _service_dict(ref.get())


@router.put("/{service_id}")
def update_service_record(product_id: str, service_id: str, payload: ServiceInput, user: CurrentUser):
    get_product(user["uid"], product_id)
    ref, existing = _service_reference(user["uid"], service_id)
    if existing.get("productId") != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service record not found.")
    data = payload.model_dump()
    data["serviceDate"] = datetime.combine(data["serviceDate"], time.min, timezone.utc)
    data["updatedAt"] = datetime.now(timezone.utc)
    ref.update(data)
    return _service_dict(ref.get())


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_record(product_id: str, service_id: str, user: CurrentUser):
    get_product(user["uid"], product_id)
    ref, existing = _service_reference(user["uid"], service_id)
    if existing.get("productId") != product_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service record not found.")
    ref.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
