import logging
import time
from rq import Worker, Queue, Connection
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import canonical components - no duplication!
from app.core.config import settings
from app.models import Note, NoteStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create synchronous database engine for RQ worker
# Convert asyncpg URL to psycopg2 URL for synchronous operations
sync_database_url = settings.database_url.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)

sync_engine = create_engine(sync_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Redis connection and queue setup
redis_conn = redis.from_url(settings.redis_url)
queue = Queue('summarization', connection=redis_conn)


def summarize_note_task(note_id: int):
    """
    Background task to summarize a note using AI-like logic.

    This task:
    1. Updates note status to 'processing'
    2. Performs AI summarization based on content keywords
    3. Updates note with summary and 'done' status
    4. Handles errors by setting status to 'failed'

    Args:
        note_id: ID of the note to summarize
    """
    logger.info(f"Starting summarization task for note {note_id}")

    db = SessionLocal()
    try:
        # Get the note
        note = db.query(Note).filter(Note.id == note_id).first()
        if not note:
            logger.error(f"Note {note_id} not found")
            return

        # Update status to processing
        note.status = NoteStatus.processing
        db.commit()

        # Simulate AI processing time
        time.sleep(5) 

        # AI-like summarization logic based on keywords
        raw_text = note.raw_text.lower()
        if "important" in raw_text or "urgent" in raw_text:
            summary = f"Priority summary: {raw_text[:100]}..."
        elif "meeting" in raw_text:
            summary = f"Meeting summary: {raw_text[:100]}..."
        else:
            summary = f"General note: {raw_text[:100]}..."

        # Update note with summary and completed status
        note.summary = summary
        note.status = NoteStatus.done
        db.commit()

        logger.info(f"Completed summarization for note {note_id}")

    except Exception as e:
        logger.error(f"Error in summarization task for note {note_id}: {str(e)}")
        try:
            # Mark note as failed
            note = db.query(Note).filter(Note.id == note_id).first()
            if note:
                note.status = NoteStatus.failed
                db.commit()
        except Exception as rollback_error:
            logger.error(f"Failed to update note status to FAILED: {rollback_error}")
    finally:
        db.close()


if __name__ == '__main__':
    """
    Run the RQ worker to process background jobs.

    This script should be run as: python -m app.notes.tasks
    to ensure proper module resolution.
    """
    logger.info("Starting RQ worker for note summarization...")
    with Connection(redis_conn):
        worker = Worker(queue)
        worker.work()