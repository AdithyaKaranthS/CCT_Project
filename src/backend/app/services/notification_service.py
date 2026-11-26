import smtplib
from datetime import date, datetime, timezone
from email.message import EmailMessage

from google.cloud.firestore_v1 import transactional

from app.config import get_settings
from app.firebase import get_firestore
from app.services.product_service import PRODUCTS, serialize_product

NOTIFICATIONS = "notifications"
REMINDER_DAYS = (30, 7, 0)


def _send_email(recipient: str, product_name: str, days: int) -> bool:
    settings = get_settings()
    if not all((settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from)):
        return False
    label = "today" if days == 0 else f"in {days} days"
    message = EmailMessage()
    message["Subject"] = f"Warranty reminder: {product_name} expires {label}"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(f"Your warranty for {product_name} expires {label}. Sign in to your Warranty Manager for details.")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        smtp.starttls()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
    return True


def generate_due_notifications() -> int:
    db = get_firestore()
    today = date.today()
    created = 0
    for snapshot in db.collection(PRODUCTS).stream():
        data = snapshot.to_dict()
        summary = serialize_product(snapshot.id, data)
        days = (summary["expiryDate"] - today).days
        if days not in REMINDER_DAYS:
            continue
        user_id = data["userId"]
        expiry_key = summary["expiryDate"].isoformat()
        notification_id = f"{snapshot.id}_{expiry_key}_{days}"
        ref = db.collection(NOTIFICATIONS).document(notification_id)
        notification = {
            "notificationId": notification_id,
            "userId": user_id,
            "productId": snapshot.id,
            "productName": data["productName"],
            "expiryDate": datetime.combine(summary["expiryDate"], datetime.min.time(), timezone.utc),
            "daysBeforeExpiry": days,
            "type": "warranty_expiry",
            "read": False,
            "createdAt": datetime.now(timezone.utc),
            "emailSent": False,
        }
        transaction = db.transaction()

        @transactional
        def create_once(tx):
            existing = ref.get(transaction=tx)
            if existing.exists:
                return False
            tx.create(ref, notification)
            return True

        created_now = create_once(transaction)
        if created_now:
            created += 1
        current_notice = ref.get().to_dict() or {}
        user = db.collection("users").document(user_id).get()
        email = (user.to_dict() or {}).get("email")
        if email and not current_notice.get("emailSent"):
            sent = _send_email(email, data["productName"], days)
            if sent:
                ref.update({"emailSent": True, "emailSentAt": datetime.now(timezone.utc)})
    for snapshot in db.collection("maintenance").stream():
        data = snapshot.to_dict()
        if data.get("status") == "Completed":
            continue
        scheduled = data.get("scheduledDate")
        if isinstance(scheduled, datetime):
            scheduled_date = scheduled.date()
        else:
            try:
                scheduled_date = date.fromisoformat(str(scheduled))
            except (TypeError, ValueError):
                continue
        days = (scheduled_date - today).days
        if days not in (7, 1, 0):
            continue
        user_id = data["userId"]
        notification_id = f"maintenance_{snapshot.id}_{scheduled_date.isoformat()}_{days}"
        ref = db.collection(NOTIFICATIONS).document(notification_id)
        notification = {
            "notificationId": notification_id,
            "userId": user_id,
            "productId": data["productId"],
            "maintenanceId": snapshot.id,
            "maintenanceTitle": data["maintenanceTitle"],
            "scheduledDate": datetime.combine(scheduled_date, datetime.min.time(), timezone.utc),
            "daysBeforeMaintenance": days,
            "type": "maintenance_reminder",
            "read": False,
            "createdAt": datetime.now(timezone.utc),
        }
        transaction = db.transaction()

        @transactional
        def create_maintenance_notice(tx):
            existing = ref.get(transaction=tx)
            if existing.exists:
                return False
            tx.create(ref, notification)
            return True

        if create_maintenance_notice(transaction):
            created += 1
    return created
