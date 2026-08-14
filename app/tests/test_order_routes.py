from datetime import datetime

from app.models.category import Category
from app.models.product import Product
from app.models.cart import CartItem
from app.models.order import Order, OrderDetail


def auth_headers(token):
    """
    Creates the Bearer Authorization header
    required by protected routes.
    """

    return {
        "Authorization": f"Bearer {token}"
    }


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
    available_quantity=10,
    is_active=True
):
    """
    Creates a product in the temporary test database.
    """

    product = Product(
        product_name=product_name,
        description="Test product",
        price=50000,
        available_quantity=available_quantity,
        product_url="https://example.com/product",
        category_id=category_id,
        is_active=is_active
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
    Creates a cart item directly in the test database.

    Direct database creation is useful for preparing
    checkout test scenarios.
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


def create_order(
    db_session,
    user_id,
    product_id,
    quantity=2,
    price=50000
):
    """
    Creates an order and its order detail directly
    in the temporary database.
    """

    order = Order(
        user_id=user_id,
        order_date=datetime.utcnow(),
        payment_method="CARD",
        total_amount=quantity * price
    )

    db_session.add(order)

    # flush() sends the order to the database so that
    # order.id becomes available before commit().
    db_session.flush()

    order_detail = OrderDetail(
        order_id=order.id,
        product_id=product_id,
        quantity=quantity,
        price=price
    )

    db_session.add(order_detail)
    db_session.commit()
    db_session.refresh(order)

    return order


def test_checkout_success(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests successful checkout.

    This also verifies that the async checkout route
    works through FastAPI TestClient.
    """

    user = create_user(
        email="checkout@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id,
        available_quantity=10
    )

    create_cart_item(
        db_session=db_session,
        user_id=user.id,
        product_id=product.id,
        quantity=2
    )

    token = login_token(user.email)

    response = client.post(
        "/orders/checkout",
        headers=auth_headers(token),
        json={
            "user_id": user.id,
            "payment_method": "CARD"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user.id
    assert data["payment_method"] == "CARD"
    assert float(data["total_amount"]) == 100000.0

    assert len(data["details"]) == 1
    assert data["details"][0]["product_id"] == product.id
    assert data["details"][0]["quantity"] == 2

    # The cart should be cleared after checkout.
    remaining_cart_item = (
        db_session.query(CartItem)
        .filter(CartItem.user_id == user.id)
        .first()
    )

    assert remaining_cart_item is None

    # Stock should decrease after successful checkout.
    updated_product = (
        db_session.query(Product)
        .filter(Product.id == product.id)
        .first()
    )

    assert updated_product.available_quantity == 8


def test_checkout_empty_cart(
    client,
    create_user,
    login_token
):
    """
    Tests checkout when the user's cart is empty.
    """

    user = create_user(
        email="empty-cart@example.com",
        role="customer"
    )

    token = login_token(user.email)

    response = client.post(
        "/orders/checkout",
        headers=auth_headers(token),
        json={
            "user_id": user.id,
            "payment_method": "CARD"
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty"


def test_checkout_insufficient_stock(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests checkout when requested quantity is greater
    than the available product stock.
    """

    user = create_user(
        email="insufficient-stock@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id,
        available_quantity=1
    )

    create_cart_item(
        db_session=db_session,
        user_id=user.id,
        product_id=product.id,
        quantity=3
    )

    token = login_token(user.email)

    response = client.post(
        "/orders/checkout",
        headers=auth_headers(token),
        json={
            "user_id": user.id,
            "payment_method": "UPI"
        }
    )

    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]


def test_checkout_inactive_product(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that an inactive product cannot be ordered.
    """

    user = create_user(
        email="inactive-product@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id,
        is_active=False
    )

    create_cart_item(
        db_session=db_session,
        user_id=user.id,
        product_id=product.id,
        quantity=1
    )

    token = login_token(user.email)

    response = client.post(
        "/orders/checkout",
        headers=auth_headers(token),
        json={
            "user_id": user.id,
            "payment_method": "CASH_ON_DELIVERY"
        }
    )

    assert response.status_code == 404
    assert "unavailable" in response.json()["detail"]


def test_user_cannot_checkout_for_another_user(
    client,
    create_user,
    login_token
):
    """
    Tests checkout ownership validation.
    """

    first_user = create_user(
        email="first-checkout@example.com",
        role="customer"
    )

    second_user = create_user(
        email="second-checkout@example.com",
        role="customer"
    )

    token = login_token(first_user.email)

    response = client.post(
        "/orders/checkout",
        headers=auth_headers(token),
        json={
            # This belongs to second_user.
            "user_id": second_user.id,
            "payment_method": "CARD"
        }
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You can place orders only for yourself"
    )


def test_get_own_order_details(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that a customer can view their own order details.
    """

    user = create_user(
        email="order-owner@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    order = create_order(
        db_session=db_session,
        user_id=user.id,
        product_id=product.id
    )

    token = login_token(user.email)

    response = client.get(
        f"/orders/details/{order.id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order.id
    assert data["user_id"] == user.id
    assert data["payment_method"] == "CARD"
    assert len(data["details"]) == 1


def test_user_cannot_view_another_users_order(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests order ownership protection.
    """

    order_owner = create_user(
        email="real-order-owner@example.com",
        role="customer"
    )

    another_user = create_user(
        email="different-order-user@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    order = create_order(
        db_session=db_session,
        user_id=order_owner.id,
        product_id=product.id
    )

    token = login_token(another_user.email)

    response = client.get(
        f"/orders/details/{order.id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You can view only your own order"
    )


def test_order_details_not_found(
    client,
    create_user,
    login_token
):
    """
    Tests viewing a non-existing order.
    """

    user = create_user(
        email="missing-order@example.com",
        role="customer"
    )

    token = login_token(user.email)

    response = client.get(
        "/orders/details/99999",
        headers=auth_headers(token)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_get_own_order_history(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that a customer can view their own order history.
    """

    user = create_user(
        email="history@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    order = create_order(
        db_session=db_session,
        user_id=user.id,
        product_id=product.id
    )

    token = login_token(user.email)

    response = client.get(
        f"/orders/{user.id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == order.id
    assert data[0]["user_id"] == user.id


def test_user_cannot_view_another_users_order_history(
    client,
    create_user,
    login_token
):
    """
    Tests order-history ownership protection.
    """

    first_user = create_user(
        email="history-first@example.com",
        role="customer"
    )

    second_user = create_user(
        email="history-second@example.com",
        role="customer"
    )

    token = login_token(first_user.email)

    response = client.get(
        f"/orders/{second_user.id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "You can view only your own order history"
    )


def test_admin_can_view_all_orders(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that an admin can view all orders.
    """

    admin = create_user(
        email="orders-admin@example.com",
        role="admin"
    )

    customer = create_user(
        email="orders-customer@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    order = create_order(
        db_session=db_session,
        user_id=customer.id,
        product_id=product.id
    )

    token = login_token(admin.email)

    response = client.get(
        "/orders/operations/all",
        headers=auth_headers(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == order.id
    assert data[0]["user_id"] == customer.id


def test_support_can_view_all_orders(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that support users can view all orders.
    """

    support = create_user(
        email="support@example.com",
        role="support"
    )

    customer = create_user(
        email="support-customer@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    create_order(
        db_session=db_session,
        user_id=customer.id,
        product_id=product.id
    )

    token = login_token(support.email)

    response = client.get(
        "/orders/operations/all",
        headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_customer_cannot_view_all_orders(
    client,
    create_user,
    login_token
):
    """
    Tests that a customer cannot use the operational
    all-orders route.
    """

    customer = create_user(
        email="restricted-customer@example.com",
        role="customer"
    )

    token = login_token(customer.email)

    response = client.get(
        "/orders/operations/all",
        headers=auth_headers(token)
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Insufficient role permissions"
    )


def test_admin_can_view_operation_order_details(
    client,
    db_session,
    create_user,
    login_token
):
    """
    Tests that an admin can view operational order details.
    """

    admin = create_user(
        email="operation-admin@example.com",
        role="admin"
    )

    customer = create_user(
        email="operation-customer@example.com",
        role="customer"
    )

    category = create_category(db_session)

    product = create_product(
        db_session=db_session,
        category_id=category.id
    )

    order = create_order(
        db_session=db_session,
        user_id=customer.id,
        product_id=product.id
    )

    token = login_token(admin.email)

    response = client.get(
        f"/orders/operations/{order.id}",
        headers=auth_headers(token)
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == order.id
    assert data["user_id"] == customer.id
    assert len(data["details"]) == 1


def test_operation_order_details_not_found(
    client,
    create_user,
    login_token
):
    """
    Tests operational lookup of a non-existing order.
    """

    admin = create_user(
        email="missing-operation-admin@example.com",
        role="admin"
    )

    token = login_token(admin.email)

    response = client.get(
        "/orders/operations/99999",
        headers=auth_headers(token)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_order_route_requires_authentication(
    client
):
    """
    Tests that order routes reject requests without a JWT.
    """

    response = client.get(
        "/orders/operations/all"
    )

    assert response.status_code == 401
