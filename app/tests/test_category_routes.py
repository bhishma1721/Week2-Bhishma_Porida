from app.models.category import Category


def create_category(
    db_session,
    category_name="Electronics"
):
    """
    Creates a category directly in the temporary test database.

    This helper is used to prepare data for category tests.
    """

    category = Category(
        category_name=category_name
    )

    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    return category


def test_category_list_route(
    client,
    db_session
):
    """
    Tests the public category-list route.
    """

    category = create_category(
        db_session,
        category_name="Electronics"
    )

    response = client.get(
        "/categories/category/list"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == category.id
    assert data[0]["category_name"] == "Electronics"


def test_admin_can_create_category(
    client,
    create_user,
    login_token
):
    """
    Tests that an admin can create a category.
    """

    admin = create_user(
        email="admin@example.com",
        role="admin"
    )

    token = login_token(admin.email)

    response = client.post(
        "/categories/category/create",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "category_name": "Books"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["category_name"] == "Books"
    assert "id" in data


def test_customer_cannot_create_category(
    client,
    create_user,
    login_token
):
    """
    Tests that a customer cannot create a category.
    """

    customer = create_user(
        email="customer@example.com",
        role="customer"
    )

    token = login_token(customer.email)

    response = client.post(
        "/categories/category/create",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "category_name": "Unauthorized Category"
        }
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "Insufficient role permissions"
    )


def test_duplicate_category_is_rejected(
    client,
    create_user,
    login_token
):
    """
    Tests duplicate category-name validation.

    According to your current router, duplicate category
    creation returns HTTP 404.
    """

    admin = create_user(
        email="admin@example.com",
        role="admin"
    )

    token = login_token(admin.email)

    category_data = {
        "category_name": "Duplicate Category"
    }

    first_response = client.post(
        "/categories/category/create",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=category_data
    )

    second_response = client.post(
        "/categories/category/create",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=category_data
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 404

    assert (
        second_response.json()["detail"]
        == "Category is already registered"
    )


def test_admin_can_update_category(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that an admin can update a category.
    """

    admin = create_user(
        email="admin@example.com",
        role="admin"
    )

    category = create_category(
        db_session,
        category_name="Old Category"
    )

    token = login_token(admin.email)

    response = client.put(
        f"/categories/category/update/{category.id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "category_name": "Updated Category"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == category.id
    assert data["category_name"] == "Updated Category"


def test_customer_cannot_update_category(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that a customer cannot update a category.
    """

    customer = create_user(
        email="customer@example.com",
        role="customer"
    )

    category = create_category(
        db_session,
        category_name="Customer Category"
    )

    token = login_token(customer.email)

    response = client.put(
        f"/categories/category/update/{category.id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "category_name": "Unauthorized Update"
        }
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "Insufficient role permissions"
    )


def test_duplicate_category_update_is_rejected(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests duplicate category-name validation during update.
    """

    admin = create_user(
        email="admin@example.com",
        role="admin"
    )

    first_category = create_category(
        db_session,
        category_name="First Category"
    )

    create_category(
        db_session,
        category_name="Second Category"
    )

    token = login_token(admin.email)

    response = client.put(
        f"/categories/category/update/{first_category.id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "category_name": "Second Category"
        }
    )

    assert response.status_code == 409

    assert (
        response.json()["detail"]
        == "Category is already registered"
    )


def test_update_missing_category(
    client,
    create_user,
    login_token
):
    """
    Tests updating a category that does not exist.
    """

    admin = create_user(
        email="admin@example.com",
        role="admin"
    )

    token = login_token(admin.email)

    response = client.put(
        "/categories/category/update/99999",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "category_name": "Missing Category"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_invalid_category_input(
    client,
    create_user,
    login_token
):
    """
    Tests Pydantic validation for an empty category name.
    """

    admin = create_user(
        email="admin@example.com",
        role="admin"
    )

    token = login_token(admin.email)

    response = client.post(
        "/categories/category/create",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "category_name": ""
        }
    )

    assert response.status_code == 422
