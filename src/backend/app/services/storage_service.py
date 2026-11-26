import mimetypes
from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import HTTPException, status

from app.config import get_settings

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def _matches_content_type(content: bytes, content_type: str) -> bool:
    if content_type == "application/pdf":
        return content.startswith(b"%PDF-")
    if content_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if content_type == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/webp":
        return len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return False


def _storage_root() -> Path:
    return Path(get_settings().local_invoice_storage_dir).expanduser().resolve()


def _invoice_file(path: str, user_id: str, product_id: str) -> Path:
    expected_prefix = f"users/{user_id}/invoices/{product_id}/"
    relative = PurePosixPath(path)
    if (
        not path.startswith(expected_prefix)
        or relative.is_absolute()
        or ".." in relative.parts
        or "\\" in path
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invoice path is outside this user's product.")
    root = _storage_root()
    file_path = root.joinpath(*relative.parts).resolve()
    try:
        file_path.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invoice path is outside local storage.") from exc
    return file_path


def upload_invoice(user_id: str, product_id: str, content: bytes, content_type: str) -> str:
    extension = ALLOWED_TYPES.get(content_type)
    if extension is None:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Upload a PDF, JPEG, PNG, or WebP invoice.")
    if not _matches_content_type(content, content_type):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="The file contents do not match the declared invoice type.")
    path = f"users/{user_id}/invoices/{product_id}/{uuid4().hex}.{extension}"
    file_path = _invoice_file(path, user_id, product_id)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("xb") as invoice:
        invoice.write(content)
    return path


def get_invoice_file(path: str, user_id: str, product_id: str) -> Path:
    file_path = _invoice_file(path, user_id, product_id)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice file not found in local storage.")
    return file_path


def invoice_content_type(file_path: Path) -> str:
    return mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"


def delete_invoice(path: str, user_id: str, product_id: str) -> None:
    file_path = _invoice_file(path, user_id, product_id)
    if file_path.exists():
        file_path.unlink()
