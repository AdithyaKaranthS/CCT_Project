from datetime import date, datetime, timezone
import io

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.dependencies import CurrentUser
from app.firebase import get_firestore
from app.schemas.claims import ClaimInput
from app.services.product_service import get_product
from google.cloud.firestore_v1 import FieldFilter

router = APIRouter(prefix="/api/claims", tags=["claims"])


@router.get("")
def list_claims(user: CurrentUser):
    snapshots = get_firestore().collection("claims").where(filter=FieldFilter("userId", "==", user["uid"])).stream()
    items = []
    for snapshot in snapshots:
        item = snapshot.to_dict()
        item["claimId"] = snapshot.id
        items.append(item)
    return {"items": sorted(items, key=lambda item: item.get("createdAt", ""), reverse=True)}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_claim(payload: ClaimInput, user: CurrentUser):
    get_product(user["uid"], payload.productId)
    db = get_firestore()
    ref = db.collection("claims").document()
    now = datetime.now(timezone.utc)
    data = payload.model_dump()
    data.update({"claimId": ref.id, "userId": user["uid"], "claimDate": data["claimDate"] or date.today().isoformat(), "createdAt": now, "updatedAt": now})
    ref.set(data)
    data["claimId"] = ref.id
    return data


@router.put("/{claim_id}")
def update_claim(claim_id: str, payload: ClaimInput, user: CurrentUser):
    get_product(user["uid"], payload.productId)
    ref = get_firestore().collection("claims").document(claim_id)
    snapshot = ref.get()
    if not snapshot.exists or snapshot.to_dict().get("userId") != user["uid"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")
    data = payload.model_dump()
    data["updatedAt"] = datetime.now(timezone.utc)
    ref.update(data)
    return {"claimId": claim_id, **snapshot.to_dict(), **data}


@router.delete("/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_claim(claim_id: str, user: CurrentUser):
    ref = get_firestore().collection("claims").document(claim_id)
    snapshot = ref.get()
    if not snapshot.exists or snapshot.to_dict().get("userId") != user["uid"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")
    ref.delete()


@router.get("/eligibility/{product_id}")
def claim_eligibility(product_id: str, user: CurrentUser):
    product = get_product(user["uid"], product_id)
    status_name = product["warrantyStatus"]
    eligible = status_name in {"active", "expiring"}
    if status_name == "expired":
        result = "Expired"
    elif eligible:
        result = "Eligible"
    else:
        result = "Requires manual verification"
    return {"productId": product_id, "eligibility": result, "eligible": eligible,
            "purchaseDate": product["purchaseDate"].isoformat(),
            "warrantyExpiry": product["expiryDate"].isoformat(),
            "warrantyStatus": status_name,
            "disclaimer": "Eligibility does not guarantee manufacturer approval. Manufacturer exclusions and terms may apply."}


@router.get("/{claim_id}/letter")
def generate_claim_letter(claim_id: str, user: CurrentUser):
    ref = get_firestore().collection("claims").document(claim_id)
    snapshot = ref.get()
    if not snapshot.exists or snapshot.to_dict().get("userId") != user["uid"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found.")
    claim = snapshot.to_dict()
    product = get_product(user["uid"], claim["productId"])
    customer_name = user.get("name", "Customer")
    letter_text = (
        f"To the Warranty Claims Department,\n\n"
        f"I am requesting a warranty review for my {product.get('brand', '')} {product['productName']} "
        f"(model {product.get('modelNumber') or 'N/A'}, serial {product.get('serialNumber') or 'N/A'}).\n\n"
        f"The product was purchased on {product['purchaseDate'].isoformat()} and the warranty expires on "
        f"{product['expiryDate'].isoformat()}.\n\nProblem description:\n{claim['problemDescription']}\n\n"
        f"Please review the attached purchase invoice and supporting documentation.\n\n"
        f"Sincerely,\n{customer_name}"
    )
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 55
    pdf.setFont("Helvetica", 11)
    for line in letter_text.splitlines():
        if y < 55:
            pdf.showPage()
            pdf.setFont("Helvetica", 11)
            y = height - 55
        pdf.drawString(55, y, line[:110])
        y -= 16
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={
        "Content-Disposition": f'attachment; filename="warranty-claim-{claim_id}.pdf"',
    })
