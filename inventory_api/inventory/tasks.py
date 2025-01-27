from celery import shared_task
from django.db.models import Sum, F
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table,
    TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from django.conf import settings
from datetime import datetime
import os

from .models import Product, Supplier, Inventory


@shared_task
def generate_inventory_report():
    """
    Generate a report on inventory levels, including:
    - Low stock alerts (based on inventory threshold).
    - Supplier performance metrics.
    - Stock value for each product and overall inventory.
    """

    report = {}

    # Inventory levels and stock value
    inventories = Inventory.objects.select_related('product')  # Optimize queries
    total_stock_value = 0
    report['inventory_levels'] = []

    for inventory in inventories:
        product = inventory.product
        stock_value = product.price * inventory.quantity
        total_stock_value += stock_value

        report['inventory_levels'].append({
            "product_name": product.name,
            "inventory": inventory.quantity,
            "price": product.price,
            "stock_value": stock_value,
            "low_stock_alert": inventory.quantity < 10,  # Threshold for low stock
        })

    # Overall stock value
    report['total_stock_value'] = total_stock_value

    # Supplier performance
    suppliers = Supplier.objects.all()
    report['supplier_performance'] = [
        {
            "supplier_name": supplier.name,
            "total_products_supplied": Product.objects.filter(supplier=supplier).count(),
            "total_inventory": Inventory.objects.filter(product__supplier=supplier).aggregate(
                total_inventory=Sum('quantity')
            )['total_inventory'] or 0,
            "total_stock_value": Inventory.objects.filter(product__supplier=supplier).annotate(
                stock_value=F('product__price') * F('quantity')
            ).aggregate(total_stock_value=Sum('stock_value'))['total_stock_value'] or 0,
        }
        for supplier in suppliers
    ]

    return report


@shared_task
def generate_inventory_report_pdf(task_id):
    """
    Generate a PDF version of the inventory report.
    """

    # Call the `generate_inventory_report` task to fetch the report data
    report = generate_inventory_report()

    # Use the MEDIA_ROOT directory for storing generated reports
    reports_dir = os.path.join(settings.MEDIA_ROOT, "generated_reports")
    os.makedirs(reports_dir, exist_ok=True)  # Ensure the directory exists

    # Define the file path for the PDF
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"report_{timestamp}_{task_id[:8]}.pdf"
    file_path = os.path.join(reports_dir, file_name)

    # Create the PDF document
    pdf = SimpleDocTemplate(file_path, pagesize=letter)
    elements = []

    # Title and Date
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Inventory Report", styles['Title']))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(
        f"Total Stock Value of All Products: ${report['total_stock_value']:,.2f}",
        styles['Normal']
    ))

    # Add spacing before the first table
    elements.append(Spacer(1, 20))

    # Inventory Levels Table
    inventory_data = [["Product Name", "Inventory", "Price", "Stock Value", "Low Stock Alert"]]
    for item in report["inventory_levels"]:
        inventory_data.append([
            item["product_name"],
            f"{item['inventory']:,}",
            f"${item['price']:,.2f}",
            f"${item['stock_value']:,.2f}",
            "Yes" if item["low_stock_alert"] else "No"
        ])

    inventory_table = Table(inventory_data, colWidths=[150, 80, 80, 100, 100])
    inventory_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(inventory_table)

    # Add spacing between tables
    elements.append(Spacer(1, 30))

    # Supplier Performance Table
    supplier_data = [["Supplier Name", "Products Supplied", "Total Inventory", "Total Stock Value"]]
    for supplier in report["supplier_performance"]:
        supplier_data.append([
            supplier["supplier_name"],
            f"{supplier['total_products_supplied']:,}",  # Format products supplied with commas
            f"{supplier['total_inventory']:,}",  # Format inventory with commas
            f"${supplier['total_stock_value']:,.2f}"  # Format stock value with commas
        ])

    supplier_table = Table(supplier_data, colWidths=[150, 120, 120, 120])
    supplier_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.lightyellow),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(supplier_table)

    # Build the PDF
    pdf.build(elements)

    # Return the file path relative to MEDIA_URL for download purposes
    return os.path.join("generated_reports", file_name)
