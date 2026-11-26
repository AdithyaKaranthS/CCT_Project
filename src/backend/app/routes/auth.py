from datetime import datetime, timezone

from fastapi import APIRouter

from app.dependencies import CurrentUser
from app.firebase import get_firestore

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.get("/me")
def get_profile(user: CurrentUser):
    profile = {
        "uid": user["uid"],
        "email": user.get("email"),
        "name": user.get("name"),
        "emailVerified": user.get("email_verified", False),
    }
    get_firestore().collection("users").document(user["uid"]).set(
        {**profile, "updatedAt": datetime.now(timezone.utc)},
        merge=True,
    )
    return profile
