import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_signup_returns_201_and_user_data(client: AsyncClient) -> None:
    payload = {
        "email": "user@example.com",
        "first_name": "string",
        "last_name": "string",
        "password": "secret123",
        "password_confirm": "secret123",
    }
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["email"] == payload["email"]
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.anyio
async def test_signup_with_missing_fields_returns_422(client: AsyncClient) -> None:
    payload = {
        # "email" is missing
        "password": "secret123",
    }
    response = await client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.anyio
async def test_login_returns_200_and_tokens(client: AsyncClient) -> None:
    # 1. Register new user
    signup_payload = {
        "email": "test@example.com",
        "first_name": "string",
        "last_name": "string",
        "password": "secret123",
        "password_confirm": "secret123",
    }
    response = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 201

    # 2. Confirm user
    confirm_payload = {"email": "test@example.com", "code": "1111"}
    response = await client.post("/api/v1/auth/verify", json=confirm_payload)
    assert response.status_code == 200

    # 3. Login with correct credentials
    login_payload = {"email": "test@example.com", "password": "secret123"}
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.anyio
async def test_refresh_returns_200_and_new_access_token(client: AsyncClient) -> None:
    # 1. Register and login user
    signup_payload = {
        "email": "refresh@example.com",
        "first_name": "string",
        "last_name": "string",
        "password": "secret123",
        "password_confirm": "secret123",
    }
    response = await client.post("/api/v1/auth/signup", json=signup_payload)
    assert response.status_code == 201

    # Confirm user
    confirm_payload = {"email": "refresh@example.com", "code": "1111"}
    response = await client.post("/api/v1/auth/verify", json=confirm_payload)
    assert response.status_code == 200

    # Login and get refresh token
    login_payload = {"email": "refresh@example.com", "password": "secret123"}
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    refresh_token = response.json()["refresh_token"]

    # 2. Call refresh with valid token
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
