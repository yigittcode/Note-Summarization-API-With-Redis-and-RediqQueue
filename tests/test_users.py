import pytest
from httpx import AsyncClient


class TestUserEndpoints:
    """Integration tests for user authentication endpoints."""

    @pytest.mark.integration
    async def test_signup_success(self, test_client: AsyncClient):
        """Test successful user registration."""
        response = await test_client.post(
            "/users/signup",
            json={
                "email": "newuser@test.com",
                "password": "securepassword",
                "role": "AGENT"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "AGENT"
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data

    @pytest.mark.integration
    async def test_signup_duplicate_email(self, test_client: AsyncClient, test_user_agent):
        """Test signup with already existing email."""
        response = await test_client.post(
            "/users/signup",
            json={
                "email": "agent@test.com",
                "password": "password123",
                "role": "AGENT"
            }
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["message"].lower()

    @pytest.mark.integration
    async def test_signup_invalid_email(self, test_client: AsyncClient):
        """Test signup with invalid email format."""
        response = await test_client.post(
            "/users/signup",
            json={
                "email": "invalid-email",
                "password": "password123",
                "role": "AGENT"
            }
        )

        assert response.status_code == 422

    @pytest.mark.integration
    async def test_login_success(self, test_client: AsyncClient, test_user_agent):
        """Test successful user login."""
        response = await test_client.post(
            "/users/login",
            json={
                "email": "agent@test.com",
                "password": "testpassword"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    @pytest.mark.integration
    async def test_login_invalid_credentials(self, test_client: AsyncClient, test_user_agent):
        """Test login with wrong password."""
        response = await test_client.post(
            "/users/login",
            json={
                "email": "agent@test.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["message"].lower()

    @pytest.mark.integration
    async def test_login_nonexistent_user(self, test_client: AsyncClient):
        """Test login with non-existent email."""
        response = await test_client.post(
            "/users/login",
            json={
                "email": "nonexistent@test.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401