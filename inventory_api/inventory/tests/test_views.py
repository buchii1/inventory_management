import os
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
import pandas as pd
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .factories import SupplierFactory, ProductFactory, InventoryFactory


class SupplierAPIViewTestCase(APITestCase):
    def setUp(self):
        self.supplier = SupplierFactory()
        self.supplier_detail_url = reverse("inventory:supplier-detail", args=[self.supplier.id])

    def test_list_suppliers(self):
        response = self.client.get(reverse("inventory:supplier"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], self.supplier.name)

    def test_create_supplier(self):
        data = {"name": "New Supplier", "contact_info": "123 Main St"}
        response = self.client.post(reverse("inventory:supplier"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Supplier")

    def test_update_supplier(self):
        data = {"name": "Updated Supplier", "contact_info": "456 Elm St"}
        response = self.client.put(self.supplier_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Supplier")

    def test_delete_supplier(self):
        response = self.client.delete(self.supplier_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ProductAPIViewTestCase(APITestCase):
    def setUp(self):
        self.product = ProductFactory()
        self.product_detail_url = reverse("inventory:product-detail", args=[self.product.id])

    def test_list_products(self):
        response = self.client.get(reverse("inventory:product-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], self.product.name)

    def test_create_product(self):
        supplier = SupplierFactory()
        data = {
            "name": "New Product",
            "description": "Test Description",
            "price": "20.00",
            "supplier_id": supplier.id,
        }
        response = self.client.post(reverse("inventory:product-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Product")

    def test_update_product(self):
        data = {
            "name": "Updated Product",
            "price": "30.00",
            "description": self.product.description,
            "supplier_id": self.product.supplier.id,
        }
        response = self.client.put(self.product_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Product")
        self.assertEqual(response.data["price"], "30.00")

    def test_delete_product(self):
        response = self.client.delete(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class InventoryAPIViewTestCase(APITestCase):
    def setUp(self):
        self.inventory = InventoryFactory()
        self.inventory_detail_url = reverse("inventory:inventory-detail", args=[self.inventory.id])

    def test_list_inventory(self):
        response = self.client.get(reverse("inventory:inventory"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["quantity"], self.inventory.quantity)

    def test_create_inventory(self):
        product = ProductFactory()
        data = {"product_id": product.id, "quantity": 100}
        response = self.client.post(reverse("inventory:inventory"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity"], 100)

    def test_update_inventory(self):
        data = {"quantity": 50, "product_id": self.inventory.product.id}
        response = self.client.put(self.inventory_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 50)

    def test_delete_inventory(self):
        response = self.client.delete(self.inventory_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ProductCSVUploadTestCase(APITestCase):
    def setUp(self):
        # Create a Supplier instance using the factory
        self.supplier = SupplierFactory(name="company")
        # self.supplier.save()
        self.upload_url = reverse("inventory:product-upload-csv")

    def test_csv_upload_success(self):
        # Create CSV data using the factory-created supplier
        data = {
            'name': ['CSV Product'],
            'description': ['From CSV'],
            'price': [15.99],
            'supplier_name': [self.supplier.name],
            'quantity': [20]
        }

        df = pd.DataFrame(data)
        # Create a CSV file in memory
        csv_file = SimpleUploadedFile("products.csv", df.to_csv(index=False).encode(), content_type="text/csv")

        # Upload the file
        response = self.client.post(self.upload_url, {'file': csv_file}, format='multipart')

        # Debug the response
        print(response.data)  # Check the response for any error messages

        # Assert the response status
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Response error: {response.data}")

        # Check if the product was created
        product_count = ProductFactory._meta.model.objects.count()
        print(f"Product count after upload: {product_count}")  # Check product count

        # Validate that the product has been created
        self.assertEqual(product_count, 1, f"Expected 1 product, but found {product_count}")

        # Check if inventory was created
        inventory_count = InventoryFactory._meta.model.objects.count()
        print(f"Inventory count after upload: {inventory_count}")
        self.assertEqual(inventory_count, 1, f"Expected 1 inventory, but found {inventory_count}")

    def test_csv_upload_missing_columns(self):
        # Create CSV with missing columns
        data = {
            'name': ['Invalid Product'],
            'price': [15.99],
            'supplier_name': [self.supplier.name],
            'quantity': [100]
        }

        df = pd.DataFrame(data)
        csv_file = SimpleUploadedFile("products.csv", df.to_csv(index=False).encode(), content_type="text/csv")

        response = self.client.post(self.upload_url, {'file': csv_file}, format='multipart')

        # Assert that the response is a bad request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required columns", response.data.get("error"))


class InventoryReportViewTestCase(APITestCase):
    def setUp(self):
        self.report_url = reverse("inventory:inventory-report")
        self.media_root = os.path.join(settings.MEDIA_ROOT, "generated_reports")
        self.base_url = settings.BASE_URL

        # Create mock reports directory
        os.makedirs(self.media_root, exist_ok=True)

        # Track test files created during the test
        self.test_files = []

    def tearDown(self):
        # Remove only the test files created during the test
        for file_name in self.test_files:
            file_path = os.path.join(self.media_root, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)

        # Do not remove the directory if it is still in use by other files

    @patch("inventory.views.generate_inventory_report.delay")
    @patch("inventory.views.generate_inventory_report_pdf.apply_async")
    @patch("inventory.views.AsyncResult")  # Mock AsyncResult to simulate task states
    def test_inventory_report_success(self, mock_AsyncResult, mock_generate_inventory_report_pdf, mock_generate_inventory_report):
        # Mock the report generation task
        mock_task = MagicMock()
        mock_task.id = "fake-task-id"
        mock_task.state = "SUCCESS"
        mock_generate_inventory_report.return_value = mock_task

        # Mock the PDF generation task
        mock_pdf_task = MagicMock()
        mock_pdf_task.id = "fake-pdf-task-id"
        mock_generate_inventory_report_pdf.return_value = mock_pdf_task

        # Mock AsyncResult for the PDF generation task
        mock_pdf_result = MagicMock()
        mock_pdf_result.state = "SUCCESS"
        mock_AsyncResult.return_value = mock_pdf_result

        # Simulate the creation of a PDF file in the reports directory
        task_id_prefix = mock_task.id[:8]  # First 8 characters of the task ID
        pdf_file_name = f"report_{task_id_prefix}.pdf"
        pdf_file_path = os.path.join(self.media_root, pdf_file_name)
        with open(pdf_file_path, "w") as f:
            f.write("Mock PDF content")

        # Track the created test file
        self.test_files.append(pdf_file_name)

        # Trigger the API to generate the report
        response = self.client.get(self.report_url)

        # Assert the API response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("status", response.data)
        self.assertIn("pdf_download_link", response.data)
        self.assertEqual(response.data["status"], "Success")

        # Assert the PDF download link matches the expected format
        expected_pdf_url = f"{self.base_url}/media/generated_reports/{pdf_file_name}"
        self.assertEqual(response.data["pdf_download_link"], expected_pdf_url)

        # Verify Celery task calls
        mock_generate_inventory_report.assert_called_once()
        mock_generate_inventory_report_pdf.assert_called_once_with(args=["fake-task-id"])
        mock_AsyncResult.assert_called_once_with("fake-pdf-task-id")


class SupplierProductInventoryAPIViewTestCase(APITestCase):
    def setUp(self):
        # Set up a supplier, products, and inventory using factories
        self.supplier = SupplierFactory(name="Test Supplier")
        self.product1 = ProductFactory(supplier=self.supplier, name="Product 1", price=10.00)
        self.product2 = ProductFactory(supplier=self.supplier, name="Product 2", price=20.00)
        self.inventory1 = InventoryFactory(product=self.product1, quantity=50)
        self.inventory2 = InventoryFactory(product=self.product2, quantity=30)
        self.url = reverse("inventory:supplier-products", args=[self.supplier.id])

    def test_supplier_product_inventory_success(self):
        # Test for a successful retrieval of supplier inventory
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["supplier_name"], self.supplier.name)
        self.assertEqual(response.data["total_products"], 2)
        self.assertEqual(response.data["total_inventory_value"], "1,100.00")

        # Check product details
        products = response.data["products"]
        self.assertEqual(len(products), 2)
        
        # Check first product
        self.assertEqual(products[0]["product"]["name"], "Product 1")
        self.assertEqual(products[0]["quantity"], 50)
        
        # Check second product
        self.assertEqual(products[1]["product"]["name"], "Product 2")
        self.assertEqual(products[1]["quantity"], 30)

    def test_supplier_not_found(self):
        # Test for a supplier that does not exist
        invalid_url = reverse("inventory:supplier-products", args=[999])  # Non-existent ID
        response = self.client.get(invalid_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Supplier not found")
