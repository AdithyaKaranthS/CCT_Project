from datetime import datetime
import io
import re

import fitz
from PIL import Image
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.dependencies import CurrentUser
from app.config import get_settings

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


def _extract_text(content: bytes, content_type: str) -> str:
    if content_type == "application/pdf" or content[:4] == b"%PDF":
        document = fitz.open(stream=content, filetype="pdf")
        return "\n".join(page.get_text() for page in document)
    if content_type.startswith("image/"):
        try:
            image = Image.open(io.BytesIO(content))
            text = ""
            try:
                import pytesseract
                text = pytesseract.image_to_string(image)
            except (ImportError, RuntimeError, OSError):
                text = ""
            return text
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The image could not be read.") from exc
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported invoice format.")


def _date_from_match(value: str) -> str | None:
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return None


@router.post("/extract")
async def extract_invoice(user: CurrentUser, file: UploadFile = File(...)):
    content_type = file.content_type or ""
    if content_type not in {"application/pdf", "image/jpeg", "image/png"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF, JPG, JPEG, and PNG files are supported.")
    content = await file.read(get_settings().max_invoice_bytes + 1)
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty.")
    if len(content) > get_settings().max_invoice_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Invoice files must be 10 MB or smaller.")
    text = _extract_text(content, content_type)
    if not text.strip():
        return {"text": "", "fields": {}, "message": "Text could not be extracted. Enter the invoice details manually."}

    fields: dict[str, str | int] = {}
    product_match = re.search(r"(?im)^\s*(?:product|item)\s*:\s*(.+)$", text)
    brand_match = re.search(r"(?im)^\s*(?:brand|manufacturer)\s*:\s*(.+)$", text)
    model_match = re.search(r"(?im)^\s*(?:model(?:\s*number)?|model\s*no\.?|sku)\s*:\s*(.+)$", text)
    serial_match = re.search(r"(?im)^\s*(?:serial(?:\s*number)?|s/n)\s*:\s*(.+)$", text)
    seller_match = re.search(r"(?im)^\s*(?:seller|store|sold\s*by|retailer)\s*:\s*(.+)$", text)
    invoice_match = re.search(r"(?im)^\s*(?:invoice(?:\s*(?:number|no\.?))?|bill(?:\s*no\.?))\s*:\s*(.+)$", text)
    date_match = re.search(r"(?i)(?:purchase\s*date|invoice\s*date|date)\s*[:\-]\s*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}|\d{4}-\d{2}-\d{2})", text)
    price_match = re.search(r"(?i)(?:amount|total|purchase\s*price|price)\s*[:\-]?\s*([₹$€£]?\s*[\d,]+(?:\.\d+)?)", text)
    warranty_match = re.search(r"(?i)warranty\s*[:\-]?\s*(\d{1,3})\s*(year|month)s?", text)

    if product_match:
        fields["productName"] = product_match.group(1).strip()
    if brand_match:
        fields["brand"] = brand_match.group(1).strip()
    if model_match:
        fields["modelNumber"] = model_match.group(1).strip()
    if serial_match:
        fields["serialNumber"] = serial_match.group(1).strip()
    if seller_match:
        fields["seller"] = seller_match.group(1).strip()
    if invoice_match:
        fields["invoiceNumber"] = invoice_match.group(1).strip()
    if date_match:
        parsed = _date_from_match(date_match.group(1).strip())
        if parsed:
            fields["purchaseDate"] = parsed
    if price_match:
        fields["purchasePrice"] = re.sub(r"[^\d.]", "", price_match.group(1))
    if warranty_match:
        amount = int(warranty_match.group(1))
        fields["warrantyDuration"] = amount * 12 if warranty_match.group(2).lower().startswith("year") else amount
    return {"text": text[:10000], "fields": fields, "message": "Review the extracted details before saving."}
