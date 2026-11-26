import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_and_openapi_are_public(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/openapi.json").status_code, 200)

    def test_all_user_data_routes_require_a_firebase_token(self):
        product = {
            "productName": "Camera",
            "purchaseDate": "2025-01-01",
            "warrantyDuration": 12,
        }
        service = {
            "serviceDate": "2025-02-01",
            "provider": "Repair shop",
            "description": "Sensor cleaning",
            "cost": 25,
        }
        requests = [
            ("GET", "/api/auth/me", None),
            ("GET", "/api/products", None),
            ("POST", "/api/products", product),
            ("GET", "/api/products/product-1", None),
            ("PUT", "/api/products/product-1", product),
            ("DELETE", "/api/products/product-1", None),
            ("GET", "/api/warranties/expiring", None),
            ("GET", "/api/invoices/product-1", None),
            ("GET", "/api/invoices/product-1/download", None),
            ("POST", "/api/products/product-1/services", service),
            ("GET", "/api/products/product-1/services", None),
            ("PUT", "/api/products/product-1/services/service-1", service),
            ("DELETE", "/api/products/product-1/services/service-1", None),
            ("GET", "/api/services", None),
            ("GET", "/api/notifications", None),
            ("PATCH", "/api/notifications/notice-1/read", None),
            ("GET", "/api/analytics", None),
            ("POST", "/api/ocr/extract", None),
            ("POST", "/api/qr/product-1", None),
            ("GET", "/api/qr/product-1/download", None),
            ("GET", "/api/qr/scan/product-1", None),
            ("GET", "/api/claims", None),
            ("POST", "/api/claims", {"productId": "product-1", "problemDescription": "Not working"}),
            ("GET", "/api/claims/eligibility/product-1", None),
            ("GET", "/api/maintenance", None),
            ("POST", "/api/maintenance", {"productId": "product-1", "maintenanceTitle": "Cleaning", "scheduledDate": "2026-12-01"}),
        ]
        for method, path, body in requests:
            with self.subTest(method=method, path=path):
                response = self.client.request(method, path, json=body)
                self.assertEqual(response.status_code, 401, response.text)

    def test_invoice_upload_requires_authentication(self):
        response = self.client.post(
            "/api/invoices/product-1",
            files={"file": ("invoice.pdf", b"%PDF-1.7", "application/pdf")},
        )
        self.assertEqual(response.status_code, 401)

    def test_scheduler_endpoint_rejects_missing_secret(self):
        response = self.client.post("/api/notifications/scheduled")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
