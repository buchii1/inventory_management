import factory
from decimal import Decimal
from inventory.models import Supplier, Product, Inventory

class SupplierFactory(factory.django.DjangoModelFactory):
    """
    Factory for the Supplier model.
    """
    class Meta:
        model = Supplier

    name = factory.Faker("company")
    contact_info = factory.Faker("address")


class ProductFactory(factory.django.DjangoModelFactory):
    """
    Factory for the Product model.
    """
    class Meta:
        model = Product

    name = factory.Faker("word")
    description = factory.Faker("text", max_nb_chars=200)
    price = factory.LazyFunction(lambda: Decimal("10.99"))
    supplier = factory.SubFactory(SupplierFactory)


class InventoryFactory(factory.django.DjangoModelFactory):
    """
    Factory for the Inventory model.
    """
    class Meta:
        model = Inventory

    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker("random_int", min=0, max=100)
