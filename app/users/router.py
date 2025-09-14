from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_user_service
from app.users.service import UserService
from app.users.schema import UserCreate, UserLogin, UserResponse, Token

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        400: {"description": "Bad request - malformed request or invalid data"},
        401: {"description": "Authentication failed - invalid credentials"},
        409: {"description": "Conflict - user already exists"},
        422: {"description": "Validation error - request data doesn't meet requirements"},
    }
)


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(
    user_create: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user account.

    Register a new user with email and password. Users can be assigned
    one of two roles:

    - **AGENT**: Default role, can only access their own notes
    - **ADMIN**: Administrative role, can access all notes in the system

    ## Request Body
    - **email**: Valid email address (must be unique)
    - **password**: User password (minimum security requirements apply)
    - **role**: User role (AGENT or ADMIN, defaults to AGENT)

    ## Response
    Returns the created user information (excluding password) with:
    - User ID, email, role, and creation timestamp

    ## Errors
    - **409**: Email already exists (conflict)
    - **422**: Validation failed (invalid email format, weak password, etc.)
    """
    return await user_service.create_user(user_create)


@router.post("/login", response_model=Token)
async def login(
    user_login: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """
    Authenticate user and get access token.

    Login with email and password to receive a JWT access token
    for authenticating subsequent API requests.

    ## Request Body
    - **email**: Registered email address
    - **password**: User password

    ## Response
    Returns authentication token with:
    - **access_token**: JWT token for API authentication
    - **token_type**: Always "bearer"

    ## Usage
    Include the token in subsequent requests:
    ```
    Authorization: Bearer <access_token>
    ```

    ## Token Expiration
    Tokens expire after 30 minutes by default. You'll need to login
    again when the token expires.

    ## Errors
    - **401**: Invalid email or password
    """
    return await user_service.authenticate_user(user_login)