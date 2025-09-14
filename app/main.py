import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.users.router import router as users_router
from app.notes.router import router as notes_router
from app.common.exceptions import (
    UserNotFoundError,
    NoteNotFoundError,
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UnauthorizedError
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown events.

    This replaces the deprecated @app.on_event decorators with the new lifespan pattern.
    Handles application initialization and cleanup tasks.
    """
    # Startup
    logger.info("Application starting up...")
    yield
    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title="AI Summarizer API",
    description="""
    ## AI-Powered Note Summarization API

    A modern, scalable FastAPI application with:

    * **JWT Authentication**: Secure user authentication with role-based access control
    * **Async Background Processing**: Redis Queue for AI-powered note summarization
    * **Role-Based Access Control**: ADMIN and AGENT roles with appropriate permissions
    * **PostgreSQL Database**: Async database operations with SQLAlchemy 2.0+
    * **Comprehensive API**: Full CRUD operations with pagination and filtering

    ### Authentication Roles

    * **ADMIN**: Can access all notes in the system
    * **AGENT**: Can only access their own notes

    ### Background Processing

    When a note is created, it automatically queues a background summarization job.
    The AI analyzes the content and generates summaries based on keywords:

    * **Priority**: Contains "important" or "urgent"
    * **Meeting**: Contains "meeting"
    * **General**: Default summary for other content
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "Abdullah Yiğit Yıldırımoğlu",
        "email": "yigitabdullah329@gmail.com",
    },
   
)


@app.exception_handler(UserNotFoundError)
async def user_not_found_exception_handler(request: Request, exc: UserNotFoundError):
    logger.warning(f"User not found error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


@app.exception_handler(NoteNotFoundError)
async def note_not_found_exception_handler(request: Request, exc: NoteNotFoundError):
    logger.warning(f"Note not found error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


@app.exception_handler(UserAlreadyExistsError)
async def user_already_exists_exception_handler(request: Request, exc: UserAlreadyExistsError):
    logger.warning(f"User already exists error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_exception_handler(request: Request, exc: InvalidCredentialsError):
    logger.warning(f"Invalid credentials error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


@app.exception_handler(UnauthorizedError)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedError):
    logger.warning(f"Unauthorized error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error"}
    )


@app.get("/", tags=["system"])
async def root():
    """
    Root endpoint - API status.

    Returns a simple message indicating the API is operational.
    Use this endpoint to verify the API is accessible.
    """
    return {"message": "AI Summarizer API is running"}


@app.get("/health", tags=["system"])
async def health_check():
    """
    Health check endpoint.

    Returns the current health status of the API.
    This endpoint can be used by load balancers and monitoring
    systems to verify service availability.

    Returns:
        dict: Status indicating service health
    """
    return {"status": "healthy"}


app.include_router(users_router)
app.include_router(notes_router)