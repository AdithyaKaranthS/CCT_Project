from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.config import get_settings
from app.dependencies import CurrentUser
from app.firebase import get_firestore
from app.services.product_service import get_product
from app.services.storage_service import (
    delete_invoice,
    get_invoice_file,
    invoice_content_type,
    upload_invoice,
)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.post("/{product_id}", status_code=status.HTTP_201_CREATED)
async def upload_product_invoice(product_id: str, user: CurrentUser, file: UploadFile = File(...)):
    product = get_product(user["uid"], product_id)
    max_bytes = get_settings().max_invoice_bytes
    content = await file.read(max_bytes + 1)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty.")
    if len(content) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"Invoice files must be {max_bytes // (1024 * 1024)} MB or smaller.")
    path = upload_invoice(user["uid"], product_id, content, file.content_type or "")
    try:
        get_firestore().collection("products").document(product_id).update({
            "invoiceURL": f"/api/invoices/{product_id}",
            "invoiceStoragePath": path,
        })
    except Exception:
        delete_invoice(path, user["uid"], product_id)
        raise
    old_path = product.get("invoiceStoragePath")
    if old_path and old_path != path:
        delete_invoice(old_path, user["uid"], product_id)
    return {"invoiceURL": f"/api/invoices/{product_id}", "invoiceStoragePath": path}


@router.get("/{product_id}")
def get_product_invoice(product_id: str, user: CurrentUser):
    product = get_product(user["uid"], product_id)
    path = product.get("invoiceStoragePath")
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No invoice is attached to this product.")
    return {
        "invoiceURL": f"/api/invoices/{product_id}/download",
        "invoiceStoragePath": path,
    }


@router.get("/{product_id}/download")
def download_product_invoice(product_id: str, user: CurrentUser):
    product = get_product(user["uid"], product_id)
    path = product.get("invoiceStoragePath")
    if not path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No invoice is attached to this product.")
    file_path = get_invoice_file(path, user["uid"], product_id)
    return FileResponse(
        file_path,
        media_type=invoice_content_type(file_path),
        headers={"Content-Disposition": f'inline; filename="{file_path.name}"'},
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product_invoice(product_id: str, user: CurrentUser):
    product = get_product(user["uid"], product_id)
    path = product.get("invoiceStoragePath")
    if path:
        delete_invoice(path, user["uid"], product_id)
        get_firestore().collection("products").document(product_id).update({
            "invoiceURL": None,
            "invoiceStoragePath": None,
        })
