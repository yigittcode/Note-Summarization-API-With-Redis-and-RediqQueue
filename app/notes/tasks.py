import logging
import time
from rq import Worker, Queue, Connection
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch

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

# Initialize T5 model components
tokenizer, model, device = None, None, None

def initialize_t5_model():
    """
    Initialize T5-small model and tokenizer.
    This function loads the model only when needed to avoid memory issues.
    """
    global tokenizer, model, device
    
    if model is not None and tokenizer is not None:
        return  # Already initialized
    
    try:
        logger.info("Loading T5-small model...")
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"Using device: {device}")
        
        # Load tokenizer and model
        tokenizer = T5Tokenizer.from_pretrained('t5-small')
        model = T5ForConditionalGeneration.from_pretrained('t5-small')
        model.to(device)
        model.eval()
        
        logger.info("T5-small model loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load T5-small model: {e}")
        logger.warning("Falling back to rule-based summarization")
        tokenizer, model, device = None, None, None


def generate_t5_summary(text: str, max_length: int = 150) -> str:
    """
    Generate summary using T5-small model.

    Args:
        text: Input text to summarize
        max_length: Maximum length of summary

    Returns:
        Generated summary text
    """
    global model, tokenizer, device

    # Initialize model if not already done
    if not model or not tokenizer:
        logger.info("T5 model not initialized, attempting to load...")
        initialize_t5_model()
        
        if not model or not tokenizer:
            logger.warning("T5 model not available, falling back to simple truncation")
            return f"Summary: {text[:100]}..." if len(text) > 100 else text

    try:
        logger.info(f"Generating summary for text: {text[:50]}...")

        # Prepare input for T5 (T5 requires task prefix)
        input_text = f"summarize: {text}"

        # Tokenize input
        inputs = tokenizer.encode(
            input_text,
            return_tensors='pt',
            max_length=512,
            truncation=True
        ).to(device)

        # Generate summary
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=max_length,
                min_length=30,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True,
                do_sample=False
            )

        # Decode the summary
        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Generated summary: {summary}")
        return summary

    except Exception as e:
        logger.error(f"Error generating T5 summary: {e}")
        return f"Summary: {text[:100]}..." if len(text) > 100 else text


def summarize_note_task(note_id: int):
    """
    Background task to summarize a note using T5-small model.

    This task:
    1. Updates note status to 'processing'
    2. Performs AI summarization using T5-small model
    3. Updates note with summary and 'done' status
    4. Handles errors by setting status to 'failed'

    Args:
        note_id: ID of the note to summarize
    """
    logger.info(f"Starting T5 summarization task for note {note_id}")

    db = SessionLocal()
    try:
        # Get the note
        note = db.query(Note).filter(Note.id == note_id).first()
        if not note:
            logger.error(f"Note {note_id} not found")
            return

        logger.info(f"Found note {note_id}, updating status to processing...")

        # Update status to processing
        note.status = NoteStatus.processing
        db.commit()

        logger.info(f"Processing note {note_id} - generating summary...")

        # Generate summary using T5-small model (will auto-initialize if needed)
        summary = generate_t5_summary(note.raw_text)

        logger.info(f"Summary generated: {summary[:50]}...")

        # Update note with AI-generated summary and completed status
        note.summary = summary
        note.status = NoteStatus.done
        db.commit()

        logger.info(f"Completed T5 summarization for note {note_id}")

    except Exception as e:
        logger.error(f"Error in T5 summarization task for note {note_id}: {str(e)}", exc_info=True)
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