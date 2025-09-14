import pytest
from httpx import AsyncClient
from app.core.security import create_access_token
from jose import jwt


class TestAuthentication:
    """Integration tests for JWT authentication and authorization."""

    @pytest.mark.integration
    async def test_protected_endpoint_without_token(self, test_client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await test_client.get("/notes/")

        assert response.status_code == 403  # FastAPI HTTPBearer returns 403

    @pytest.mark.integration
    async def test_protected_endpoint_with_invalid_token(self, test_client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await test_client.get("/notes/", headers=headers)

        assert response.status_code == 401

    @pytest.mark.integration
    async def test_protected_endpoint_with_valid_token(
        self, test_client: AsyncClient, auth_headers_agent
    ):
        """Test accessing protected endpoint with valid token."""
        response = await test_client.get("/notes/", headers=auth_headers_agent)

        assert response.status_code == 200

    @pytest.mark.integration
    async def test_token_contains_user_info(self, agent_token):
        """Test that JWT token contains correct user information."""
        # Note: In production, you'd use the actual secret key
        # For testing, we decode without verification to check structure
        decoded = jwt.decode(agent_token, key="dummy", algorithms=["HS256"], options={"verify_signature": False})

        assert "sub" in decoded  # subject (user email)
        assert "exp" in decoded  # expiration time
        assert decoded["sub"] == "agent@test.com"  # verify correct email

    @pytest.mark.integration
    async def test_role_based_access_admin_vs_agent(
        self, test_client: AsyncClient, auth_headers_agent, auth_headers_admin
    ):
        """Test different access levels between admin and agent roles."""
        # Create a note with agent
        agent_response = await test_client.post(
            "/notes/",
            json={"raw_text": "Agent's test note"},
            headers=auth_headers_agent
        )
        assert agent_response.status_code == 201
        note_id = agent_response.json()["id"]

        # Agent can access their own note
        agent_get = await test_client.get(
            f"/notes/{note_id}",
            headers=auth_headers_agent
        )
        assert agent_get.status_code == 200

        # Admin can also access the agent's note
        admin_get = await test_client.get(
            f"/notes/{note_id}",
            headers=auth_headers_admin
        )
        assert admin_get.status_code == 200