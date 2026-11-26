import os
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException
from app.config import _default_invoice_storage_dir
from app.schemas.product import ProductInput
from app.services.product_service import _expiry_timestamp, get_product
from app.services.storage_service import (
    _invoice_file,
    delete_invoice,
    get_invoice_file,
    upload_invoice,
)
from app.services.warranty_service import add_months, warranty_summary


class WarrantyServiceTests(unittest.TestCase):
    def test_default_invoice_directory_uses_the_user_data_location(self):
        with TemporaryDirectory() as directory:
            overrides = {"LOCALAPPDATA": directory, "XDG_DATA_HOME": directory}
            with patch.dict(os.environ, overrides):
                expected = (
                    Path(directory) / "Warrantly" / "invoices"
                    if os.name == "nt"
                    else Path(directory) / "warrantly" / "invoices"
                )
                self.assertEqual(Path(_default_invoice_storage_dir()), expected)

    def test_add_months_clamps_to_last_day_of_target_month(self):
        self.assertEqual(add_months(date(2024, 1, 31), 1), date(2024, 2, 29))
        self.assertEqual(add_months(date(2024, 2, 29), 12), date(2025, 2, 28))

    def test_expiry_is_persistable_as_a_utc_timestamp(self):
        expiry = _expiry_timestamp(date(2024, 1, 31), 1)
        self.assertEqual(expiry, datetime(2024, 2, 29, tzinfo=timezone.utc))

    def test_status_boundaries_include_expiry_day_and_thirty_day_window(self):
        purchase = date(2025, 1, 1)
        self.assertEqual(warranty_summary(purchase, 12, date(2025, 12, 1))["warrantyStatus"], "active")
        self.assertEqual(warranty_summary(purchase, 12, date(2025, 12, 2))["warrantyStatus"], "expiring")
        self.assertEqual(warranty_summary(purchase, 12, date(2026, 1, 1))["warrantyStatus"], "expiring")
        self.assertEqual(warranty_summary(purchase, 12, date(2026, 1, 2))["warrantyStatus"], "expired")

    def test_product_validation_rejects_negative_warranty_duration(self):
        with self.assertRaises(ValueError):
            ProductInput(
                productName="Camera",
                purchaseDate=date(2025, 1, 1),
                warrantyDuration=-1,
            )

    def test_invoice_upload_validates_file_signature_before_storage(self):
        with self.assertRaises(HTTPException) as context:
            upload_invoice("user-1", "product-1", b"not a pdf", "application/pdf")
        self.assertEqual(context.exception.status_code, 415)

    def test_invoice_is_stored_and_removed_from_local_disk(self):
        with TemporaryDirectory() as directory:
            with patch(
                "app.services.storage_service.get_settings",
                return_value=SimpleNamespace(local_invoice_storage_dir=directory),
            ):
                path = upload_invoice("user-1", "product-1", b"%PDF-1.7 test", "application/pdf")
                file_path = get_invoice_file(path, "user-1", "product-1")
                self.assertEqual(file_path.read_bytes(), b"%PDF-1.7 test")
                delete_invoice(path, "user-1", "product-1")
                self.assertFalse(file_path.exists())

    def test_invoice_path_is_scoped_to_user_and_product(self):
        with TemporaryDirectory() as directory:
            with patch(
                "app.services.storage_service.get_settings",
                return_value=SimpleNamespace(local_invoice_storage_dir=directory),
            ):
                valid = _invoice_file("users/user-1/invoices/product-1/invoice.pdf", "user-1", "product-1")
                self.assertTrue(valid.is_relative_to(directory))
        with self.assertRaises(HTTPException) as context:
            _invoice_file("users/user-2/invoices/product-1/invoice.pdf", "user-1", "product-1")
        self.assertEqual(context.exception.status_code, 403)

    def test_product_lookup_rejects_a_record_owned_by_another_user(self):
        snapshot = Mock(exists=True)
        snapshot.to_dict.return_value = {"userId": "user-2"}
        database = Mock()
        database.collection.return_value.document.return_value.get.return_value = snapshot
        with patch("app.services.product_service.get_firestore", return_value=database):
            with self.assertRaises(HTTPException) as context:
                get_product("user-1", "product-1")
        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
