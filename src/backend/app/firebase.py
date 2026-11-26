import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import HTTPException, status

from app.config import get_settings


def _get_app() -> firebase_admin.App:
    settings = get_settings()
    try:
        return firebase_admin.get_app()
    except ValueError:
        options = {}
        if settings.firebase_project_id:
            options["projectId"] = settings.firebase_project_id
        cred = None
        if settings.google_application_credentials:
            credential_path = Path(settings.google_application_credentials)
            if not credential_path.is_file():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="The configured Firebase service-account file does not exist.",
                )
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credential_path)
            cred = credentials.Certificate(str(credential_path))
        try:
            return firebase_admin.initialize_app(credential=cred, options=options or None)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase is not configured. Set up Application Default Credentials and Firebase environment variables.",
            ) from exc


def get_firestore():
    return firestore.client(_get_app())
