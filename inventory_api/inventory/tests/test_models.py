from django.test import TestCase
from decimal import Decimal
from .factories import SupplierFactory, ProductFactory, InventoryFactory


class SupplierModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.supplier = SupplierFactory()

    def test_supplier_creation(self):
        self.assertEqual(str(self.supplier), self.supplier.name)
        self.assertIsNotNone(self.supplier.contact_info)


class ProductModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = ProductFactory()

    def test_product_creation(self):
        self.assertEqual(str(self.product), self.product.name)
        self.assertGreater(self.product.price, Decimal("0.0"))
        self.assertIsNotNone(self.product.supplier)


class InventoryModelTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.inventory = InventoryFactory()

    def test_inventory_creation(self):
        self.assertEqual(str(self.inventory), f"{self.inventory.product.name} - {self.inventory.quantity}")
        self.assertGreaterEqual(self.inventory.quantity, 0)

    def test_inventory_product_link(self):
        self.assertEqual(self.inventory.product.inventory.quantity, self.inventory.quantity)
