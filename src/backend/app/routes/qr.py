import io
from datetime import datetime, timezone

import qrcode
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.dependencies import CurrentUser
from app.firebase import get_firestore
from app.services.product_service import get_product

router = APIRouter(prefix="/api/qr", tags=["qr"])


def _build_qr(product_id: str, origin: str = "") -> bytes:
    url = f"{origin.rstrip('/')}/products/{product_id}" if origin else f"/products/{product_id}"
    image = qrcode.make(url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@router.post("/{product_id}")
def generate_product_qr(product_id: str, user: CurrentUser):
    product = get_product(user["uid"], product_id)
    ref = get_firestore().collection("products").document(product_id)
    qr_url = f"/api/qr/{product_id}/download"
    ref.update({"qrCodeURL": qr_url, "updatedAt": datetime.now(timezone.utc)})
    return {"productId": product_id, "qrCodeURL": qr_url}


@router.get("/{product_id}/download")
def download_product_qr(product_id: str, user: CurrentUser):
    get_product(user["uid"], product_id)
    content = _build_qr(product_id)
    return StreamingResponse(io.BytesIO(content), media_type="image/png", headers={
        "Content-Disposition": f'attachment; filename="{product_id}-warranty-qr.png"',
    })


@router.get("/scan/{product_id}")
def scan_product_qr(product_id: str, user: CurrentUser):
    return get_product(user["uid"], product_id)
