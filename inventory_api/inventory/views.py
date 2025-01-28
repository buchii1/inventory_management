from time import sleep
from decimal import Decimal
import os
import logging
import pandas as pd
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    GenericAPIView
)
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from drf_spectacular.utils import extend_schema
from celery.result import AsyncResult
from django.conf import settings

from .tasks import generate_inventory_report, generate_inventory_report_pdf
from .models import Product, Inventory, Supplier
from .serializers import (
    ProductSerializer,
    InventorySerializer,
    SupplierSerializer,
    ProductCSVUploadSerializer,
    ProductCSVResponseSerializer,
)


logger = logging.getLogger(__name__)


# Define custom pagination settings for the API
class CustomPagination(PageNumberPagination):
    """
    Custom pagination class for setting the default page size, 
    allowing clients to modify page size via query parameters, 
    and enforcing a maximum page size limit.
    """
    page_size = 10  # Default number of items per page
    page_size_query_param = 'page_size'  # Query param to override page size
    max_page_size = 50  # Maximum page size to prevent large responses


# Generic Detail View for reuse
class GenericDetailAPIView(RetrieveUpdateDestroyAPIView):
    """
    A reusable base class for handling GET, PUT, PATCH, 
    and DELETE requests on a single object.
    """
    pass


# Supplier Views
class SupplierAPIView(ListCreateAPIView):
    """
    Handles GET and POST requests for Supplier objects.

    - GET: Retrieve a list of all suppliers.
    - POST: Create a new supplier.
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class SupplierDetailAPIView(GenericDetailAPIView):
    """
    Handles GET, PUT, PATCH, and DELETE requests for a specific supplier.

    - GET: Retrieve a single supplier by its ID.
    - PUT/PATCH: Update an existing supplier's details.
    - DELETE: Remove a supplier from the database.
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


# Product Views
class ProductListCreateAPIView(ListCreateAPIView):
    """
    Handles GET and POST requests for Product objects.

    - GET: Retrieve a paginated list of products.
           Supports filtering by 'name', 'price', and 'supplier__name'.
    - POST: Create a new product.
    """
    queryset = Product.objects.select_related('supplier').order_by("name")
    serializer_class = ProductSerializer

    def get(self, request, *args, **kwargs):
        """
        Override GET to add pagination and filtering for product list.
        """
        # Add pagination and filtering only for GET requests
        self.pagination_class = CustomPagination
        self.filter_backends = [DjangoFilterBackend]
        self.filterset_fields = ('name', 'price', 'supplier__name')
        
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Override POST to handle product creation.
        """
        return super().post(request, *args, **kwargs)


class ProductDetailAPIView(GenericDetailAPIView):
    """
    Handles GET, PUT, PATCH, and DELETE requests for a specific product.

    - GET: Retrieve a single product by its ID.
    - PUT/PATCH: Update an existing product's details.
    - DELETE: Remove a product from the database.
    """
    queryset = Product.objects.select_related('supplier')
    serializer_class = ProductSerializer


# Inventory Views
class InventoryAPIView(ListCreateAPIView):
    """
    Handles GET and POST requests for Inventory objects.

    - GET: Retrieve a list of inventory levels for all products.
    - POST: Create or update inventory levels for a specific product.
    """
    queryset = Inventory.objects.select_related('product')  # Optimize query
    serializer_class = InventorySerializer


class InventoryDetailAPIView(GenericDetailAPIView):
    """
    Handles GET, PUT, PATCH, and DELETE requests for a specific inventory.

    - GET: Retrieve inventory details for a specific product.
    - PUT/PATCH: Update the inventory level for a product.
    - DELETE: Remove inventory details for a product.
    """
    queryset = Inventory.objects.select_related('product')
    serializer_class = InventorySerializer


class SupplierProductInventoryAPIView(GenericAPIView):
    """
    Retrieves all products and their quantities for a given supplier.
    """
    def get(self, request, pk):
        try:
            # Get the supplier
            supplier = Supplier.objects.get(id=pk)

            # Retrieve all products related to the supplier
            products = Product.objects.filter(supplier=supplier)
            
            # Retrieve the total product value
            total_inventory_value = "{:,.2f}".format(supplier.total_inventory_value())

            # Retrieve inventory for each product
            inventory_data = []
            for product in products:
                inventory = Inventory.objects.filter(product=product).first()
                if inventory:
                    # Serialize the product but remove supplier details
                    product_data = ProductSerializer(product).data
                    
                    # Remove the supplier data from the product dictionary
                    if 'supplier' in product_data:
                        del product_data['supplier']
                    
                    inventory_data.append({
                        'product': product_data,
                        'quantity': inventory.quantity
                    })

            # Prepare the response with supplier name, total products, and total value at the top level
            response_data = {
                'supplier_name': supplier.name,
                'total_products': products.count(),
                'total_inventory_value': total_inventory_value,
                'products': inventory_data
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Supplier.DoesNotExist:
            return Response({"error": "Supplier not found"}, status=status.HTTP_404_NOT_FOUND)


class ProductCSVUploadView(GenericAPIView):
    """
    API view to handle uploading and processing of a CSV file 
    containing product information.
    """
    serializer_class = ProductCSVUploadSerializer

    @extend_schema(
    description="Upload a CSV file to import product data",
    request={
        "multipart/form-data": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "format": "binary",
                        "description": "CSV file containing product data"}
            },
            "required": ["file"],
        }
    },
    responses={
        200: ProductCSVResponseSerializer,
    },
)

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests for uploading and processing a CSV file.

        Args:
            request: The HTTP request object containing the file in `request.FILES`.

        Returns:
            Response: A JSON response indicating the result of the file processing,
                      including the count of successfully imported records and
                      details about any errors encountered.

        Raises:
            HTTP 400: If no file is provided or the CSV file is missing required columns.
            HTTP 500: If an unexpected error occurs during processing.
        """
        # Retrieve the file from the request
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data.get("file")
        if not file:
            return Response(
                {"error": "No file provided. Please upload a CSV file."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Read the CSV file into a pandas DataFrame
            data = pd.read_csv(file)

            # Define required columns and check for missing ones
            required_columns = ["name", "description", "price", "supplier_name", "quantity"]
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                return Response(
                    {"error": f"Missing required columns: {', '.join(missing_columns)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            success_count = 0
            errors = []

            # Use a database transaction to ensure atomicity
            with transaction.atomic():
                for _, row in data.iterrows():
                    try:
                        # Clean and validate row data
                        supplier_name = row["supplier_name"].strip()
                        supplier = Supplier.objects.filter(name__iexact=supplier_name).first()
                        if not supplier:
                            raise ValueError(f"Supplier '{row['supplier_name']}' not found.")

                        # Ensure price and quantity are properly typed
                        price = Decimal(row["price"])
                        quantity = int(row["quantity"])
                        if quantity < 0:
                            raise ValueError("Quantity must be a positive integer.")

                        product, created = Product.objects.update_or_create(
                            name=row["name"],
                            defaults={
                                "description": row["description"],
                                "price": price,
                                "supplier": supplier,
                            }
                        )

                        # Update inventory quantity
                        inventory, _ = Inventory.objects.get_or_create(product=product)
                        inventory.quantity += quantity
                        inventory.save()

                        success_count += 1
                    except Exception as e:
                        errors.append({"row": row.to_dict(), "error": str(e)})

            response_data = {
                "message": "File processed successfully",
                "success_count": success_count,
                "error_count": len(errors),
                "errors": errors,
            }
            response_serializer = ProductCSVResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)

            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to process file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InventoryReportView(APIView):
    """
    Trigger the generation of the inventory report.
    """

    def get(self, request, *args, **kwargs):
        try:
            # Trigger report generation task
            logger.info("Triggering generate_inventory_report task.")
            task = generate_inventory_report.delay()
            logger.info("Task triggered with ID: %s", task.id)

            # Wait for the report to be generated
            logger.info("Waiting for the report task (ID: %s) to complete.", task.id)
            while task.state not in ['SUCCESS', 'FAILURE']:
                logger.debug("Task (ID: %s) state: %s. Retrying in 2 seconds.", task.id, task.state)
                sleep(2)  # Check every 2 seconds

            if task.state == 'SUCCESS':
                logger.info("Report task (ID: %s) completed successfully. Triggering PDF generation.", task.id)

                # Trigger PDF generation task
                pdf_task_id = generate_inventory_report_pdf.apply_async(args=[task.id]).id
                logger.info("PDF generation task triggered with ID: %s", pdf_task_id)

                # Wait for the PDF to be generated
                logger.info("Waiting for the PDF task (ID: %s) to complete.", pdf_task_id)
                while True:
                    pdf_task_result = AsyncResult(pdf_task_id)
                    logger.debug("PDF task (ID: %s) state: %s.", pdf_task_id, pdf_task_result.state)
                    if pdf_task_result.state == 'SUCCESS':
                        logger.info("PDF generation task (ID: %s) succeeded.", pdf_task_id)
                        break
                    elif pdf_task_result.state == 'FAILURE':
                        logger.error("PDF generation task (ID: %s) failed.", pdf_task_id)
                        return Response({
                            "status": "Failure",
                            "message": "PDF generation failed."
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    sleep(2)  # Check every 2 seconds

                # Locate the generated PDF
                task_id_prefix = task.id[:8]  # First 8 characters of the task_id
                reports_dir = os.path.join(settings.MEDIA_ROOT, "generated_reports")
                logger.info("Searching for PDF file with prefix '%s' in directory: %s.", task_id_prefix, reports_dir)

                try:
                    pdf_file_name = next(
                        (file for file in os.listdir(reports_dir) if file.endswith(f"{task_id_prefix}.pdf")),
                        None
                    )
                except FileNotFoundError as e:
                    logger.exception("The directory '%s' does not exist.", reports_dir)
                    return Response({
                        "status": "Failure",
                        "message": "Reports directory not found."
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Exception as e:
                    logger.exception("An error occurred while searching for the PDF file: %s", str(e))
                    return Response({
                        "status": "Failure",
                        "message": "Error while locating PDF file."
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                if pdf_file_name:
                    # Build the absolute URL for the generated PDF file
                    pdf_download_link = f"{settings.BASE_URL}/media/generated_reports/{pdf_file_name}"
                    logger.info("Found PDF file: %s. Returning download link.", pdf_file_name)
                    return Response({
                        "status": "Success",
                        "pdf_download_link": pdf_download_link
                    }, status=status.HTTP_200_OK)
                else:
                    logger.error("PDF file not found with prefix: %s in directory: %s.", task_id_prefix, reports_dir)
                    return Response({
                        "status": "Failure",
                        "message": "PDF file not found."
                    }, status=status.HTTP_404_NOT_FOUND)

            else:
                logger.error("Report generation task (ID: %s) failed with state: %s.", task.id, task.state)
                return Response({
                    "status": "Failure",
                    "message": "Report generation failed."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception("An unexpected error occurred while processing the report: %s", str(e))
            return Response({
                "status": "Failure",
                "error": f"An error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
