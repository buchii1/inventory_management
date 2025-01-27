from django.urls import path

from . import views

app_name = 'inventory'

urlpatterns = [
    path('suppliers/', views.SupplierAPIView.as_view(), name="supplier"),
    path('suppliers/<int:pk>/', views.SupplierDetailAPIView.as_view(), name="supplier-detail"),
    path('products/', views.ProductListCreateAPIView.as_view(), name="product-list"),
    path('products/<int:pk>/', views.ProductDetailAPIView.as_view(), name="product-detail"),
    path('inventory/', views.InventoryAPIView.as_view(), name="inventory"),
    path('inventory/<int:pk>/', views.InventoryDetailAPIView.as_view(), name="inventory-detail"),
    path('products/upload-csv/', views.ProductCSVUploadView.as_view(), name='product-upload-csv'),
    path('inventory-report/', views.InventoryReportView.as_view(), name='inventory-report'),
    path('suppliers/<int:pk>/products/', views.SupplierProductInventoryAPIView.as_view(), name='supplier-products'),
]
