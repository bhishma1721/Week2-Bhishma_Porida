from app.models.category import Category
from app.models.product import Product


def create_category(
    db_session,
    category_name="Electronics"
):
    """
    Creates a category directly in the temporary test database.

    This helper avoids repeating category creation code
    in multiple product tests.
    """

    category = Category(
        category_name=category_name
    )

    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    return category


def create_product(
    db_session,
    category_id,
    product_name="Laptop",
    is_active=True
):
    """
    Creates a product directly in the temporary test database.
    """

    product = Product(
        product_name=product_name,
        description="Test product",
        price=50000,
        available_quantity=10,
        product_url="https://example.com/laptop",
        category_id=category_id,
        is_active=is_active
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    return product


def test_get_products_route(
    client,
    db_session
):
    """
    Tests the public product listing route.

    Active products should be returned.
    """

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    response = client.get(
        "/products/product"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == product.id
    assert data[0]["product_name"] == "Laptop"
    assert data[0]["is_active"] is True


def test_get_product_by_id_route(
    client,
    db_session
):
    """
    Tests retrieving one active product by ID.
    """

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    response = client.get(
        f"/products/product/{product.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product.id
    assert data["product_name"] == "Laptop"
    assert data["category_id"] == category.id


def test_product_not_found(
    client
):
    """
    Tests product lookup with a non-existing ID.
    """

    response = client.get(
        "/products/product/99999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_search_products_by_name(
    client,
    db_session
):
    """
    Tests product search by product name.
    """

    category = create_category(db_session)

    create_product(
        db_session=db_session,
        category_id=category.id,
        product_name="Gaming Laptop"
    )

    response = client.get(
        "/products/product/search",
        params={
            "name": "Gaming"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["product_name"] == "Gaming Laptop"


def test_search_products_by_category(
    client,
    db_session
):
    """
    Tests product search by category ID.
    """

    category = create_category(
        db_session,
        category_name="Books"
    )

    create_product(
        db_session=db_session,
        category_id=category.id,
        product_name="Python Book"
    )

    response = client.get(
        "/products/product/search",
        params={
            "id": category.id
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["category_id"] == category.id


def test_search_products_not_found(
    client,
    db_session
):
    """
    Tests product search when no product matches.
    """

    category = create_category(db_session)

    create_product(
        db_session=db_session,
        category_id=category.id
    )

    response = client.get(
        "/products/product/search",
        params={
            "name": "NonExistingProduct"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "No products found"


def test_admin_can_create_product(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that an admin can create a product.
    """

    admin = create_user(
        email="admin@example.com",
        role="admin"
    )

    category = create_category(db_session)

    token = login_token(admin.email)

    response = client.post(
        "/products/products/create",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "product_name": "Admin Created Product",
            "description": "Product created by admin",
            "price": 1000,
            "available_quantity": 20,
            "product_url": "https://example.com/product",
            "category_id": category.id
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["product_name"] == "Admin Created Product"
    assert data["price"] == 1000
    assert data["available_quantity"] == 20
    assert data["is_active"] is True


def test_customer_cannot_create_product(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that a customer cannot access the admin
    product creation route.
    """

    customer = create_user(
        email="customer@example.com",
        role="customer"
    )

    category = create_category(db_session)

    token = login_token(customer.email)

    response = client.post(
        "/products/products/create",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "product_name": "Unauthorized Product",
            "description": "This should not be created",
            "price": 1000,
            "available_quantity": 20,
            "product_url": None,
            "category_id": category.id
        }
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Insufficient role permissions"
    )


def test_duplicate_product_is_rejected(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests duplicate product-name validation.
    """

    admin = create_user(
        email="admin@example.com",
        role="admin"
    )

    category = create_category(db_session)

    token = login_token(admin.email)

    product_data = {
        "product_name": "Unique Product",
        "description": "Product description",
        "price": 2000,
        "available_quantity": 5,
        "product_url": None,
        "category_id": category.id
    }

    first_response = client.post(
        "/products/products/create",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=product_data
    )

    second_response = client.post(
        "/products/products/create",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=product_data
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]
        == "Product name is already registered"
    )


def test_admin_can_update_product(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that an admin can update an existing product.
    """

    admin = create_user(
        email="admin@example.com",
        role="admin"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    token = login_token(admin.email)

    response = client.put(
        f"/products/products/update/{product.id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "product_name": "Updated Laptop",
            "description": "Updated product description",
            "price": 60000,
            "available_quantity": 15,
            "product_url": "https://example.com/updated",
            "category_id": category.id
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product.id
    assert data["product_name"] == "Updated Laptop"
    assert data["price"] == 60000
    assert data["available_quantity"] == 15


def test_admin_can_deactivate_product(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests product deactivation.

    After deactivation, the product should not be visible
    through public product routes.
    """

    admin = create_user(
        email="admin@example.com",
        role="admin"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    token = login_token(admin.email)

    response = client.delete(
        f"/products/products/deactivate/{product.id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Product deactivated successfully"
    assert data["product_id"] == product.id

    # Public product detail should no longer return
    # the inactive product.
    detail_response = client.get(
        f"/products/product/{product.id}"
    )

    assert detail_response.status_code == 404
    assert detail_response.json()["detail"] == "Product not found"
