import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_get_me_returns_200_and_user_data(client: AsyncClient, fake_jwt_token: str) -> None:
    headers = {"Authorization": f"Bearer {fake_jwt_token}"}

    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data


@pytest.mark.anyio
async def test_list_users_without_admin_returns_403(client: AsyncClient, fake_jwt_token: str) -> None:
    headers = {"Authorization": f"Bearer {fake_jwt_token}"}

    response = await client.get("/api/v1/users/?limit=2&offset=0", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


@pytest.mark.anyio
async def test_get_user_by_id_without_admin_returns_403(client: AsyncClient, fake_jwt_token: str) -> None:
    headers = {"Authorization": f"Bearer {fake_jwt_token}"}

    response = await client.get("/api/v1/users/1", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


@pytest.mark.anyio
async def test_update_user_returns_200(client: AsyncClient, fake_jwt_token: str) -> None:
    headers = {"Authorization": f"Bearer {fake_jwt_token}"}

    payload = {"first_name": "Updated", "last_name": "User"}
    response = await client.patch("/api/v1/users/", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == payload["first_name"]
    assert data["last_name"] == payload["last_name"]


@pytest.mark.anyio
async def test_delete_user_without_admin_returns_403(client: AsyncClient, fake_jwt_token: str) -> None:
    headers = {"Authorization": f"Bearer {fake_jwt_token}"}

    response = await client.delete("/api/v1/users/1", headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
