# Inventory Management System

## Overview
The **Inventory Management System** is a RESTful API built using **Django REST Framework (DRF)** to manage products, suppliers, and inventory levels. It includes features for uploading product information via CSV, generating inventory reports, and handling large-scale data efficiently using Celery for background tasks. The system is Dockerized for easy deployment and scalability.

---

## Features
### Products
- **GET /products**: List all products with pagination and filtering options (by name, price, or supplier).
- **POST /products**: Add a new product with fields like `name`, `description`, `price`, and `supplier`.
- **PUT /products/{id}**: Update an existing product.
- **DELETE /products/{id}**: Remove a product.

### Suppliers
- **GET /suppliers**: List all suppliers.
- **POST /suppliers**: Add a new supplier with fields like `name` and `contact information`.
- **PUT /suppliers/{id}**: Update a supplier.
- **DELETE /suppliers/{id}**: Remove a supplier.

### Inventory Levels
- **GET /inventory**: Check inventory levels for all products.
- **POST /inventory**: Update inventory levels for a product (`product_id`, `quantity`).

### File Handling
- **POST /upload-csv**: Upload and process a CSV file to import product information. The system validates and processes the file, providing feedback on the number of successful records and errors. The file must be in CSV format (.csv) and include the following required columns: name (product name), description (product description), price (decimal value for product price), supplier_name (supplier name matching an existing supplier), and quantity (positive integer for stock quantity). Any additional columns will be ignored. Rows with invalid data, such as missing suppliers or incorrect data types, are logged as errors, while valid rows are processed successfully.

### Reporting
- Generate detailed reports on:
  - Inventory levels
  - Low stock alerts
  - Supplier performance metrics
- Reports are generated using background tasks and can be downloaded in PDF format.

---

## Tech Stack
- **Backend**: Django REST Framework (DRF)
- **Task Queue**: Celery with Redis as the message broker
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose
- **File Handling**: Pandas for processing CSV files
- **PDF Generation**: Reportlab
- **Testing**: pytest and Django test framework
- **Documentation**: drf-spectacular for OpenAPI (Swagger) documentation

---

## Installation and Setup
### Prerequisites
- Docker & Docker Compose installed
- Python 3.10 or above
- PostgreSQL (prod)
- sqlite3 (dev)

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/buchii1/inventory-management.git
   cd inventory-management-system
   ```

2. **Set up environment variables**:
   - Rename the `.env.example` file in the root directory and populate the fields
   - Update the DJANGO_ENV to match your environment (`development` or `production`)

3. **Build and run the Docker containers**:
   ```bash
   docker-compose up --build
   ```

4. **Access the application**:
   - API: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
   - Admin Panel: [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## API Documentation
- The API documentation is available at: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- It provides detailed information about all endpoints, request parameters, and response formats.

---

## Testing
1. **Run Tests**:
   ```bash
   docker-compose exec web pytest
   ```

2. **View Coverage Report**:
   ```bash
   docker-compose exec web pytest --cov=inventory
   ```

---

## Design Choices
- **Django REST Framework**: Selected for its robust ecosystem and ease of integration with tools like Celery, PostgreSQL, and Redis.
- **Docker**: To ensure the application runs consistently across different environments.
- **Celery**: Handles background tasks like report generation to improve API responsiveness.
- **Pandas**: Efficiently processes large CSV files for bulk data import.
- **Reportlab**: Generates clean and professional PDF reports.

---