from fastapi import APIRouter, Query, Response, status

from app.dependencies import CurrentUser
from app.schemas.product import ProductInput
from app.services import product_service

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def get_products(
    user: CurrentUser,
    search: str | None = Query(default=None, max_length=120),
    category: str | None = Query(default=None, max_length=60),
):
    return {"items": product_service.list_products(user["uid"], search, category)}


@router.post("", status_code=status.HTTP_201_CREATED)
def add_product(payload: ProductInput, user: CurrentUser):
    return product_service.create_product(user["uid"], payload.model_dump())


@router.get("/{product_id}")
def get_product(product_id: str, user: CurrentUser):
    return product_service.get_product(user["uid"], product_id)


@router.put("/{product_id}")
def edit_product(product_id: str, payload: ProductInput, user: CurrentUser):
    return product_service.update_product(user["uid"], product_id, payload.model_dump())


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_product(product_id: str, user: CurrentUser):
    product_service.delete_product(user["uid"], product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
