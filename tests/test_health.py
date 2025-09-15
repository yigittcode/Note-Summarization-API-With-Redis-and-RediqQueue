import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Integration tests for system health endpoints."""

    @pytest.mark.integration
    async def test_root_endpoint(self, test_client: AsyncClient):
        """Test root endpoint returns API status."""
        response = await test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "AI Summarizer API" in data["message"]

    @pytest.mark.integration
    async def test_health_check_endpoint(self, test_client: AsyncClient):
        """Test health check endpoint."""
        response = await test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"