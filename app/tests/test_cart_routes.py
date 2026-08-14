from app.models.category import Category
from app.models.product import Product
from app.models.cart import CartItem


def create_category(
    db_session,
    category_name="Electronics"
):
    """
    Creates a category in the temporary test database.
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
    available_quantity=10
):
    """
    Creates an active product for cart testing.
    """

    product = Product(
        product_name=product_name,
        description="Test product",
        price=50000,
        available_quantity=available_quantity,
        product_url="https://example.com/product",
        category_id=category_id,
        is_active=True
    )

    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)

    return product


def create_cart_item(
    db_session,
    user_id,
    product_id,
    quantity=2
):
    """
    Creates a cart item directly in the temporary database.
    """

    cart_item = CartItem(
        user_id=user_id,
        product_id=product_id,
        quantity=quantity
    )

    db_session.add(cart_item)
    db_session.commit()
    db_session.refresh(cart_item)

    return cart_item


def auth_headers(token):
    """
    Creates the Authorization header required by protected routes.
    """

    return {
        "Authorization": f"Bearer {token}"
    }


def test_add_to_cart(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests adding a product to the authenticated user's cart.
    """

    user = create_user(
        email="customer@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    token = login_token(user.email)

    response = client.post(
        "/cart/add",
        headers=auth_headers(token),
        json={
            "user_id": user.id,
            "product_id": product.id,
            "quantity": 2
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["user_id"] == user.id
    assert data[0]["product_id"] == product.id
    assert data[0]["quantity"] == 2


def test_add_existing_product_increases_quantity(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests adding the same product twice.

    The route should increase the existing cart quantity
    instead of creating another cart item.
    """

    user = create_user(
        email="quantity@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id,
        available_quantity=10
    )

    token = login_token(user.email)

    first_response = client.post(
        "/cart/add",
        headers=auth_headers(token),
        json={
            "user_id": user.id,
            "product_id": product.id,
            "quantity": 2
        }
    )

    second_response = client.post(
        "/cart/add",
        headers=auth_headers(token),
        json={
            "user_id": user.id,
            "product_id": product.id,
            "quantity": 3
        }
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    data = second_response.json()

    assert len(data) == 1
    assert data[0]["quantity"] == 5


def test_add_to_cart_exceeding_stock_is_rejected(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that a quantity greater than available stock
    is rejected.
    """

    user = create_user(
        email="stock@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id,
        available_quantity=2
    )

    token = login_token(user.email)

    response = client.post(
        "/cart/add",
        headers=auth_headers(token),
        json={
            "user_id": user.id,
            "product_id": product.id,
            "quantity": 3
        }
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Requested quantity exceeds available stock"
    )


def test_user_cannot_add_to_another_users_cart(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests cart ownership during add-to-cart.
    """

    first_user = create_user(
        email="first@example.com",
        role="customer"
    )

    second_user = create_user(
        email="second@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    token = login_token(first_user.email)

    response = client.post(
        "/cart/add",
        headers=auth_headers(token),
        json={
            # This belongs to second_user, not first_user.
            "user_id": second_user.id,
            "product_id": product.id,
            "quantity": 1
        }
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "You can manage only your own cart"
    )


def test_view_own_cart(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests viewing the authenticated user's own cart.
    """

    user = create_user(
        email="view-cart@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    create_cart_item(
        db_session=db_session,
        user_id=user.id,
        product_id=product.id,
        quantity=2
    )

    token = login_token(user.email)

    response = client.get(
        f"/cart/{user.id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["user_id"] == user.id
    assert data[0]["product_id"] == product.id
    assert data[0]["quantity"] == 2


def test_user_cannot_view_another_users_cart(
    client,
    create_user,
    login_token
):
    """
    Tests that a user cannot view another user's cart.
    """

    first_user = create_user(
        email="cart-owner@example.com",
        role="customer"
    )

    second_user = create_user(
        email="other-cart-user@example.com",
        role="customer"
    )

    token = login_token(first_user.email)

    response = client.get(
        f"/cart/{second_user.id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "You can view only your own cart"
    )


def test_update_cart_quantity(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests updating the quantity of an own cart item.
    """

    user = create_user(
        email="update-cart@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id,
        available_quantity=10
    )

    cart_item = create_cart_item(
        db_session=db_session,
        user_id=user.id,
        product_id=product.id,
        quantity=2
    )

    token = login_token(user.email)

    response = client.put(
        f"/cart/update/{cart_item.id}",
        headers=auth_headers(token),
        json={
            "quantity": 5
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == cart_item.id
    assert data["quantity"] == 5


def test_update_cart_exceeding_stock_is_rejected(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that cart quantity cannot be updated above stock.
    """

    user = create_user(
        email="update-stock@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id,
        available_quantity=3
    )

    cart_item = create_cart_item(
        db_session=db_session,
        user_id=user.id,
        product_id=product.id,
        quantity=1
    )

    token = login_token(user.email)

    response = client.put(
        f"/cart/update/{cart_item.id}",
        headers=auth_headers(token),
        json={
            "quantity": 4
        }
    )

    assert response.status_code == 400

    assert (
        response.json()["detail"]
        == "Requested quantity exceeds available stock"
    )


def test_user_cannot_update_another_users_cart_item(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests ownership validation during cart update.
    """

    cart_owner = create_user(
        email="update-owner@example.com",
        role="customer"
    )

    another_user = create_user(
        email="update-other@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    cart_item = create_cart_item(
        db_session=db_session,
        user_id=cart_owner.id,
        product_id=product.id,
        quantity=2
    )

    token = login_token(another_user.email)

    response = client.put(
        f"/cart/update/{cart_item.id}",
        headers=auth_headers(token),
        json={
            "quantity": 5
        }
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "You can update only your own cart item"
    )


def test_remove_cart_item(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests removing an own cart item.
    """

    user = create_user(
        email="remove-cart@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    cart_item = create_cart_item(
        db_session=db_session,
        user_id=user.id,
        product_id=product.id,
        quantity=2
    )

    token = login_token(user.email)

    response = client.delete(
        f"/cart/remove/{cart_item.id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200

    assert (
        response.json()["message"]
        == "Cart item removed successfully"
    )


def test_user_cannot_remove_another_users_cart_item(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests ownership validation during cart removal.
    """

    cart_owner = create_user(
        email="remove-owner@example.com",
        role="customer"
    )

    another_user = create_user(
        email="remove-other@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    cart_item = create_cart_item(
        db_session=db_session,
        user_id=cart_owner.id,
        product_id=product.id,
        quantity=2
    )

    token = login_token(another_user.email)

    response = client.delete(
        f"/cart/remove/{cart_item.id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 403

    assert (
        response.json()["detail"]
        == "You can remove only your own cart item"
    )


def test_cart_route_requires_authentication(
    client
):
    """
    Tests that the cart route rejects requests without a JWT.
    """

    response = client.get(
        "/cart/1"
    )

    assert response.status_code == 401
