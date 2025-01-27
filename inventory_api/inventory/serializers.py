from django.db.utils import IntegrityError
from rest_framework import serializers
from .models import Product, Inventory, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    """
    DocString
    """
    class Meta:
        model = Supplier
        fields = '__all__'

    def create(self, validated_data):
        """
        Handle duplicate name errors gracefully during supplier creation.
        """
        try:
            return Supplier.objects.create(**validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {"name": "A supplier with this name already exists (case-insensitive)."}
            )


class ProductSerializer(serializers.ModelSerializer):
    """
    DocString
    """
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source='supplier',
        write_only=True
    )

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'supplier', 'supplier_id']


# class SupplierProductInventoryResponseSerializer(serializers.Serializer):
#     """
#     Response serializer for Supplier Product Inventory.
#     """
#     supplier_name = serializers.CharField()
#     total_products = serializers.IntegerField()
#     total_inventory_value = serializers.DecimalField(max_digits=10, decimal_places=2)
#     products = ProductInventorySerializer(many=True)


class InventorySerializer(serializers.ModelSerializer):
    """
    DocString
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )

    class Meta:
        model = Inventory
        fields = ['id', 'product', 'product_id', 'quantity']


class ProductCSVUploadSerializer(serializers.Serializer):
    """
    DocString
    """
    file = serializers.FileField()


class ProductCSVResponseSerializer(serializers.Serializer):
    """
    DocString
    """
    message = serializers.CharField()
    success_count = serializers.IntegerField()
    error_count = serializers.IntegerField()
    errors = serializers.ListField(
        child=serializers.DictField()
    )
