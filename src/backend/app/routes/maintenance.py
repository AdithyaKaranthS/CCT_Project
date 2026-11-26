from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentUser
from app.firebase import get_firestore
from app.schemas.maintenance import MaintenanceInput
from app.services.product_service import get_product
from google.cloud.firestore_v1 import FieldFilter

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])
COLLECTION = "maintenance"


def _serialize(record_id: str, data: dict) -> dict:
    result = {**data, "maintenanceId": record_id}
    if isinstance(result.get("scheduledDate"), datetime):
        result["scheduledDate"] = result["scheduledDate"].date().isoformat()
    if isinstance(result.get("completionDate"), datetime):
        result["completionDate"] = result["completionDate"].date().isoformat()
    return result


@router.get("")
def list_maintenance(user: CurrentUser):
    snapshots = get_firestore().collection(COLLECTION).where(filter=FieldFilter("userId", "==", user["uid"])).stream()
    items = [_serialize(snapshot.id, snapshot.to_dict()) for snapshot in snapshots]
    return {"items": sorted(items, key=lambda item: item.get("scheduledDate", ""))}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_maintenance(payload: MaintenanceInput, user: CurrentUser):
    get_product(user["uid"], payload.productId)
    ref = get_firestore().collection(COLLECTION).document()
    now = datetime.now(timezone.utc)
    data = payload.model_dump()
    data.update({
        "maintenanceId": ref.id,
        "userId": user["uid"],
        "scheduledDate": datetime.combine(data["scheduledDate"], datetime.min.time(), timezone.utc),
        "completionDate": datetime.combine(data["completionDate"], datetime.min.time(), timezone.utc) if data["completionDate"] else None,
        "cost": float(Decimal(data["cost"])),
        "createdAt": now,
        "updatedAt": now,
    })
    ref.set(data)
    return _serialize(ref.id, data)


@router.put("/{maintenance_id}")
def update_maintenance(maintenance_id: str, payload: MaintenanceInput, user: CurrentUser):
    get_product(user["uid"], payload.productId)
    ref = get_firestore().collection(COLLECTION).document(maintenance_id)
    snapshot = ref.get()
    if not snapshot.exists or snapshot.to_dict().get("userId") != user["uid"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found.")
    data = payload.model_dump()
    data.update({
        "scheduledDate": datetime.combine(data["scheduledDate"], datetime.min.time(), timezone.utc),
        "completionDate": datetime.combine(data["completionDate"], datetime.min.time(), timezone.utc) if data["completionDate"] else None,
        "cost": float(Decimal(data["cost"])),
        "updatedAt": datetime.now(timezone.utc),
    })
    ref.update(data)
    return _serialize(maintenance_id, {**snapshot.to_dict(), **data})


@router.patch("/{maintenance_id}/complete")
def complete_maintenance(maintenance_id: str, user: CurrentUser):
    ref = get_firestore().collection(COLLECTION).document(maintenance_id)
    snapshot = ref.get()
    if not snapshot.exists or snapshot.to_dict().get("userId") != user["uid"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found.")
    data = snapshot.to_dict()
    today = date.today()
    update = {"status": "Completed", "completionDate": datetime.combine(today, datetime.min.time(), timezone.utc), "updatedAt": datetime.now(timezone.utc)}
    ref.update(update)
    return _serialize(maintenance_id, {**data, **update})


@router.delete("/{maintenance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_maintenance(maintenance_id: str, user: CurrentUser):
    ref = get_firestore().collection(COLLECTION).document(maintenance_id)
    snapshot = ref.get()
    if not snapshot.exists or snapshot.to_dict().get("userId") != user["uid"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found.")
    ref.delete()
