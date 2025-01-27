from django.db import models
from django.db.models import Sum, F
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Lower


# Create your models here.
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_info = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('name'), 
                name='unique_supplier_name_case_insensitive'
            )
        ]

    def __str__(self):
        return self.name
    
    def total_inventory_value(self):
        # Calculate total value of all products and their quantities in one query
        total_value = Product.objects.filter(supplier=self) \
            .annotate(total_price=F('price') * F('inventory__quantity')) \
            .aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        return total_value
    

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier = models.ForeignKey(Supplier, related_name='products', on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    

class Inventory(models.Model):
    product = models.OneToOneField(Product, related_name='inventory', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = _('Inventory Level')

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    
    # def get_total_number_of_products(self):
    #     return self.product.count()