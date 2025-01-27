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
- **POST /upload-csv**: Upload and process a CSV file to import product information. The system validates and processes the file, providing feedback on the number of successful records and errors.

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
- PostgreSQL (if running locally without Docker)

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/inventory-management-system.git
   cd inventory-management-system
   ```

2. **Set up environment variables**:
   - Rename the `.env.example` file in the root directory and populate the fields
   - Update the DJANGO_ENV to match your environment (`development` or `production`)

3. **Build and run the Docker containers**:
   ```bash
   docker-compose up --build
   ```

4. **Run migrations**:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

5. **Access the application**:
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

## Deployment
1. **Build Docker Image**:
   ```bash
   docker build -t inventory-api:latest .
   ```

2. **Push to a Container Registry** (e.g., Docker Hub):
   ```bash
   docker tag inventory-api:latest your-dockerhub-username/inventory-api:latest
   docker push your-dockerhub-username/inventory-api:latest
   ```

3. **Deploy to a Platform**:
   - Platforms such as AWS, DigitalOcean, or Heroku can be used for hosting.
   - Ensure to update environment variables and secrets in the deployment environment.

---

## Design Choices
- **Django REST Framework**: Selected for its robust ecosystem and ease of integration with tools like Celery, PostgreSQL, and Redis.
- **Docker**: To ensure the application runs consistently across different environments.
- **Celery**: Handles background tasks like report generation to improve API responsiveness.
- **Pandas**: Efficiently processes large CSV files for bulk data import.
- **WeasyPrint**: Generates clean and professional PDF reports.

---

## Challenges Faced
1. **Efficient CSV Processing**:
   - Used `pandas` for efficient data validation and transformation.
   - Implemented database transactions to ensure atomicity.
2. **Asynchronous Task Management**:
   - Integrated Celery with Redis for handling long-running tasks.
   - Used polling mechanisms to track task status.
3. **Scalability**:
   - Dockerized the application for easy scaling and deployment.
   - Optimized database queries using `select_related` and bulk operations.

---
