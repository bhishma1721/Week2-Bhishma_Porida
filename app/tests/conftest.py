import os

# This must be set before importing app.main.
# It prevents the application from creating tables in PostgreSQL
# while tests are running.
os.environ["TESTING"] = "1"


import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base, get_db

from app.models.user import User
from app.routers.login_router import hash_password


# This is a temporary SQLite database.
# It is separate from your PostgreSQL database.
TEST_DATABASE_URL = "sqlite://"


test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        # TestClient can access the database from another thread.
        "check_same_thread": False
    },
    # Keeps the same in-memory SQLite connection available
    # during the test.
    poolclass=StaticPool
)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


@pytest.fixture()
def db_session():
    """
    Creates a clean temporary database for every test.

    drop_all() removes the temporary test tables.
    create_all() creates them again before the next test.

    This does not drop or modify your PostgreSQL tables.
    """

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()

    try:
        # yield gives the database session to the test.
        yield db
    finally:
        # Close the session after the test completes.
        db.close()


@pytest.fixture()
def client(db_session):
    """
    Creates a FastAPI TestClient.

    The TestClient sends HTTP requests to FastAPI
    without starting Uvicorn.
    """

    def override_get_db():
        """
        Replaces the production get_db dependency.

        All routes called during testing will use the
        temporary SQLite database.
        """

        yield db_session

    # FastAPI dependency override.
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clear the override after the test finishes.
    app.dependency_overrides.clear()


@pytest.fixture()
def create_user(db_session):
    """
    Returns a helper function that creates a user
    directly in the temporary test database.
    """

    def _create_user(
        email="customer@example.com",
        role="customer",
        password="Secret123"
    ):
        user = User(
            name="Test User",
            email=email,
            password=hash_password(password),
            mobile="9876543210",
            role=role
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    return _create_user


@pytest.fixture()
def login_token(client):
    """
    Returns a helper function that logs in a user
    and returns the JWT token.
    """

    def _login_token(
        email,
        password="Secret123"
    ):
        response = client.post(
            "/auth/login",
            data={
                # OAuth2PasswordRequestForm expects the email
                # in the field called username.
                "username": email,
                "password": password
            }
        )

        assert response.status_code == 200

        return response.json()["access_token"]

    return _login_token
