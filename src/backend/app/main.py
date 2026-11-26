from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import analytics, auth, claims, invoices, maintenance, notifications, ocr, products, qr, services, warranties

settings = get_settings()

app = FastAPI(
    title="Cloud Digital Warranty Manager API",
    description="Firebase-backed REST API for product warranties, invoices, service records, and reminders.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Scheduler-Secret"],
)

for route in (
    auth.router,
    products.router,
    warranties.router,
    invoices.router,
    services.router,
    services.global_router,
    notifications.router,
    analytics.router,
    ocr.router,
    qr.router,
    claims.router,
    maintenance.router,
):
    app.include_router(route)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
