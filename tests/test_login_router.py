# from types import SimpleNamespace
# from unittest.mock import MagicMock, patch

# import pytest
# from fastapi import HTTPException

# from app.routers.login_router import (
#     generate_token,
#     get_current_user,
#     hash_password,
#     login,
#     require_roles,
#     verify_password,
# )


# def create_mock_db(result):
#     """
#     Creates a fake database session.

#     The route expects this chain:

#     db.query(...).filter(...).first()
#     """

#     db = MagicMock()

#     (
#         db.query.return_value
#         .filter.return_value
#         .first.return_value
#     ) = result

#     return db


# def test_password_hash_and_verify():
#     """
#     Passwords must be stored as hashes and verified correctly.
#     """

#     plain_password = "Secret123"

#     hashed_password = hash_password(plain_password)

#     assert hashed_password != plain_password
#     assert verify_password(plain_password, hashed_password) is True
#     assert verify_password("WrongPassword", hashed_password) is False


# def test_login_success():
#     """
#     Valid credentials should return a JWT bearer token.
#     """

#     fake_user = SimpleNamespace(
#         email="customer@example.com",
#         password="stored-hashed-password"
#     )

#     db = create_mock_db(fake_user)

#     request = SimpleNamespace(
#         username="customer@example.com",
#         password="Secret123"
#     )

#     # We mock password verification because this test focuses on
#     # login route behavior, not bcrypt implementation.
#     with patch(
#         "app.routers.login_router.verify_password",
#         return_value=True
#     ):
#         response = login(request, db)

#     assert response["token_type"] == "bearer"
#     assert response["access_token"] is not None
#     assert isinstance(response["access_token"], str)


# def test_login_user_not_found():
#     """
#     Login should return 404 when the email does not exist.
#     """

#     db = create_mock_db(None)

#     request = SimpleNamespace(
#         username="missing@example.com",
#         password="Secret123"
#     )

#     with pytest.raises(HTTPException) as exception:
#         login(request, db)

#     assert exception.value.status_code == 404
#     assert exception.value.detail == "User not found"


# def test_login_invalid_password():
#     """
#     Login should return 401 when the password is incorrect.
#     """

#     fake_user = SimpleNamespace(
#         email="customer@example.com",
#         password="stored-hashed-password"
#     )

#     db = create_mock_db(fake_user)

#     request = SimpleNamespace(
#         username="customer@example.com",
#         password="WrongPassword"
#     )

#     with patch(
#         "app.routers.login_router.verify_password",
#         return_value=False
#     ):
#         with pytest.raises(HTTPException) as exception:
#             login(request, db)

#     assert exception.value.status_code == 401
#     assert exception.value.detail == "Invalid password"


# def test_get_current_user_with_valid_token():
#     """
#     A valid JWT should return the corresponding database user.
#     """

#     email = "customer@example.com"

#     fake_user = SimpleNamespace(
#         id=1,
#         email=email,
#         role="customer"
#     )

#     db = create_mock_db(fake_user)

#     token = generate_token({"sub": email})

#     result = get_current_user(token, db)

#     assert result is fake_user
#     assert result.email == email


# def test_get_current_user_with_invalid_token():
#     """
#     A malformed or invalid JWT should return 401.
#     """

#     db = create_mock_db(None)

#     with pytest.raises(HTTPException) as exception:
#         get_current_user("invalid.token.value", db)

#     assert exception.value.status_code == 401
#     assert exception.value.detail == "Invalid authentication credentials"


# def test_get_current_user_when_user_does_not_exist():
#     """
#     A valid token for a deleted/non-existing user should return 401.
#     """

#     email = "deleted@example.com"

#     db = create_mock_db(None)

#     token = generate_token({"sub": email})

#     with pytest.raises(HTTPException) as exception:
#         get_current_user(token, db)

#     assert exception.value.status_code == 401


# def test_admin_role_is_allowed():
#     """
#     An admin should pass an admin-only authorization check.
#     """

#     admin_user = SimpleNamespace(
#         id=1,
#         role="admin"
#     )

#     admin_check = require_roles("admin")

#     result = admin_check(admin_user)

#     assert result is admin_user


# def test_customer_is_rejected_from_admin_route():
#     """
#     A customer should be rejected from an admin-only authorization check.
#     """

#     customer_user = SimpleNamespace(
#         id=2,
#         role="customer"
#     )

#     admin_check = require_roles("admin")

#     with pytest.raises(HTTPException) as exception:
#         admin_check(customer_user)

#     assert exception.value.status_code == 403
#     assert exception.value.detail == "Insufficient role permissions"


# def test_support_role_is_allowed_for_operations():
#     """
#     Support users should pass admin/support operation authorization.
#     """

#     support_user = SimpleNamespace(
#         id=3,
#         role="support"
#     )

#     operations_check = require_roles("admin", "support")

#     result = operations_check(support_user)

#     assert result is support_user
