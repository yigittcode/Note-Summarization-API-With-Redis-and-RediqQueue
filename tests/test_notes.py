import pytest
from httpx import AsyncClient
from app.models import Note, NoteStatus


class TestNoteEndpoints:
    """Integration tests for note management endpoints."""

    @pytest.mark.integration
    async def test_create_note_success(
        self, test_client: AsyncClient, auth_headers_agent
    ):
        """Test successful note creation."""
        response = await test_client.post(
            "/notes/",
            json={"raw_text": "This is a test note about an important meeting."},
            headers=auth_headers_agent
        )

        assert response.status_code == 201
        data = response.json()
        assert data["raw_text"] == "This is a test note about an important meeting."
        assert data["status"] == "queued"
        assert "id" in data
        assert "created_at" in data
        assert data["summary"] is None

    @pytest.mark.integration
    async def test_create_note_unauthorized(self, test_client: AsyncClient):
        """Test note creation without authentication."""
        response = await test_client.post(
            "/notes/",
            json={"raw_text": "This should fail without auth."}
        )

        assert response.status_code == 403  # FastAPI HTTPBearer returns 403

    @pytest.mark.integration
    async def test_get_note_by_id_success(
        self, test_client: AsyncClient, auth_headers_agent, test_db_session
    ):
        """Test retrieving a note by ID."""
        # First create a note
        create_response = await test_client.post(
            "/notes/",
            json={"raw_text": "Test note for retrieval"},
            headers=auth_headers_agent
        )
        note_id = create_response.json()["id"]

        # Then retrieve it
        response = await test_client.get(
            f"/notes/{note_id}",
            headers=auth_headers_agent
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == note_id
        assert data["raw_text"] == "Test note for retrieval"

    @pytest.mark.integration
    async def test_get_note_not_found(
        self, test_client: AsyncClient, auth_headers_agent
    ):
        """Test retrieving non-existent note."""
        response = await test_client.get(
            "/notes/99999",
            headers=auth_headers_agent
        )

        assert response.status_code == 404

    @pytest.mark.integration
    async def test_get_notes_paginated(
        self, test_client: AsyncClient, auth_headers_agent
    ):
        """Test retrieving notes with pagination."""
        # Create multiple notes
        for i in range(5):
            await test_client.post(
                "/notes/",
                json={"raw_text": f"Test note {i}"},
                headers=auth_headers_agent
            )

        response = await test_client.get(
            "/notes/?page=1&size=3",
            headers=auth_headers_agent
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        assert len(data["items"]) <= 3
        assert data["page"] == 1
        assert data["size"] == 3

    @pytest.mark.integration
    async def test_get_notes_with_search(
        self, test_client: AsyncClient, auth_headers_agent
    ):
        """Test retrieving notes with search filter."""
        # Create notes with different content
        await test_client.post(
            "/notes/",
            json={"raw_text": "Meeting notes from today"},
            headers=auth_headers_agent
        )
        await test_client.post(
            "/notes/",
            json={"raw_text": "Random thoughts and ideas"},
            headers=auth_headers_agent
        )

        response = await test_client.get(
            "/notes/?search=meeting",
            headers=auth_headers_agent
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        # Check that search results contain the term
        found_meeting = any("meeting" in item["raw_text"].lower() for item in data["items"])
        assert found_meeting

    @pytest.mark.integration
    async def test_agent_cannot_see_other_notes(
        self, test_client: AsyncClient, auth_headers_agent, auth_headers_admin,
        test_user_agent, test_user_admin
    ):
        """Test that agent users can only see their own notes."""
        # Admin creates a note
        admin_response = await test_client.post(
            "/notes/",
            json={"raw_text": "Admin's private note"},
            headers=auth_headers_admin
        )
        admin_note_id = admin_response.json()["id"]

        # Agent tries to access admin's note
        response = await test_client.get(
            f"/notes/{admin_note_id}",
            headers=auth_headers_agent
        )

        assert response.status_code == 404

    @pytest.mark.integration
    async def test_admin_can_see_all_notes(
        self, test_client: AsyncClient, auth_headers_agent, auth_headers_admin
    ):
        """Test that admin users can see all notes."""
        # Agent creates a note
        agent_response = await test_client.post(
            "/notes/",
            json={"raw_text": "Agent's note"},
            headers=auth_headers_agent
        )
        agent_note_id = agent_response.json()["id"]

        # Admin should be able to access agent's note
        response = await test_client.get(
            f"/notes/{agent_note_id}",
            headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["raw_text"] == "Agent's note"

    @pytest.mark.integration
    async def test_notes_list_role_based_access(
        self, test_client: AsyncClient, auth_headers_agent, auth_headers_admin
    ):
        """Test role-based access control in notes listing."""
        # Agent creates notes
        for i in range(2):
            await test_client.post(
                "/notes/",
                json={"raw_text": f"Agent note {i}"},
                headers=auth_headers_agent
            )

        # Admin creates notes
        for i in range(2):
            await test_client.post(
                "/notes/",
                json={"raw_text": f"Admin note {i}"},
                headers=auth_headers_admin
            )

        # Agent should only see their notes
        agent_response = await test_client.get(
            "/notes/",
            headers=auth_headers_agent
        )
        agent_data = agent_response.json()

        # Admin should see all notes
        admin_response = await test_client.get(
            "/notes/",
            headers=auth_headers_admin
        )
        admin_data = admin_response.json()

        assert agent_response.status_code == 200
        assert admin_response.status_code == 200
        assert agent_data["total"] == 2  # Only agent's notes
        assert admin_data["total"] == 4  # All notes