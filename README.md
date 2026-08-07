# Online Shopping API

A FastAPI backend for online shopping application. The project supports users, categories, products, carts, and orders using PostgreSQL and SQLAlchemy.

## Features

- User registration and login
- Category creation and listing
- Product registration and search
- Cart management
- Order checkout and order history
- Product stock validation
- Swagger API documentation

## Project Structure

```Case Study Prac
app/
├── main.py
├── db/
│   └── base.py
├── models/
│   ├── user.py
│   ├── category.py
│   ├── product.py
│   ├── cart.py
│   └── order.py
├── schemas/
│   ├── user_schema.py
│   ├── product_schema.py
│   ├── cart_schema.py
│   ├── category_schema.py
│   └── order_schema.py
└── routers/
    ├── user_router.py
    ├── category_router.py
    ├── product_router.py
    ├── cart_router.py
    └── order_router.py

This project does not use session.py, repositories, services, utilities, or tests folders.
Main APIs



Method
Endpoint
Purpose




POST
/api/users/register
Register a user


POST
/api/users/login
Log in


POST
/api/categories
Create a category


GET
/api/categories
List categories


POST
/api/products
Add a product


GET
/api/products
List products


GET
/api/products/search
Search products


POST
/api/cart/add
Add an item to cart


GET
/api/cart/{user_id}
View cart


POST
/api/orders/checkout
Place an order


GET
/api/orders/{user_id}
View order history


GET
/api/orders/details/{order_id}
View order details



A category must be created before assigning its ID to a product.
Setup

Create a PostgreSQL database.
Configure the database connection in app/db/base.py.
Install dependencies:

pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic email-validator

Run the application:

uvicorn app.main:app --reload

Open Swagger documentation:

/docs
Validations

Unique and valid user email
Valid password and mobile number
Existing category before product creation
Existing product before adding to cart
Quantity must be greater than zero
Quantity cannot exceed stock
Cart cannot be empty during checkout
Valid payment method
Correct order total calculation