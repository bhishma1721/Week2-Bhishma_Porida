def test_root_route(client):
    """
    Tests the application's root route.
    """

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Online Shopping API is running"


def test_register_route(client):
    """
    Tests successful user registration.

    The password must not be returned in the response.
    """

    response = client.post(
        "/users/register",
        json={
            "name": "Customer One",
            "email": "customer1@example.com",
            "password": "Secret123",
            "mobile": "9876543210"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Customer One"
    assert data["email"] == "customer1@example.com"
    assert data["mobile"] == "9876543210"

    # Registration always creates a customer.
    assert data["role"] == "customer"

    # Password must not be exposed by UserResponse.
    assert "password" not in data


def test_register_duplicate_email(client):
    """
    Tests duplicate email validation.
    """

    user_data = {
        "name": "Customer One",
        "email": "duplicate@example.com",
        "password": "Secret123",
        "mobile": "9876543210"
    }

    first_response = client.post(
        "/users/register",
        json=user_data
    )

    second_response = client.post(
        "/users/register",
        json=user_data
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 404

    assert (
        second_response.json()["detail"]
        == "Email is already registered"
    )


def test_login_route(client):
    """
    Tests successful login and JWT creation.
    """

    register_response = client.post(
        "/users/register",
        json={
            "name": "Login User",
            "email": "login@example.com",
            "password": "Secret123",
            "mobile": "9876543210"
        }
    )

    assert register_response.status_code == 200

    response = client.post(
        "/auth/login",
        data={
            # Your login route uses OAuth2 form data.
            # Therefore email is sent as username.
            "username": "login@example.com",
            "password": "Secret123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_invalid_password(client):
    """
    Tests login with an incorrect password.
    """

    client.post(
        "/users/register",
        json={
            "name": "Wrong Password User",
            "email": "wrong-password@example.com",
            "password": "Secret123",
            "mobile": "9876543210"
        }
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "wrong-password@example.com",
            "password": "WrongPassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password"


def test_login_user_not_found(client):
    """
    Tests login when the email is not present in the database.
    """

    response = client.post(
        "/auth/login",
        data={
            "username": "missing@example.com",
            "password": "Secret123"
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_invalid_token_is_rejected(client):
    """
    Tests that a protected route rejects an invalid JWT.

    The cart route requires get_current_user().
    """

    response = client.get(
        "/cart/1",
        headers={
            "Authorization": "Bearer invalid.token.value"
        }
    )

    assert response.status_code == 401
