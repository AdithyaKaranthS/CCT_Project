import hmac

from fastapi import APIRouter, Header, HTTPException, Response, status

from app.config import get_settings
from app.dependencies import CurrentUser
from app.firebase import get_firestore
from app.services.notification_service import generate_due_notifications
from google.cloud.firestore_v1 import FieldFilter

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(user: CurrentUser):
    docs = get_firestore().collection("notifications").where(filter=FieldFilter("userId", "==", user["uid"])).stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        data["notificationId"] = doc.id
        if hasattr(data.get("expiryDate"), "isoformat"):
            data["expiryDate"] = data["expiryDate"].date().isoformat()
        if hasattr(data.get("createdAt"), "isoformat"):
            data["createdAt"] = data["createdAt"].isoformat()
        items.append(data)
    items.sort(key=lambda item: item.get("createdAt", ""), reverse=True)
    return {"items": items}


@router.patch("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_read(notification_id: str, user: CurrentUser):
    ref = get_firestore().collection("notifications").document(notification_id)
    doc = ref.get()
    if not doc.exists or doc.to_dict().get("userId") != user["uid"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    ref.update({"read": True})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/scheduled")
def run_scheduled_notifications(x_scheduler_secret: str | None = Header(default=None)):
    secret = get_settings().scheduler_secret
    if not secret or not x_scheduler_secret or not hmac.compare_digest(secret, x_scheduler_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scheduler credentials.")
    return {"created": generate_due_notifications()}
