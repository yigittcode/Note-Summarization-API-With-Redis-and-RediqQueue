"""
Tests for the refactored error handling in job enqueueing.

These tests verify that the robust error handling implementation
properly logs errors and handles Redis failures gracefully.
"""

import pytest
from unittest.mock import patch, MagicMock
from app.notes.service import NoteService
from app.notes.schema import NoteCreate
from app.models import User, UserRole, NoteStatus
from tests.mocks import MockNoteRepository


class TestJobEnqueueingErrorHandling:
    """Tests for robust job enqueueing error handling."""

    @pytest.mark.unit
    @patch('app.notes.service.redis.from_url')
    @patch('app.notes.service.logger')
    async def test_redis_connection_failure_logged(self, mock_logger, mock_redis_from_url):
        """Test that Redis connection failures are properly logged."""
        # Arrange
        mock_repo = MockNoteRepository()
        service = NoteService(mock_repo)
        user = User(id=1, email="test@example.com", role=UserRole.AGENT)
        note_data = NoteCreate(raw_text="Test note content")

        # Mock Redis connection to raise an exception
        mock_redis_from_url.side_effect = Exception("Redis connection failed")

        # Act
        result = await service.create_note(note_data, user)

        # Assert
        # Note should still be created successfully
        assert result.raw_text == "Test note content"

        # Error should be logged with full traceback
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args
        assert "Failed to enqueue summary job for note" in error_call[0][0]
        assert "Redis connection failed" in error_call[0][0]
        assert error_call[1]["exc_info"] is True  # Full traceback included

    @pytest.mark.unit
    @patch('app.notes.service.Queue')
    @patch('app.notes.service.redis.from_url')
    @patch('app.notes.service.logger')
    async def test_queue_enqueue_failure_logged(self, mock_logger, mock_redis_from_url, mock_queue_class):
        """Test that Queue enqueue failures are properly logged."""
        # Arrange
        mock_repo = MockNoteRepository()
        service = NoteService(mock_repo)
        user = User(id=1, email="test@example.com", role=UserRole.AGENT)
        note_data = NoteCreate(raw_text="Test note content")

        # Mock successful Redis connection but failed queue enqueue
        mock_redis_conn = MagicMock()
        mock_redis_from_url.return_value = mock_redis_conn
        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue
        mock_queue.enqueue.side_effect = Exception("Queue enqueue failed")

        # Act
        result = await service.create_note(note_data, user)

        # Assert
        # Note should still be created successfully
        assert result.raw_text == "Test note content"

        # Error should be logged
        mock_logger.error.assert_called()
        error_call = mock_logger.error.call_args
        assert "Failed to enqueue summary job for note" in error_call[0][0]
        assert "Queue enqueue failed" in error_call[0][0]

    @pytest.mark.unit
    @patch('app.notes.service.redis.from_url')
    @patch('app.notes.service.logger')
    async def test_successful_enqueue_logged(self, mock_logger, mock_redis_from_url):
        """Test that successful job enqueueing is logged."""
        # Arrange
        mock_repo = MockNoteRepository()
        service = NoteService(mock_repo)
        user = User(id=1, email="test@example.com", role=UserRole.AGENT)
        note_data = NoteCreate(raw_text="Test note content")

        # Mock successful Redis and Queue operations
        mock_redis_conn = MagicMock()
        mock_redis_from_url.return_value = mock_redis_conn

        with patch('app.notes.service.Queue') as mock_queue_class:
            mock_queue = MagicMock()
            mock_queue_class.return_value = mock_queue
            mock_job = MagicMock()
            mock_job.id = "job-123"
            mock_queue.enqueue.return_value = mock_job

            # Act
            result = await service.create_note(note_data, user)

            # Assert
            # Note should be created successfully
            assert result.raw_text == "Test note content"

            # Success should be logged
            mock_logger.info.assert_called()
            info_call = mock_logger.info.call_args
            assert "Successfully enqueued summarization job job-123 for note" in info_call[0][0]

    @pytest.mark.unit
    @patch('app.notes.service.redis.from_url')
    @patch('app.notes.service.logger')
    async def test_note_status_updated_on_queue_failure(self, mock_logger, mock_redis_from_url):
        """Test that note status is updated to 'failed' when queue fails."""
        # Arrange
        mock_repo = MockNoteRepository()
        service = NoteService(mock_repo)
        user = User(id=1, email="test@example.com", role=UserRole.AGENT)
        note_data = NoteCreate(raw_text="Test note content")

        # Mock Redis connection failure
        mock_redis_from_url.side_effect = Exception("Redis connection failed")

        # Act
        result = await service.create_note(note_data, user)

        # Assert
        # Note should be created
        assert result.raw_text == "Test note content"

        # Check that the note in the mock repository has been updated to 'failed'
        note_in_repo = mock_repo.notes[result.id]
        assert note_in_repo.status == NoteStatus.failed

        # Warning should be logged about status update
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args
        assert "Updated note" in warning_call[0][0] and "status to 'failed' due to queue failure" in warning_call[0][0]